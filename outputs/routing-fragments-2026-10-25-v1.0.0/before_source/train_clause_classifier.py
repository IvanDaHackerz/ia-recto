"""Purged grouped stacking over training-only atomic cases and a fixed semantic encoder."""
from __future__ import annotations
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(k,'1')
import argparse,json,csv,time,collections,subprocess,sys,hashlib
from pathlib import Path
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from clause_classifier import training_atoms,glossary_atoms,deduplicate,split_clauses,state_of,AtomicClassifier,ClauseEngine,ClauseHead
from semantic_encoder import encode,preload,save_cache,MODEL_NAME
from classifier_runtime import predict_records
from train_classifier import sources,save,jsonl,sha,evaluate,gates,select_thresholds,SEED,ROOT

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,required=True);a=parser.parse_args();run=a.run_dir.resolve()
    if run.exists():raise ValueError('Use a new run directory')
    parts,general,typing,audit=sources();train=parts['train'];val=parts['validation'];policy=json.loads((ROOT/'dataset/pipelines/item10/evaluation_policy.json').read_text())
    assert policy['exploratory_training_authorized']
    with (ROOT/'dataset/data_contract/topic_taxonomy.csv').open(encoding='utf-8-sig',newline='') as f:taxonomy=list(csv.DictReader(f))
    atoms=[a for r in train for a in training_atoms(r)];glossary=glossary_atoms(taxonomy)
    # Check derived atoms against actual development input text; no development questions are fitted.
    protected={ ' '.join(''.join(c.lower() if c.isalnum() else ' ' for c in r['question_text']).split()) for r in val+general+typing }
    unique=deduplicate(atoms+glossary);assert not {a['normalized_fact'] for a in unique}&protected
    run.mkdir(parents=True);started=time.time();jsonl(run/'training_atoms.jsonl',atoms);jsonl(run/'taxonomy_training_glossary.jsonl',glossary);jsonl(run/'unique_training_atoms.jsonl',unique)
    audit.update({'experiment':'purged_atomic_semantic_stacking','training_parent_rows':459,'raw_derived_atoms':len(atoms),'unique_training_atoms_with_glossary':len(unique),'taxonomy_definition_rows':len(glossary),'taxonomy_sha256':sha(ROOT/'dataset/data_contract/topic_taxonomy.csv'),
        'derived_atom_status':'AI-derived from human-reviewed training parents; no independent human review of atom extraction is claimed','frozen_training_modified':False,'heldout_questions_fitted':False,
        'external_backbone':MODEL_NAME,'backbone_finetuned':False,'benchmark_design_informed_by_prior_development_errors':True})
    save(run/'data_audit.json',audit);save(run/'policy_snapshot.json',policy)
    y=np.array([state_of(r) for r in train]);groups=np.array([r['leakage_group_id'] for r in train]);texts=[r['question_text'] for r in train]
    folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=SEED).split(texts,y,groups))
    split_audit=[]
    for n,(fit,held) in enumerate(folds):
        held_facts={a['normalized_fact'] for a in deduplicate([a for i in held for a in training_atoms(train[i])])}
        fit_atoms=deduplicate([a for i in fit for a in training_atoms(train[i])])
        kept=[a for a in fit_atoms if a['normalized_fact'] not in held_facts]
        assert not set(groups[fit])&set(groups[held]);assert not {a['normalized_fact'] for a in kept}&held_facts
        assert set(a['category'] for a in kept+glossary)=={'labor','consumer','excluded'}
        split_audit.append({'fold':n,'fit_parent_count':len(fit),'held_parent_count':len(held),'fit_group_ids':sorted(set(groups[fit])),'held_group_ids':sorted(set(groups[held])),
            'fit_atom_count_before_purge':len(fit_atoms),'shared_atomic_facts_purged':len(fit_atoms)-len(kept),'fit_atom_count_after_purge':len(kept),'held_fact_count':len(held_facts),'atomic_fact_overlap_after_purge':0})
    save(run/'purged_calibration_folds.json',split_audit)
    print(json.dumps({'training_parents':459,'derived_atoms':len(atoms),'unique_atoms_with_taxonomy':len(unique),'purged_folds':split_audit},ensure_ascii=False),flush=True)
    cache=ROOT/'tmp/item10_semantic_vectors.npz';preload(cache)
    # Fixed pretrained encoding is inference, not fitting. Synthetic test text is not encoded.
    preload_texts=list(dict.fromkeys([a['text'] for a in unique]+[p for r in train+val+general+typing for p in split_clauses(r['question_text'])]))
    print('Encoding '+str(len(preload_texts))+' training/development clauses locally',flush=True)
    encode(preload_texts);save_cache(cache)
    configs=[{'feature_kind':kind,'C':C,'semantic_weight':2.0 if kind=='hybrid' else 1.0} for kind in ['lexical','semantic','hybrid'] for C in [1.,10.,100.]]
    save(run/'atomic_configs.json',configs);comparisons=[];best=None
    for config in configs:
        label=config['feature_kind']+'_C'+str(int(config['C']));print('Fit '+label,flush=True);oof=np.zeros((459,6))
        for fit,held in folds:
            forbidden={a['normalized_fact'] for a in deduplicate([a for i in held for a in training_atoms(train[i])])}
            material=deduplicate([a for i in fit for a in training_atoms(train[i])]);material=[a for a in material if a['normalized_fact'] not in forbidden]+glossary
            atomic=AtomicClassifier(**config).fit(material);oof[held]=atomic.question_features([texts[i] for i in held])
        final_atomic=AtomicClassifier(**config).fit(atoms+glossary)
        for metaC in [1.,10.,100.]:
            joint=LogisticRegression(C=metaC,class_weight='balanced',max_iter=2000,random_state=SEED).fit(oof,y)
            engine=ClauseEngine(final_atomic,joint)
            bundle={'model_version':run.name,'config':dict(config,meta_C=metaC),'primary_model':ClauseHead('primary',engine),'scope_model':ClauseHead('scope',engine),'thresholds':{'primary':0.,'scope':0.},
                'seed':SEED,'policy_version':policy['policy_version'],'train_question_ids':[r['question_id'] for r in train],'train_group_ids':sorted(set(groups)),'deployment_allowed':False,
                'additional_training_source':'42 project taxonomy definitions; atomic derivatives from training parents only'}
            predictions=predict_records(bundle,val);thresholds,search,chosen=select_thresholds(val,predictions,policy);bundle['thresholds']=thresholds
            predictions=predict_records(bundle,val);m=evaluate(val,predictions);checks=gates(m,policy)
            summary={'name':label+'_metaC'+str(int(metaC)),'config':bundle['config'],'validation':m,'gates':checks,'all_validation_targets_met':all(g['passed'] for g in checks),'thresholds':thresholds}
            comparisons.append(summary)
            rank=(summary['all_validation_targets_met'],sum(g['passed'] for g in checks),min(m['primary']['macro_f1'],m['scope']['macro_f1']),(m['primary']['macro_f1']+m['scope']['macro_f1'])/2,-m['primary']['log_loss']-m['scope']['log_loss'])
            if best is None or rank>best[0]:best=(rank,bundle,summary,search)
            print(json.dumps({'candidate':summary['name'],'pF1':m['primary']['macro_f1'],'sF1':m['scope']['macro_f1'],'partial_recall':m['scope']['classification_report']['partially_supported']['recall'],'coverage':m['routing']['decisive_coverage']}),flush=True)
    rank,bundle,selected,search=best;joblib.dump(bundle,run/'classifier.joblib',compress=3);save(run/'candidate_comparison.json',comparisons);save(run/'selected_threshold_search.json',search)
    selection={'selected_candidate':selected['name'],'selection_data':'102 seed validation rows only','selection_rule':'target attainment, then number of passing targets, minimum macro F1, mean macro F1 and log loss','model_sha256':sha(run/'classifier.joblib'),'thresholds':bundle['thresholds'],'test_opened':False,'benchmark_results_used_for_within_run_selection':False,'experiment_design_informed_prior_benchmark_errors':True}
    save(run/'selection_frozen.json',selection)
    reports={}
    for name,rows in [('validation',val),('ai_general_development',general),('ai_typing_development',typing)]:
        predictions=predict_records(bundle,rows)
        for r,p in zip(rows,predictions):p.update(expected_primary=r.get('primary_label'),expected_scope=r.get('scope_label'),expected_action=r.get('expected_action','classify'),language_style=r['language_style'],scenario_family_id=r.get('scenario_family_id',r.get('leakage_group_id')),variation_type=r.get('variation_type'))
        jsonl(run/(name+'_predictions.jsonl'),predictions);m=evaluate(rows,predictions,bootstrap=True);m['targets']=gates(m,policy,include_clarification=name=='ai_typing_development');m['all_applicable_targets_met']=all(g['passed'] for g in m['targets']);reports[name]=m;save(run/(name+'_metrics.json'),m)
    save_cache(cache)
    manifest={'model_version':run.name,'status':'exploratory_development_complete','selected_candidate':selected['name'],'as_of':'2026-10-17','training_parent_rows':459,
        'additional_training_rows':{'atomic_derivatives':len(atoms),'taxonomy_definitions':len(glossary),'unique_atoms_with_glossary':len(unique)},'training_sources':audit['source_sha256'],
        'model_sha256':sha(run/'classifier.joblib'),'runtime_sha256':sha(ROOT/'dataset/pipelines/item10/clause_classifier.py'),'encoder':MODEL_NAME,'encoder_manifest_sha256':sha(ROOT/'models/embedding_backbone_manifest.json'),
        'synthetic_test_opened':False,'deployment_allowed':False,'formal_human_gold_available':False,'all_development_targets_met':all(m['all_applicable_targets_met'] for m in reports.values()),
        'confidence_method':'Joint state probability model fitted on training-only OOF evidence from group-disjoint, atomic-fact-purged base models. Calibration is empirically checked; no real-world guarantee.',
        'experiment_design_informed_prior_development_errors':True,'elapsed_seconds':time.time()-started}
    save(run/'run_manifest.json',manifest);(run/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    print(json.dumps({'selected':selected['name'],'all_development_targets_met':manifest['all_development_targets_met'],'elapsed_seconds':manifest['elapsed_seconds'],'results':{n:{'primary_accuracy':m['primary']['accuracy'],'primary_f1':m['primary']['macro_f1'],'scope_f1':m['scope']['macro_f1'],'partial_recall':m['scope']['classification_report']['partially_supported']['recall'],'mixed_recall':m['primary']['classification_report']['mixed']['recall'],'coverage':m['routing']['decisive_coverage']} for n,m in reports.items()}},indent=2),flush=True)

if __name__=='__main__':main()
