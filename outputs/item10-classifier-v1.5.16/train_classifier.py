"""Reproducible exploratory baselines. Develop first; open synthetic test only after selection is frozen."""
from __future__ import annotations
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(key,'1')
import argparse,collections,csv,hashlib,json,platform,subprocess,sys,time,warnings
from pathlib import Path
import numpy as np
import sklearn,scipy,joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,f1_score,log_loss
from classifier_runtime import predict_records,route,route_prediction,normalize,strip_training_wrappers,ComponentSignalClassifier

ROOT=Path(__file__).resolve().parents[3]
SEED=20261017
PRIMARY=['labor','consumer','mixed','out_of_scope'];SCOPE=['fully_supported','partially_supported','unsupported']
CONFIGS=[{'name':'dummy_prior','kind':'dummy','features':'none','C':None},
 {'name':'logistic_word_C1','kind':'logistic','features':'word','C':1.0},
 {'name':'logistic_wordchar_C1','kind':'logistic','features':'wordchar','C':1.0},
 {'name':'logistic_wordchar_C4','kind':'logistic','features':'wordchar','C':4.0},
 {'name':'svm_wordchar_C1','kind':'svm','features':'wordchar','C':1.0},
 {'name':'svm_wordchar_C4','kind':'svm','features':'wordchar','C':4.0}]

def readrows(path):return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def jsonl(path,rows):path.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows),encoding='utf-8')
def norm(text):return ' '.join(''.join(c.lower() if c.isalnum() else ' ' for c in text).split())

def sources():
    seed_dir=ROOT/'dataset/processed/item10/reviewed_v1.0.0';dev_dir=ROOT/'dataset/processed/item10/ai_reviewed_eval_v1.0.0'
    for d in (seed_dir,dev_dir):
        m=json.loads((d/'dataset_manifest.json').read_text())
        for name,h in m['files_sha256'].items():
            if sha(d/name)!=h:raise ValueError('Frozen/source checksum mismatch: '+str(d/name))
    seed=readrows(seed_dir/'classifier_questions.jsonl')
    general=readrows(dev_dir/'evaluation_questions.jsonl');typing=readrows(dev_dir/'typing_questions.jsonl')
    partitions={s:[r for r in seed if r['split']==s] for s in ('train','validation','test')}
    assert {s:len(v) for s,v in partitions.items()}=={'train':459,'validation':102,'test':100}
    group_splits=collections.defaultdict(set)
    for r in seed:group_splits[r['leakage_group_id']].add(r['split'])
    assert all(len(v)==1 for v in group_splits.values())
    assert not {norm(r['question_text']) for r in partitions['train']}&{norm(r['question_text']) for r in partitions['validation']+partitions['test']+general+typing}
    assert len({r['question_id'] for r in seed+general+typing})==861
    assert all(r['human_reviewer'] and r['annotation_status']=='human_reviewed_owner_authorized_cleanup' for r in seed)
    assert all(r['origin']=='ai_authored' and r['review_status']=='ai_approved' and not r['locked'] for r in general+typing)
    audit={'status':'passed','train':459,'validation':102,'synthetic_test':100,'ai_development':200,
        'frozen_and_ai_source_file_hashes_passed':True,'leakage_groups_crossing_partitions':0,'train_exact_matches_to_heldout':0,
        'features':'question_text only','semantic_independence_asserted':False,
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [seed_dir/'classifier_questions.jsonl',dev_dir/'evaluation_questions.jsonl',dev_dir/'typing_questions.jsonl']}}
    return partitions,general,typing,audit

def build(config,folds):
    if config['kind']=='dummy':return DummyClassifier(strategy='prior',random_state=SEED)
    preprocessor=strip_training_wrappers if config.get('strip_wrappers') else None
    word=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,strip_accents='unicode',min_df=1,max_features=15000,preprocessor=preprocessor)
    features=word if config['features']=='word' else FeatureUnion([('word',word),('character',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True,strip_accents='unicode',min_df=1,max_features=30000,preprocessor=preprocessor))])
    clf=LogisticRegression(C=config['C'],class_weight='balanced',max_iter=2500,solver='lbfgs',random_state=SEED) if config['kind']=='logistic' else LinearSVC(C=config['C'],class_weight='balanced',random_state=SEED,max_iter=5000)
    pipe=Pipeline([('features',features),('classifier',clf)])
    return CalibratedClassifierCV(estimator=pipe,method='sigmoid',cv=folds,ensemble=False,n_jobs=1)

