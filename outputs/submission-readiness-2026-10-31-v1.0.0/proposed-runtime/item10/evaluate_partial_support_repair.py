"""Score the opened original synthetic set as regressions, never as a fresh holdout."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import joblib
from classifier_runtime import predict_records
from train_classifier import sources,save,jsonl,sha,evaluate,gates,ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve()
    manifest=json.loads((run/'run_manifest.json').read_text());lineage=manifest['repair_lineage'];parent=Path(lineage['parent_run'])
    if (run/'opened_test_regression_metrics.json').exists() or (run/'repair_regression_freeze.json').exists():raise ValueError('Regression result already recorded; use a new version for further development')
    assert lineage['original_synthetic_test_previously_opened'] and lineage['original_synthetic_test_role']=='regression_only'
    assert json.loads((run/'software_tests.json').read_text())['passed']
    assert sha(parent/'classifier.joblib')==lineage['parent_model_sha256']
    assert sha(parent/'synthetic_test_metrics.json')==lineage['parent_original_holdout_metrics_sha256']
    selection=json.loads((run/'selection_frozen.json').read_text());assert sha(run/'classifier.joblib')==selection['model_sha256']==manifest['model_sha256']
    hashes={}
    for name in ['train_logical_classifier.py','logical_clause_model.py','clause_classifier.py','semantic_encoder.py','scope_constraints.py','classifier_runtime.py','train_classifier.py']:
        source=ROOT/'dataset/pipelines/item10'/name;assert sha(source)==sha(run/name);hashes[name]=sha(source)
    parts,_,_,audit=sources();assert audit['source_sha256']==manifest['source_hashes']
    save(run/'repair_regression_freeze.json',{'model_sha256':sha(run/'classifier.joblib'),'source_sha256':hashes,'thresholds':selection['thresholds'],'source_role':'previously opened synthetic test; regression only',
        'fresh_independent_holdout':False,'model_weights_and_calibration_fitted_on_these_rows':False,'preprocessing_fix_informed_by_prior_failures':True})
    rows=parts['test'];predictions=predict_records(joblib.load(run/'classifier.joblib'),rows)
    for r,v in zip(rows,predictions):v.update(expected_primary=r['primary_label'],expected_scope=r['scope_label'],language_style=r['language_style'],scenario_family_id=r['leakage_group_id'])
    jsonl(run/'opened_test_regression_predictions.jsonl',predictions);metrics=evaluate(rows,predictions,bootstrap=True);policy=json.loads((run/'policy_snapshot.json').read_text())
    metrics.update(targets=gates(metrics,policy),evaluation_role='Previously opened synthetic set: development regression only',fresh_independent_holdout=False)
    metrics['all_applicable_targets_met']=all(g['passed'] for g in metrics['targets']);save(run/'opened_test_regression_metrics.json',metrics)
    old={v['question_id']:v for v in map(json.loads,(parent/'synthetic_test_predictions.jsonl').read_text().splitlines())}
    changes=[];fixed=[];regressed=[]
    for v in predictions:
        prior=old[v['question_id']];expected=(v['expected_primary'],v['expected_scope']);before=(prior['predicted_primary'],prior['predicted_scope']);after=(v['predicted_primary'],v['predicted_scope'])
        if before!=after:changes.append({'question_id':v['question_id'],'expected':expected,'before':before,'after':after})
        if before!=expected and after==expected:fixed.append(v['question_id'])
        if before==expected and after!=expected:regressed.append(v['question_id'])
    summary={'role':'Development regression after an inspected test failure; not a fresh final accuracy estimate','parent':parent.name,'current':run.name,'corrected_question_ids':fixed,'regressed_question_ids':regressed,'changed_predictions':changes,
        'parent_partial_recall':json.loads((parent/'synthetic_test_metrics.json').read_text())['scope']['classification_report']['partially_supported']['recall'],
        'current_partial_precision':metrics['scope']['classification_report']['partially_supported']['precision'],'current_partial_recall':metrics['scope']['classification_report']['partially_supported']['recall'],
        'fresh_independent_holdout_required':True,'deployment_allowed':False}
    save(run/'repair_comparison.json',summary)
    manifest.update(status='partial_support_repair_regression_complete',original_synthetic_test_regression_evaluated=True,fresh_independent_holdout_evaluated=False,
        regression_targets_passed=metrics['all_applicable_targets_met'],deployment_allowed=False);save(run/'run_manifest.json',manifest)
    print(json.dumps({'partial_precision':summary['current_partial_precision'],'partial_recall':summary['current_partial_recall'],'corrected':len(fixed),'regressed':len(regressed),'primary_accuracy_regression_only':metrics['primary']['accuracy'],'fresh_holdout':False},indent=2))
if __name__=='__main__':main()
