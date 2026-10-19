"""One-shot synthetic holdout check after development and software gates pass."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib
from classifier_runtime import predict_records
from train_classifier import sources,save,jsonl,sha,evaluate,gates,ROOT

def ensure_unopened_source(manifest,current_policy):
    if manifest.get('original_synthetic_test_previously_opened') or current_policy['data'].get('synthetic_test_already_opened'):
        raise ValueError('Original synthetic test was opened in a prior run. Use explicitly labeled regression evaluation; final claims require a fresh independent holdout.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve()
    manifest=json.loads((run/'run_manifest.json').read_text());selection=json.loads((run/'selection_frozen.json').read_text());policy=json.loads((run/'policy_snapshot.json').read_text());tests=json.loads((run/'software_tests.json').read_text())
    current_policy=json.loads((ROOT/'dataset/pipelines/item10/evaluation_policy.json').read_text())
    ensure_unopened_source(manifest,current_policy)
    if manifest['synthetic_test_opened'] or (run/'synthetic_test_metrics.json').exists() or (run/'final_evaluation_freeze.json').exists():raise ValueError('Synthetic holdout already opened or attempted; no repeated tuning/evaluation')
    assert manifest['all_development_targets_met'] and tests['passed']
    assert not manifest['deployment_allowed'] and not policy['deployment_authorized']
    assert sha(run/'classifier.joblib')==selection['model_sha256']==manifest['model_sha256']
    source_hashes={}
    for name in ['train_logical_classifier.py','logical_clause_model.py','clause_classifier.py','semantic_encoder.py','scope_constraints.py','classifier_runtime.py','train_classifier.py']:
        current=ROOT/'dataset/pipelines/item10'/name;assert sha(current)==sha(run/name),'Source changed after development: '+name;source_hashes[name]=sha(current)
    parts,_,_,audit=sources();assert audit['source_sha256']==manifest['source_hashes']
    save(run/'final_evaluation_freeze.json',{'model_sha256':sha(run/'classifier.joblib'),'policy_sha256':sha(run/'policy_snapshot.json'),'source_hashes':source_hashes,'software_tests_sha256':sha(run/'software_tests.json'),
        'thresholds':selection['thresholds'],'synthetic_holdout_rows':100,'development_gates_passed':True,'purpose':'Supplementary synthetic holdout only; does not replace independent human gold','opened_once':True,'further_tuning_requires_new_independent_holdout':True})
    manifest.update(synthetic_test_opened=True,test_opened_with_model_sha256=sha(run/'classifier.joblib'));save(run/'run_manifest.json',manifest)
    rows=parts['test'];predictions=predict_records(joblib.load(run/'classifier.joblib'),rows)
    for r,v in zip(rows,predictions):v.update(expected_primary=r['primary_label'],expected_scope=r['scope_label'],language_style=r['language_style'],scenario_family_id=r['leakage_group_id'])
    jsonl(run/'synthetic_test_predictions.jsonl',predictions);metrics=evaluate(rows,predictions,bootstrap=True);metrics['targets']=gates(metrics,policy);metrics['all_applicable_targets_met']=all(g['passed'] for g in metrics['targets']);metrics['evaluation_role']='Supplementary synthetic holdout, not independent human-written gold';save(run/'synthetic_test_metrics.json',metrics)
    manifest.update(status='exploratory_synthetic_test_complete',synthetic_test_all_targets_met=metrics['all_applicable_targets_met'],deployment_allowed=False);save(run/'run_manifest.json',manifest)
    print(json.dumps({'synthetic_test_primary_accuracy':metrics['primary']['accuracy'],'primary_macro_F1':metrics['primary']['macro_f1'],'scope_macro_F1':metrics['scope']['macro_f1'],'all_targets_met':metrics['all_applicable_targets_met'],'deployment_allowed':False},indent=2))
if __name__=='__main__':main()