def wilson(success,n):
    if n==0:return None
    z=1.959963984540054;p=success/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return {'lower':float(max(0,c-h)),'upper':float(min(1,c+h)),'method':'Wilson 95% interval','numerator':int(success),'denominator':int(n)}

def bootstrap_group(rows,predictions,key,labels,repeats=2000):
    groups=collections.defaultdict(list)
    for i,r in enumerate(rows):groups[r.get('leakage_group_id',r.get('scenario_family_id',r['question_id']))].append(i)
    matrices=[];mapping={l:i for i,l in enumerate(labels)}
    for indices in groups.values():
        m=np.zeros((len(labels),len(labels)),dtype=int)
        for i in indices:m[mapping[rows[i][key]],mapping[predictions[i]['predicted_'+('primary' if key=='primary_label' else 'scope')]]]+=1
        matrices.append(m)
    matrices=np.array(matrices);rng=np.random.default_rng(SEED);scores=[]
    for _ in range(repeats):
        m=matrices[rng.integers(0,len(matrices),len(matrices))].sum(axis=0);tp=m.diagonal();den=m.sum(axis=0)+m.sum(axis=1)
        scores.append(float(np.divide(2*tp,den,out=np.zeros(len(labels),dtype=float),where=den>0).mean()))
    return {'lower':float(np.quantile(scores,.025)),'upper':float(np.quantile(scores,.975)),'method':'95% percentile bootstrap of scenario/leakage groups','groups':len(groups),'replicates':repeats}

def head_metrics(rows,predictions,head,bootstrap=False):
    key=head+'_label';labels=PRIMARY if head=='primary' else SCOPE
    y=[r[key] for r in rows];pred=[r['predicted_'+head] for r in predictions]
    probs=np.array([[r[head+'_probabilities'][c] for c in labels] for r in predictions])
    assert np.isfinite(probs).all() and np.allclose(probs.sum(axis=1),1,atol=1e-10)
    # sklearn log_loss expects alphabetically sorted columns, not our presentation label order.
    alphabetical=sorted(labels);ordered=np.array([[r[head+'_probabilities'][c] for c in alphabetical] for r in predictions])
    true=np.array([[int(a==b) for b in labels] for a in y]);confidence=np.array([probs[i,labels.index(label)] for i,label in enumerate(pred)]);correct=np.array(y)==np.array(pred)
    bins=[];ece=0.0
    for low,high in zip(np.arange(0,1,.1),np.arange(.1,1.01,.1)):
        mask=(confidence>=low)&(confidence<high if high<.999 else confidence<=high+1e-10);n=int(mask.sum())
        if n:
            acc=float(correct[mask].mean());conf=float(confidence[mask].mean());ece+=n/len(rows)*abs(acc-conf)
            bins.append({'lower':float(low),'upper':float(high),'count':n,'accuracy':acc,'mean_confidence':conf})
    result={'rows':len(rows),'accuracy':float(accuracy_score(y,pred)),'macro_f1':float(f1_score(y,pred,labels=labels,average='macro',zero_division=0)),
        'micro_f1':float(f1_score(y,pred,labels=labels,average='micro',zero_division=0)),
        'classification_report':classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist(),'label_order':labels,
        'mean_confidence':float(confidence.mean()),'mean_confidence_when_wrong':float(confidence[~correct].mean()) if (~correct).any() else None,
        'log_loss':float(log_loss(y,ordered,labels=alphabetical)),'multiclass_brier_sum_squared':float(np.mean(np.sum((probs-true)**2,axis=1))),
        'top_label_expected_calibration_error_10_bins':float(ece),'reliability_bins':bins,'accuracy_wilson_95':wilson(int(correct.sum()),len(rows))}
    if bootstrap:result['macro_f1_group_bootstrap_95']=bootstrap_group(rows,predictions,key,labels)
    return result

