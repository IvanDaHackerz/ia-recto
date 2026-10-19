"""Explicit component union; probabilities calibrated on purged training-only grouped folds."""
from __future__ import annotations
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(key,'1')
import argparse,csv,json,time,subprocess,sys,shutil
from pathlib import Path
import numpy as np
import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedGroupKFold
from clause_classifier import training_atoms,glossary_atoms,deduplicate,state_of,split_clauses
from logical_clause_model import LogicalClauseEstimator,LogicalClauseEngine,LogicalClauseHead,normalized_fact,fact_texts
from semantic_encoder import preload,save_cache,encode,MODEL_NAME
from classifier_runtime import predict_records
from train_classifier import sources,save,jsonl,sha,evaluate,gates,select_thresholds,ROOT,SEED

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--scope-constraints',action='store_true');parser.add_argument('--calibration',choices=['sigmoid','temperature'],default='sigmoid');parser.add_argument('--parent-run',type=Path);a=parser.parse_args();run=a.run_dir.resolve()
    if run.exists():raise ValueError('Never overwrite an experiment')
    parts,general,typing,audit=sources();train=parts['train'];val=parts['validation'];policy=json.loads((ROOT/'dataset/pipelines/item10/evaluation_policy.json').read_text())
    assert policy['exploratory_training_authorized'] and not policy['deployment_authorized']
    parent=None;lineage=None
    if a.parent_run:
        parent=a.parent_run.resolve();parent_manifest=json.loads((parent/'run_manifest.json').read_text())
        for name,h in json.loads((parent/'artifact_checksums.json').read_text()).items():
            if sha(parent/name)!=h:raise ValueError('Parent artifact changed: '+name)
        if not parent_manifest['synthetic_test_opened']:raise ValueError('Repair lineage expects the previously evaluated parent')
        previous_bundle=joblib.load(parent/'classifier.joblib')
        if previous_bundle['calibration_method']!=a.calibration:raise ValueError('Keep the parent calibration method fixed for this repair')
        lineage={'parent_run':str(parent),'parent_model_sha256':sha(parent/'classifier.joblib'),'parent_original_holdout_metrics_sha256':sha(parent/'synthetic_test_metrics.json'),
            'original_synthetic_test_previously_opened':True,'original_synthetic_test_role':'regression_only','fix_informed_by_opened_holdout_errors':True,
            'candidate_configuration_inherited':True,'fresh_independent_holdout_required':True}
    with (ROOT/'dataset/data_contract/topic_taxonomy.csv').open(encoding='utf-8-sig',newline='') as f:taxonomy=list(csv.DictReader(f))
    glossary=glossary_atoms(taxonomy);atoms=[a for r in train for a in training_atoms(r)];unique=deduplicate(atoms+glossary)
    protected={normalized_fact(r['question_text']) for r in val+general+typing};assert not {a['normalized_fact'] for a in unique}&protected
    run.mkdir(parents=True);started=time.time();texts=np.array([r['question_text'] for r in train]);y=np.array([state_of(r) for r in train]);groups=np.array([r['leakage_group_id'] for r in train])
    folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=SEED).split(texts,y,groups));fold_report=[]
    for i,(fit,held) in enumerate(folds):
        assert not set(groups[fit])&set(groups[held])
        forbidden={normalized_fact(t) for p in texts[held] for t in fact_texts(p)}
        material=[a for j in fit for a in training_atoms(train[j])];kept=[a for a in material if normalized_fact(a['text']) not in forbidden]
        assert not {normalized_fact(a['text']) for a in kept+glossary}&forbidden
        fold_report.append({'fold':i,'fit_rows':len(fit),'calibration_rows':len(held),'fit_group_ids':sorted(set(groups[fit])),'calibration_group_ids':sorted(set(groups[held])),
            'shared_atomic_fact_rows_purged':len(material)-len(kept),'atomic_fact_overlap_after_purge':0,'fit_parent_ids':[train[j]['question_id'] for j in fit],'held_parent_ids':[train[j]['question_id'] for j in held]})
    save(run/'calibration_folds.json',fold_report);jsonl(run/'training_atoms.jsonl',atoms);jsonl(run/'taxonomy_training_glossary.jsonl',glossary);jsonl(run/'unique_training_atoms.jsonl',unique)
    audit.update(experiment='logical_clause_union',raw_derived_atoms=len(atoms),unique_training_atoms_with_glossary=len(unique),taxonomy_definition_rows=len(glossary),taxonomy_sha256=sha(ROOT/'dataset/data_contract/topic_taxonomy.csv'),
        derived_atom_status='AI-derived from human-reviewed training parents; extraction not independently human reviewed',heldout_questions_fitted=False,external_backbone=MODEL_NAME,backbone_finetuned=False,benchmark_design_informed_prior_development_errors=True)
    if lineage:audit['repair_lineage']=lineage;save(run/'repair_lineage.json',lineage)
    save(run/'data_audit.json',audit);save(run/'policy_snapshot.json',policy)
    configs=[previous_bundle['config']] if parent else [{'feature_kind':kind,'C':C,'semantic_weight':2. if kind=='hybrid' else 1.,'use_scope_constraints':a.scope_constraints} for kind in ['lexical','semantic','hybrid'] for C in [1.,10.,100.]]
    cache=ROOT/'tmp/item10_semantic_vectors.npz';uses_encoder=any(c['feature_kind']!='lexical' for c in configs)
    if uses_encoder:
        preload(cache);encode(list(dict.fromkeys([a['text'] for a in unique]+[p for r in train+val+general+typing for p in split_clauses(r['question_text'])])));save_cache(cache)
    comparisons=[];best=None
    for config in configs:
        kind=config['feature_kind'];C=config['C']
        print('Training '+kind+' C='+str(C),flush=True)
        estimator=LogicalClauseEstimator(**config,training_texts=list(texts),glossary=glossary)
        joint=CalibratedClassifierCV(estimator,method=a.calibration,cv=folds,ensemble=False,n_jobs=1).fit(texts,y)
        engine=LogicalClauseEngine(joint,joint.calibrated_classifiers_[0].estimator.atomic)
        bundle={'model_version':run.name,'config':config,'primary_model':LogicalClauseHead('primary',engine),'scope_model':LogicalClauseHead('scope',engine),'thresholds':{'primary':0.,'scope':0.},
            'seed':SEED,'policy_version':policy['policy_version'],'train_question_ids':[r['question_id'] for r in train],'train_group_ids':sorted(set(groups)),'deployment_allowed':False,
            'additional_training_source':'42 taxonomy definitions plus atomic derivatives of training parents only','resolve_mixed_components':a.scope_constraints,'calibration_method':a.calibration,
            'referral_routing_enabled':True}
        predictions=predict_records(bundle,val);thresholds,search,_=select_thresholds(val,predictions,policy);bundle['thresholds']=thresholds
        m=evaluate(val,predict_records(bundle,val));checks=gates(m,policy);name=kind+'_C'+str(int(C))
        summary={'name':name,'config':config,'validation':m,'gates':checks,'all_validation_targets_met':all(g['passed'] for g in checks),'thresholds':thresholds};comparisons.append(summary)
        rank=(summary['all_validation_targets_met'],sum(g['passed'] for g in checks),min(m['primary']['macro_f1'],m['scope']['macro_f1']),(m['primary']['macro_f1']+m['scope']['macro_f1'])/2,-m['primary']['log_loss']-m['scope']['log_loss'])
        if best is None or rank>best[0]:best=(rank,bundle,summary,search)
        print(json.dumps({'candidate':name,'primary_F1':m['primary']['macro_f1'],'scope_F1':m['scope']['macro_f1'],'mixed_recall':m['primary']['classification_report']['mixed']['recall'],'partial_recall':m['scope']['classification_report']['partially_supported']['recall'],'coverage':m['routing']['decisive_coverage'],'thresholds':thresholds}),flush=True)
    _,bundle,selected,search=best;joblib.dump(bundle,run/'classifier.joblib',compress=3);save(run/'candidate_comparison.json',comparisons);save(run/'selected_threshold_search.json',search)
    save(run/'selection_frozen.json',{'selected_candidate':selected['name'],'selection_data':'Configuration inherited from parent; thresholds selected on 102 validation rows only' if parent else '102 seed validation rows only','selection_rule':'Inherit parent configuration for focused preprocessing repair' if parent else 'target attainment, passing target count, minimum F1, mean F1, log loss','model_sha256':sha(run/'classifier.joblib'),'thresholds':bundle['thresholds'],'test_opened':False,'development_benchmarks_used_for_selection':False,'experiment_design_informed_prior_benchmark_errors':True,'repair_lineage':lineage})
    reports={}
    for name,rows in [('validation',val),('ai_general_development',general),('ai_typing_development',typing)]:
        predictions=predict_records(bundle,rows)
        for r,p in zip(rows,predictions):p.update(expected_primary=r.get('primary_label'),expected_scope=r.get('scope_label'),expected_action=r.get('expected_action','classify'),language_style=r['language_style'],scenario_family_id=r.get('scenario_family_id',r.get('leakage_group_id')),variation_type=r.get('variation_type'))
        jsonl(run/(name+'_predictions.jsonl'),predictions);m=evaluate(rows,predictions,bootstrap=True);m['targets']=gates(m,policy,include_clarification=name=='ai_typing_development');m['all_applicable_targets_met']=all(g['passed'] for g in m['targets']);reports[name]=m;save(run/(name+'_metrics.json'),m)
    if uses_encoder:save_cache(cache)
    manifest={'model_version':run.name,'status':'exploratory_development_complete','selected_candidate':selected['name'],'as_of':'2026-10-17','training_parent_rows':459,'additional_training_rows':{'atomic_derivatives':len(atoms),'taxonomy_definitions':len(glossary),'unique_atoms_with_glossary':len(unique)},
        'source_hashes':audit['source_sha256'],'model_sha256':sha(run/'classifier.joblib'),'runtime_script_sha256':sha(ROOT/'dataset/pipelines/item10/classifier_runtime.py'),'encoder':MODEL_NAME,'encoder_manifest_sha256':sha(ROOT/'models/embedding_backbone_manifest.json'),
        'selected_feature_kind':bundle['config']['feature_kind'],'encoder_used_by_selected_model':bundle['config']['feature_kind']!='lexical',
        'synthetic_test_opened':False,'deployment_allowed':False,'formal_human_gold_available':False,'all_development_targets_met':all(m['all_applicable_targets_met'] for m in reports.values()),
        'confidence_method':'Three-fold group-disjoint calibration, shared atomic facts purged per fold, '+a.calibration+' joint-state calibration. Chosen labels use explicit component union; confidence is posterior mass assigned to that chosen label, not necessarily maximum probability.',
        'experiment_design_informed_prior_development_errors':True,'elapsed_seconds':time.time()-started}
    if lineage:manifest.update(repair_lineage=lineage,original_synthetic_test_previously_opened=True,fresh_independent_holdout_required=True)
    save(run/'run_manifest.json',manifest)
    for name in ['train_logical_classifier.py','logical_clause_model.py','clause_classifier.py','semantic_encoder.py','scope_constraints.py','classifier_runtime.py','referral_routing.py','train_classifier.py']:shutil.copy2(Path(__file__).parent/name,run/name)
    (run/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    print(json.dumps({'selected':selected['name'],'all_development_targets_met':manifest['all_development_targets_met'],'results':{n:{'primary_accuracy':m['primary']['accuracy'],'primary_f1':m['primary']['macro_f1'],'scope_f1':m['scope']['macro_f1'],'partial_recall':m['scope']['classification_report']['partially_supported']['recall'],'mixed_recall':m['primary']['classification_report']['mixed']['recall'],'coverage':m['routing']['decisive_coverage']} for n,m in reports.items()}},indent=2),flush=True)

if __name__=='__main__':main()
