"""Package classifier implementation repairs; defer performance evaluation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import joblib

from classifier_runtime import predict_records
from train_classifier import ROOT, sources, readrows, save, jsonl, sha

HERE = Path(__file__).resolve().parent


def build(parent, output):
    parent, output = parent.resolve(), output.resolve()
    if output.exists():
        raise ValueError('Use a new version directory')
    checks = json.loads((parent / 'artifact_checksums.json').read_text())
    for name, expected in checks.items():
        if sha(parent / name) != expected:
            raise ValueError('Frozen parent changed: ' + name)
    output.mkdir(parents=True)
    retained = ['calibration_folds.json', 'candidate_comparison.json', 'data_audit.json', 'policy_snapshot.json',
        'repair_lineage.json', 'requirements.lock.txt', 'selected_threshold_search.json',
        'taxonomy_training_glossary.jsonl', 'training_atoms.jsonl', 'unique_training_atoms.jsonl']
    for name in retained:
        shutil.copyfile(parent / name, output / name)
    for path in HERE.glob('*.py'):
        shutil.copyfile(path, output / path.name)
    old = joblib.load(parent / 'classifier.joblib')
    bundle = joblib.load(parent / 'classifier.joblib')
    bundle['model_version'] = output.name
    joblib.dump(bundle, output / 'classifier.joblib')
    bundle = joblib.load(output / 'classifier.joblib')
    a, b = old['primary_model'].engine, bundle['primary_model'].engine
    equal = {'atomic_weights': joblib.hash(a.atomic.model)==joblib.hash(b.atomic.model),
        'feature_vocabulary': joblib.hash(a.atomic.lexical)==joblib.hash(b.atomic.lexical),
        'calibration': joblib.hash(a.joint_model)==joblib.hash(b.joint_model),
        'thresholds': old['thresholds']==bundle['thresholds'],
        'training_membership': old['train_question_ids']==bundle['train_question_ids'] and old['train_group_ids']==bundle['train_group_ids']}
    if not all(equal.values()):
        raise ValueError('Inherited learned state changed')
    manifest = json.loads((parent / 'run_manifest.json').read_text())
    for key in ['all_development_targets_met', 'regression_targets_passed', 'focused_repair']:
        manifest.pop(key, None)
    manifest.update(model_version=output.name, as_of='2026-10-19', status='implementation_checks_pending',
        model_sha256=sha(output / 'classifier.joblib'), runtime_script_sha256=sha(HERE / 'classifier_runtime.py'),
        parent_classifier=parent.relative_to(ROOT).as_posix(), new_model_fitting=False,
        performance_evaluation_deferred=True, displayed_metrics_deferred=True, user_terminal_testing_deferred=True,
        original_synthetic_test_regression_evaluated=False, fresh_independent_holdout_evaluated=False,
        formal_acceptance_completed=False, website_integration_completed=False, llm_integration_completed=False)
    save(output / 'run_manifest.json', manifest)
    save(output / 'selection_frozen.json', {'selected_candidate': manifest['selected_candidate'],
        'selection_data': 'Parent configuration, trained weights, calibration and validation-selected thresholds inherited unchanged.',
        'model_sha256': manifest['model_sha256'], 'thresholds': bundle['thresholds'],
        'new_selection_or_fitting': False, 'fresh_independent_holdout_evaluated': False})
    save(output / 'implementation_lineage.json', {'parent': parent.relative_to(ROOT).as_posix(),
        'parent_checksums_sha256': sha(parent / 'artifact_checksums.json'), 'unchanged_learned_state': equal,
        'repair_informed_by_inspected_development_cases': True, 'new_training_questions': 0})
    parts, general, typing, audit = sources()
    assert audit['source_sha256']==manifest['source_hashes']
    # Replay data supports persistence/software assertions only. No new accuracy,
    # F1, calibration, bootstrap or acceptance metrics are produced by this build.
    for name, data in [('validation', parts['validation']), ('ai_general_development', general), ('ai_typing_development', typing)]:
        jsonl(output / (name + '_predictions.jsonl'), predict_records(bundle, data))
    baseline = ROOT / 'outputs/item13-evaluation-v1.0.1/error_log.jsonl'
    inspected = readrows(baseline)
    route_audit = []
    for case, result in zip(inspected, predict_records(bundle, [{'question_text': r['expected']['question_text']} for r in inspected])):
        route_audit.append({'case_id': case['case_id'], 'question_text': result['question_text'],
            'before_action': case['actual']['classification']['routing_action'],
            'before_reason': case['actual']['classification']['reason'],
            'after_action': result['routing_action'], 'after_reason': result['reason'],
            'expected_action': case['expected']['expected_route'],
            'implementation_expectation_met': result['routing_action']==case['expected']['expected_route'],
            'role': 'Inspected regression scenario; not independent evaluation'})
    save(output / 'routing_implementation_audit.json', route_audit)
    if not all(r['implementation_expectation_met'] for r in route_audit):
        raise ValueError('An inspected routing repair remains unresolved')
    with (output / 'software_tests.log').open('w',encoding='utf-8') as log:
        result = subprocess.run([sys.executable, str(HERE / 'test_logical_classifier.py'), '--run-dir', str(output)],
            stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError('Classifier software checks failed; inspect ' + str(output / 'software_tests.log'))
    tests = json.loads((output / 'software_tests.json').read_text())
    manifest['status']='implementation_software_checked_performance_evaluation_pending'
    manifest['software_tests']=tests
    save(output / 'run_manifest.json', manifest)
    card = {'model_version': output.name, 'status': manifest['status'],
        'parent_classifier': manifest['parent_classifier'], 'training_parent_rows': 459, 'unique_atomic_fit_texts': 222,
        'new_training_questions': 0, 'unchanged_learned_state': equal, 'thresholds': bundle['thresholds'],
        'software_tests': tests, 'routing_repairs': 'Anaphoric follow-ups, background versus complaints, bounded spelling aliases and scope/workplace boundaries; conservative spelling/boundary features before concern detection.',
        'software_replay_role': 'Inspected regression assertions only; not a new performance evaluation.',
        'formal_evaluation_completed': False, 'display_metrics_implemented': False, 'independent_human_gold_available': False,
        'website_integration_completed': False, 'llm_integration_completed': False,
        'deployment_allowed': False, 'answer_generation_allowed': False,
        'limitations': ['Rule changes were informed by inspected development cases.',
            'Label confidence does not measure legal-answer correctness.',
            'Final performance/calibration evaluation and formal acceptance remain pending.']}
    save(output / 'MODEL_CARD.json', card)
    save(output / 'deferred_evaluation.json', {'user_requested_deferral': True,
        'formal_performance_evaluation_pending': True, 'metric_presentation_pending': True,
        'interactive_terminal_testing_pending': True, 'independent_human_input_pending': True,
        'new_accuracy_f1_or_calibration_report_produced': False,
        'historical_evaluation': 'outputs/item13-evaluation-v1.0.1',
        'original_policy_snapshot_role': 'Historical training/threshold policy; current implementation status is in run_manifest.json.'})
    save(output / 'artifact_checksums.json', {p.relative_to(output).as_posix(): sha(p)
        for p in sorted(output.rglob('*')) if p.is_file()})
    print(json.dumps({'model_version': output.name, 'software_tests': tests,
        'learned_state_unchanged': all(equal.values()), 'performance_evaluation_deferred': True}, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    build(args.parent,args.output)