def routing_metrics(rows,predictions):
    classified=[(r,p) for r,p in zip(rows,predictions) if r.get('primary_label') is not None]
    unsupported=[(r,p) for r,p in classified if r['scope_label']=='unsupported']
    admitted=sum(p['substantive_answer_admitted'] for r,p in unsupported)
    decisive=sum(p['routing_action']!='clarify' for r,p in classified)
    clarification=[(r,p) for r,p in zip(rows,predictions) if r.get('expected_action')=='clarify']
    # Exact relevance categories are the authored deciding facts, not labels shown to the router.
    expected_reason={'TYPE_G17':'employment_category_missing','TYPE_G18':'refund_transaction_missing','TYPE_G19':'contract_relationship_missing','TYPE_G20':'charge_context_missing'}
    successes=sum(p['routing_action']=='clarify' and p['reason']==expected_reason.get(r.get('scenario_family_id')) for r,p in clarification)
    known_correct=sum(r['primary_label']==p['predicted_primary'] and r['scope_label']==p['predicted_scope'] for r,p in classified if p['routing_action']!='clarify')
    groups=collections.defaultdict(list)
    for r,p in clarification:groups[r['scenario_family_id']].append(p['routing_action']=='clarify' and p['reason']==expected_reason.get(r['scenario_family_id']))
    return {'classifiable_rows':len(classified),'decisive_count':decisive,'decisive_coverage':decisive/len(classified) if classified else None,
        'correct_joint_labels_among_decisive':known_correct/decisive if decisive else None,
        'unsupported_count':len(unsupported),'unsupported_answer_admitted_count':admitted,'unsupported_admission_rate':admitted/len(unsupported) if unsupported else None,
        'unsupported_admission_wilson_95':wilson(admitted,len(unsupported)),
        'clarification_rows':len(clarification),'relevant_clarification_count':successes,'relevant_clarification_rate':successes/len(clarification) if clarification else None,
        'clarification_all_variants_correct_families':sum(all(v) for v in groups.values()),'clarification_families':len(groups),
        'routing_counts':dict(collections.Counter(p['routing_action'] for p in predictions)),'reason_counts':dict(collections.Counter(p['reason'] for p in predictions)),
        'clarification_relevance_evaluator':'deterministic missing-fact category checks against authored benchmark; not independent human evaluation'}

def evaluate(rows,predictions,bootstrap=False):
    classified=[(r,p) for r,p in zip(rows,predictions) if r.get('primary_label') is not None];rs=[r for r,p in classified];ps=[p for r,p in classified]
    result={'primary':head_metrics(rs,ps,'primary',bootstrap),'scope':head_metrics(rs,ps,'scope',bootstrap),'routing':routing_metrics(rows,predictions),'language':{},'variation':{}}
    for field,out in [('language_style','language'),('variation_type','variation')]:
        for v in sorted({r[field] for r in rs if field in r}):
            pairs=[(r,p) for r,p in classified if r.get(field)==v];a=[r for r,p in pairs];b=[p for r,p in pairs]
            # Scope F1 includes only classes represented in a small stratum; primary uses all four labels.
            result[out][v]={'count':len(a),'primary_accuracy':float(accuracy_score([r['primary_label'] for r in a],[p['predicted_primary'] for p in b])),
                'primary_macro_f1':float(f1_score([r['primary_label'] for r in a],[p['predicted_primary'] for p in b],labels=PRIMARY,average='macro',zero_division=0)),
                'scope_accuracy':float(accuracy_score([r['scope_label'] for r in a],[p['predicted_scope'] for p in b]))}
    return result

