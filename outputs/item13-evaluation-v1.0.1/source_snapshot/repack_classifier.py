"""Package a bounded scope-rule repair without fitting models or thresholds."""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PIPELINE = ROOT / 'dataset/pipelines/item10'
sys.path.insert(0, str(PIPELINE))
import joblib
from classifier_runtime import predict_records
from train_classifier import sources, evaluate, gates, readrows, save, jsonl, sha


def build(parent, output):
    parent, output = Path(parent).resolve(), Path(output).resolve()
    checks = __import__('json').loads((parent / 'artifact_checksums.json').read_text())
    for name, expected in checks.items():
        if sha(parent / name) != expected:
            raise ValueError('Parent checksum mismatch: ' + name)
    if output.exists():
        raise ValueError('Use a new version directory')
    old = joblib.load(parent / 'classifier.joblib')
    bundle = joblib.load(parent / 'classifier.joblib')
    bundle['model_version'] = output.name
    old_engine = old['primary_model'].engine
    engine = bundle['primary_model'].engine
    unchanged = {
        'atomic_model': joblib.hash(old_engine.atomic.model) == joblib.hash(engine.atomic.model),
        'lexical_features': joblib.hash(old_engine.atomic.lexical) == joblib.hash(engine.atomic.lexical),
        'joint_calibration': joblib.hash(old_engine.joint_model) == joblib.hash(engine.joint_model),
        'thresholds': old['thresholds'] == bundle['thresholds'],
        'training_membership': old['train_question_ids'] == bundle['train_question_ids']
            and old['train_group_ids'] == bundle['train_group_ids'],
    }
    if not all(unchanged.values()):
        raise ValueError('Learned state changed')
    shutil.copytree(parent, output)
    (output / 'artifact_checksums.json').unlink()
    # These opened-regression outputs are generated again below in the new packet.
    for name in ['opened_test_regression_metrics.json', 'opened_test_regression_predictions.jsonl',
                 'repair_regression_freeze.json']:
        (output / name).unlink()
    for path in parent.glob('*.py'):
        current = PIPELINE / path.name
        if current.exists():
            shutil.copyfile(current, output / path.name)
    joblib.dump(bundle, output / 'classifier.joblib')
    load = lambda name: __import__('json').loads((output / (name + '.json')).read_text())
    manifest, selection, card = (load(n) for n in ['run_manifest', 'selection_frozen', 'MODEL_CARD'])
    focused = {'parent': parent.relative_to(ROOT).as_posix(), 'parent_model_sha256': sha(parent / 'classifier.joblib'),
        'scope': 'Taglish public disclosure scope recognition; inspected Item 13 development failure.',
        'new_fitting': False, 'threshold_selection': False, 'unchanged_learned_state': unchanged}
    manifest.update(model_version=output.name, model_sha256=sha(output / 'classifier.joblib'),
        status='focused_scope_repair_development', focused_repair=focused,
        runtime_script_sha256=sha(PIPELINE / 'classifier_runtime.py'))
    selection.update(model_sha256=manifest['model_sha256'],
        selection_data='Configuration, fitted calibration and thresholds inherited unchanged from parent.',
        selection_rule='Bounded runtime scope repair informed by inspected Item 13 development errors.',
        focused_repair_parent=focused['parent'])
    save(output / 'selection_frozen.json', selection)
    save(output / 'focused_repair_lineage.json', focused)
    parts, general, typing, audit = sources()
    assert audit['source_sha256'] == manifest['source_hashes']
    policy = load('policy_snapshot')
    all_passed = True
    for name, data in [('validation', parts['validation']), ('ai_general_development', general),
                       ('ai_typing_development', typing)]:
        predictions = predict_records(bundle, data)
        metrics = evaluate(data, predictions, bootstrap=True)
        metrics['targets'] = gates(metrics, policy, include_clarification=name == 'ai_typing_development')
        metrics['all_applicable_targets_met'] = all(g['passed'] for g in metrics['targets'])
        metrics['evaluation_role'] = 'Inspected development regression; no fresh independent accuracy estimate'
        all_passed &= metrics['all_applicable_targets_met']
        save(output / (name + '_metrics.json'), metrics)
        jsonl(output / (name + '_predictions.jsonl'), predictions)
    manifest['all_development_targets_met'] = all_passed
    save(output / 'run_manifest.json', manifest)
    subprocess.run([sys.executable, str(PIPELINE / 'test_logical_classifier.py'), '--run-dir', str(output)], check=True)
    subprocess.run([sys.executable, str(PIPELINE / 'evaluate_partial_support_repair.py'), '--run-dir', str(output)], check=True)
    regression, tests = load('opened_test_regression_metrics'), load('software_tests')
    parent_predictions = {p['question_id']: p for p in readrows(parent / 'opened_test_regression_predictions.jsonl')}
    regressed = [p['question_id'] for p in readrows(output / 'opened_test_regression_predictions.jsonl')
        if all(parent_predictions[p['question_id']]['predicted_' + h] == p['expected_' + h] for h in ['primary', 'scope'])
        and any(p['predicted_' + h] != p['expected_' + h] for h in ['primary', 'scope'])]
    card.update(model_version=output.name, status='focused_scope_repair_development',
        development_targets_passed=all_passed, focused_repair=focused,
        regression_accuracy=regression['primary']['accuracy'],
        regression_decisive_coverage=regression['routing']['decisive_coverage'],
        regression_partial_recall=regression['scope']['classification_report']['partially_supported']['recall'],
        regression_partial_precision=regression['scope']['classification_report']['partially_supported']['precision'],
        all_regression_targets_passed=regression['all_applicable_targets_met'],
        regression_new_classification_errors=len(regressed), software_tests_passed=tests['tests_run'])
    save(output / 'MODEL_CARD.json', card)
    save(output / 'focused_regression_comparison.json', {'parent': focused['parent'], 'regressed_question_ids': regressed,
        'fresh_holdout': False, 'unchanged_learned_state': unchanged})
    (output / 'REPAIR_REPORT.md').write_text(
        f'# Classifier scope repair\n\nVersion: {output.name}. Parent: {parent.name}.\n\n'
        'Recognizes bounded Taglish public disclosure of private data. Ordinary delivery addresses and negated disclosures have regression controls.\n\n'
        f"{tests['tests_run']} software tests pass. Opened original development regression: "
        f"{regression['primary']['accuracy']:.1%} primary accuracy; {len(regressed)} new classification regressions.\n\n"
        'Weights, feature vocabulary, calibration, training membership and confidence thresholds are inherited unchanged. '
        'No training or independent human questions were added. Results are inspected development evidence. '
        'Historical selection files and original-parent repair comparison retain their historical roles. '
        'The focused comparison records the immediate parent. Live answering and deployment remain disabled.\n', encoding='utf-8')
    if regressed or not all_passed or not regression['all_applicable_targets_met']:
        raise ValueError('Regression targets failed; no current pointer changed')
    save(output / 'artifact_checksums.json', {p.relative_to(output).as_posix(): sha(p)
        for p in sorted(output.rglob('*')) if p.is_file()})
    print(output.name + ': packaged with unchanged learned state', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.parent, args.output)