def gates(metrics,policy,include_clarification=False):
    t=policy['targets'];p=metrics['primary'];s=metrics['scope'];r=metrics['routing'];pr=p['classification_report'];sr=s['classification_report']
    checks=[('primary_macro_f1',p['macro_f1'],t['primary_macro_f1_min'],'min'),('scope_macro_f1',s['macro_f1'],t['scope_macro_f1_min'],'min'),
        ('out_of_scope_recall',pr['out_of_scope']['recall'],t['out_of_scope_recall_min'],'min'),('mixed_recall',pr['mixed']['recall'],t['mixed_recall_min'],'min'),
        ('partially_supported_recall',sr['partially_supported']['recall'],t['partially_supported_scope_recall_min'],'min'),
        ('minimum_primary_class_recall',min(pr[c]['recall'] for c in PRIMARY),t['each_primary_class_recall_min'],'min'),
        ('unsupported_admission_rate',r['unsupported_admission_rate'],t['unsupported_substantive_answer_routing_admission_max'],'max'),
        ('decisive_coverage',r['decisive_coverage'],t['decisive_routing_coverage_classifiable_min'],'min')]
    if include_clarification:checks.append(('relevant_clarification_count',r['relevant_clarification_count'],t['clarification_success_current_benchmark_min_count'],'min'))
    return [{'name':name,'observed':v,'target':target,'direction':direction,'passed':v is not None and (v>=target if direction=='min' else v<=target)} for name,v,target,direction in checks]

def select_thresholds(rows,base_predictions,policy):
    options=[];grid=[0.0,.3,.4,.5,.6,.7,.8,.85,.9,.95,.97,.98,.99,.995,.999,1.01]
    for a in grid:
        for b in grid:
            preds=[]
            for p in base_predictions:
                v=dict(p);v.update(route_prediction(p,{'primary':a,'scope':b}));preds.append(v)
            m=routing_metrics(rows,preds);safe=m['unsupported_admission_rate']<=policy['targets']['unsupported_substantive_answer_routing_admission_max'];enough=m['decisive_coverage']>=policy['targets']['decisive_routing_coverage_classifiable_min']
            options.append({'primary':a,'scope':b,'safety_target_met':safe,'coverage_target_met':enough,**m})
    def rank(r):return (r['safety_target_met'] and r['coverage_target_met'],r['safety_target_met'],r['decisive_coverage'] if not r['coverage_target_met'] else r['correct_joint_labels_among_decisive'] or 0,r['decisive_coverage'],r['primary']+r['scope'])
    chosen=max(options,key=rank)
    return {'primary':chosen['primary'],'scope':chosen['scope']},options,chosen

def train(run,experiment='baseline'):
    if run.exists():raise ValueError('Use a new run directory; never overwrite results or an opened test.')
    policy=json.loads((ROOT/'dataset/pipelines/item10/evaluation_policy.json').read_text())
    assert policy['owner_confirmed'] and policy['exploratory_training_authorized'] and not policy['deployment_authorized']
    partitions,general,typing,audit=sources();run.mkdir(parents=True)
    configs=[dict(c,strip_wrappers=experiment in ('strip_wrappers','compositional'),composition=experiment=='compositional') for c in CONFIGS]
    audit['experiment']=experiment
    if experiment=='strip_wrappers':audit['correction']='Remove class-correlated generator wrappers using generator/training-only patterns; no new scenarios or held-out examples are fitted.'
    if experiment=='compositional':audit['correction']='Training-only supported-labor, supported-consumer and excluded-content binary targets derived from training annotations; remove generator wrappers and compose primary/scope probabilities. Products approximate independent detector outputs; empirical calibration is reported, not guaranteed.'
    save(run/'data_audit.json',audit);save(run/'policy_snapshot.json',policy);save(run/'candidate_configs.json',configs)
    trainrows=partitions['train'];val=partitions['validation'];texts=[r['question_text'] for r in trainrows]
    groups=np.array([r['leakage_group_id'] for r in trainrows]);joint=np.array([r['primary_label']+'|'+r['scope_label'] for r in trainrows])
    folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=SEED).split(texts,joint,groups))
    held=[]
    fold_report=[]
    for i,(a,b) in enumerate(folds):
        assert not set(groups[a])&set(groups[b]);held.extend(b.tolist())
        for key in ('primary_label','scope_label'):assert set(trainrows[j][key] for j in a)==set(trainrows[j][key] for j in b)==set(r[key] for r in trainrows)
        fold_report.append({'fold':i,'fit_rows':len(a),'calibration_rows':len(b),'fit_group_ids':sorted(set(groups[a])),'calibration_group_ids':sorted(set(groups[b]))})
    assert sorted(held)==list(range(459));save(run/'calibration_folds.json',fold_report)
    summaries=[];models={};started=time.time()
    for config in configs:
        print('Training '+config['name'],flush=True);heads={};captured=[]
        fit_targets=['supported_labor','supported_consumer','excluded'] if experiment=='compositional' else ['primary','scope']
        components={}
        for head in fit_targets:
            model=build(config,folds)
            if head=='supported_labor':y=['present' if any(t.startswith('labor.') for t in r['supported_topic_ids']) else 'absent' for r in trainrows]
            elif head=='supported_consumer':y=['present' if any(t.startswith('consumer.') for t in r['supported_topic_ids']) else 'absent' for r in trainrows]
            elif head=='excluded':y=['present' if r['excluded_topic_ids'] else 'absent' for r in trainrows]
            else:y=[r[head+'_label'] for r in trainrows]
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always');model.fit(texts,y);captured.extend(str(v.message) for v in w)
            if experiment=='compositional':components[head]=model
            else:heads[head+'_model']=model
        if experiment=='compositional':heads={'primary_model':ComponentSignalClassifier('primary',components),'scope_model':ComponentSignalClassifier('scope',components)}
        bundle={'model_version':run.name,'config':config,'thresholds':{'primary':0.,'scope':0.},**heads}
        base=predict_records(bundle,val);thresholds,search,chosen=select_thresholds(val,base,policy);bundle['thresholds']=thresholds
        preds=predict_records(bundle,val);metrics=evaluate(val,preds);checks=gates(metrics,policy)
        summary={'name':config['name'],'config':config,'validation':metrics,'gates':checks,'all_validation_targets_met':all(c['passed'] for c in checks),'thresholds':thresholds,'warnings':captured}
        summaries.append(summary);models[config['name']]=bundle
        save(run/(config['name']+'_validation.json'),summary);save(run/(config['name']+'_threshold_search.json'),search)
        print(json.dumps({'candidate':config['name'],'primary_f1':metrics['primary']['macro_f1'],'scope_f1':metrics['scope']['macro_f1'],'coverage':metrics['routing']['decisive_coverage'],'unsafe_admission':metrics['routing']['unsupported_admission_rate'],'thresholds':thresholds}),flush=True)
    learned=[s for s in summaries if s['config']['kind']!='dummy']
    def candidate_rank(s):
        m=s['validation'];return (s['all_validation_targets_met'],sum(g['passed'] for g in s['gates']),min(m['primary']['macro_f1'],m['scope']['macro_f1']),(m['primary']['macro_f1']+m['scope']['macro_f1'])/2,-m['primary']['log_loss']-m['scope']['log_loss'])
    selected=max(learned,key=candidate_rank);bundle=models[selected['name']]
    bundle.update(seed=SEED,policy_version=policy['policy_version'],train_question_ids=[r['question_id'] for r in trainrows],train_group_ids=sorted(set(groups)),deployment_allowed=False)
    joblib.dump(bundle,run/'classifier.joblib',compress=3)
    # Selection is fixed using validation only; development benchmark results are never a hidden selection criterion.
    selection={'selected_candidate':selected['name'],'selection_data':'102 seed validation rows only','selection_rule':'validation target attainment, then minimum primary/scope macro F1, average macro F1, log loss','thresholds':bundle['thresholds'],'model_sha256':sha(run/'classifier.joblib'),'test_opened':False,'development_benchmarks_used_for_selection':False,'selected_before_development_scoring':True}
    save(run/'selection_frozen.json',selection);save(run/'candidate_comparison.json',summaries)
    reports={}
    for name,rows in [('validation',val),('ai_general_development',general),('ai_typing_development',typing)]:
        preds=predict_records(bundle,rows)
        for r,p in zip(rows,preds):p.update(expected_primary=r.get('primary_label'),expected_scope=r.get('scope_label'),expected_action=r.get('expected_action','classify'),language_style=r['language_style'],scenario_family_id=r.get('scenario_family_id',r.get('leakage_group_id')),variation_type=r.get('variation_type'))
        jsonl(run/(name+'_predictions.jsonl'),preds);metrics=evaluate(rows,preds,bootstrap=True);metrics['targets']=gates(metrics,policy,include_clarification=name=='ai_typing_development');metrics['all_applicable_targets_met']=all(c['passed'] for c in metrics['targets']);reports[name]=metrics;save(run/(name+'_metrics.json'),metrics)
    manifest={'status':'exploratory_development_complete','as_of':'2026-10-17','model_version':run.name,'selected_candidate':selected['name'],'seed':SEED,
        'training_rows':459,'validation_rows':102,'development_benchmark_rows':200,'synthetic_test_opened':False,'source_hashes':audit['source_sha256'],
        'model_sha256':sha(run/'classifier.joblib'),'policy_snapshot_sha256':sha(run/'policy_snapshot.json'),'training_script_sha256':sha(Path(__file__)),
        'runtime_script_sha256':sha(ROOT/'dataset/pipelines/item10/classifier_runtime.py'),
        'elapsed_seconds':time.time()-started,'versions':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'joblib':joblib.__version__},
        'formal_human_gold_available':False,'deployment_allowed':False,'all_development_targets_met':all(m['all_applicable_targets_met'] for m in reports.values()),
        'remaining':[],'warnings':[w for c in summaries for w in c['warnings']]}
    save(run/'run_manifest.json',manifest)
    (run/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    print(json.dumps({'selected':selected['name'],'all_development_targets_met':manifest['all_development_targets_met'],'test_opened':False,'elapsed_seconds':manifest['elapsed_seconds']},indent=2),flush=True)

def final_test(run):
    current_policy=json.loads((ROOT/'dataset/pipelines/item10/evaluation_policy.json').read_text())
    if current_policy['data'].get('synthetic_test_already_opened'):
        raise ValueError('Original synthetic test was already opened. Reuse is development regression only; renewed final claims require a fresh independent holdout.')
    manifest=json.loads((run/'run_manifest.json').read_text());selection=json.loads((run/'selection_frozen.json').read_text())
    if manifest['synthetic_test_opened'] or (run/'synthetic_test_metrics.json').exists():raise ValueError('Test already opened; no repeated tuning/evaluation in this run.')
    assert sha(run/'classifier.joblib')==selection['model_sha256']==manifest['model_sha256']
    assert sha(ROOT/'dataset/pipelines/item10/classifier_runtime.py')==manifest['runtime_script_sha256']
    partitions,_,_,audit=sources();assert audit['source_sha256']==manifest['source_hashes']
    rows=partitions['test'];bundle=joblib.load(run/'classifier.joblib');policy=json.loads((run/'policy_snapshot.json').read_text())
    # Mark test opened before prediction; failures cannot silently permit another tuned run.
    manifest['synthetic_test_opened']=True;manifest['test_opened_with_model_sha256']=sha(run/'classifier.joblib');save(run/'run_manifest.json',manifest)
    preds=predict_records(bundle,rows)
    for r,p in zip(rows,preds):p.update(expected_primary=r['primary_label'],expected_scope=r['scope_label'],language_style=r['language_style'],scenario_family_id=r['leakage_group_id'])
    jsonl(run/'synthetic_test_predictions.jsonl',preds);metrics=evaluate(rows,preds,bootstrap=True);metrics['targets']=gates(metrics,policy);metrics['all_applicable_targets_met']=all(c['passed'] for c in metrics['targets']);save(run/'synthetic_test_metrics.json',metrics)
    manifest['status']='exploratory_test_complete';manifest['synthetic_test_all_targets_met']=metrics['all_applicable_targets_met'];manifest['deployment_allowed']=False;save(run/'run_manifest.json',manifest)
    print(json.dumps({'synthetic_test_primary_f1':metrics['primary']['macro_f1'],'synthetic_test_scope_f1':metrics['scope']['macro_f1'],'all_targets_met':metrics['all_applicable_targets_met'],'deployment_allowed':False},indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['develop','test'],required=True);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--experiment',choices=['baseline','strip_wrappers','compositional'],default='baseline');a=p.parse_args()
    train(a.run_dir.resolve(),a.experiment) if a.stage=='develop' else final_test(a.run_dir.resolve())

if __name__=='__main__':main()
