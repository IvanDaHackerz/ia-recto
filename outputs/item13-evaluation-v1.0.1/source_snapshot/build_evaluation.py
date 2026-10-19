"""Build a new versioned offline evaluation packet, with truthful pending gates."""
from __future__ import annotations
import argparse
import io
import platform
import shutil
import unittest
from collections import Counter
from pathlib import Path

from evaluation_common import ROOT, HERE, CASE_SCHEMA, jsonl, read, save, sha, verify_packet
from runner import prepare, run, verify_freeze


def snapshot_parents(protocol):
    verifier = ROOT / protocol['verifier']
    audit = read(verifier / 'preservation_audit.json')
    hashes = {**audit['parent_artifact_sha256'], **audit['source_sha256']}
    hashes.update({(Path(protocol['verifier']) / name).as_posix(): value
                   for name, value in read(verifier / 'artifact_checksums.json').items()})
    hashes[(Path(protocol['verifier']) / 'artifact_checksums.json').as_posix()] = sha(verifier / 'artifact_checksums.json')
    for folder in ['dataset/processed/item10/reviewed_v1.0.0', 'dataset/processed/item10/ai_reviewed_eval_v1.0.0']:
        manifest = read(ROOT / folder / 'dataset_manifest.json')
        hashes.update({(Path(folder) / name).as_posix(): value for name, value in manifest['files_sha256'].items()})
        hashes[(Path(folder) / 'dataset_manifest.json').as_posix()] = sha(ROOT / folder / 'dataset_manifest.json')
    manifest = read(ROOT / 'dataset/processed/item10/reviewed_v1.0.0/dataset_manifest.json')
    hashes.update({('outputs/item10-review-cleaned/' + name): value for name, value in manifest['cleaned_workbooks_sha256'].items()})
    if protocol.get('parent_evaluation'):
        parent = ROOT / protocol['parent_evaluation']
        verify_packet(parent)
        hashes.update({p.relative_to(ROOT).as_posix(): sha(p) for p in parent.rglob('*') if p.is_file()})
    return hashes


def figures(output, metrics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    matrix = metrics['overall']['primary']['confusion_matrix']
    fig, ax = plt.subplots(figsize=(6, 4.8))
    data = np.asarray(matrix['true_rows_predicted_columns'])
    ax.imshow(data, cmap='Blues', vmin=0)
    labels = [x.replace('_', ' ') for x in matrix['labels']]
    ax.set(xticks=range(len(labels)), yticks=range(len(labels)), xticklabels=labels, yticklabels=labels,
           xlabel='Predicted label', ylabel='Expected label', title='Development classification (labeled cases)')
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(data[i, j]), ha='center', va='center', color='white' if data[i, j] > data.max() / 2 else '#162b46')
    fig.tight_layout(); fig.savefig(output / 'classification_confusion.png', dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 4.6))
    ax.plot([0, 1], [0, 1], '--', color='#777777', label='Perfect calibration')
    for name, color in [('primary', '#235a95'), ('scope', '#a04a18')]:
        points = [b for b in metrics['overall'][name]['calibration']['bins'] if b['count']]
        ax.plot([b['mean_confidence'] for b in points], [b['observed_accuracy'] for b in points], 'o-', color=color, label=name)
    ax.set(xlim=(0, 1.02), ylim=(0, 1.02), xlabel='Mean predicted-label probability', ylabel='Observed label accuracy',
           title='Development label calibration (not legal confidence)')
    ax.legend(loc='lower right'); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(output / 'label_calibration.png', dpi=180); plt.close(fig)


def format_rate(value):
    if value is None: return 'Unavailable'
    return f'{value:.1%}'


def report(output, results, metrics, tests, preservation):
    protocol = read(output / 'protocol.json')
    overall = metrics['overall']
    suite_lines = []
    for name, values in metrics['strata']['suite'].items():
        suite_lines.append(f"| {name} | {values['cases']} | {values['primary']['count']} | {format_rate(values['primary']['accuracy'])} | {format_rate(values['scope']['accuracy'])} | {format_rate(values['decisive_coverage']['value'])} |")
    gate_lines = '\n'.join(f"| {g['metric']} | {format_rate(g['value'])} | {g['direction']} {format_rate(g['target'])} | {'Pass' if g['passed'] else 'Miss'} |" for g in metrics['screening_gates'])
    failed = [r for r in results if r['assessment']['issues']]
    issue_lines = '\n'.join(f"- `{r['case_id']}`: {', '.join(r['assessment']['issues'])}." for r in failed[:20]) or 'No per-case mismatches were recorded.'
    interval = overall['primary_accuracy']['family_cluster_bootstrap_95']
    interval_text = f'{interval[0]:.1%}–{interval[1]:.1%}' if interval else 'unavailable'
    text = f'''# Item 13 — offline system evaluation

The offline evaluator is implemented and executed on **291 AI-authored development cases**, with **{tests['tests_run']} software tests passing**. This implements the offline phase of Item 13. Formal independent acceptance and actual generated-answer evaluation remain pending.

The run freezes protocol, cases, grouping and code/source hashes before inference. The actual `{protocol['classifier']}`, `{protocol['retrieval']}` and `{protocol['verifier']}` receive only question text; expected labels/domains/provision IDs are used afterward for scoring. No LLM calls, new model fitting, source promotion or deployment occurred.

## Data and results

The same 200 general/typing questions, 67 retrieval cases and 24 AI-authored system questions across eight three-variant families were used. A repair revision reuses the parent case bytes and screening targets unchanged. They cover supported/partially supported mixed concerns, exclusions, missing facts and corpus gaps. All material remains development; zero independent human questions were created.

| Suite | Cases | Labeled cases | Primary accuracy | Scope accuracy | Decisive coverage |
|---|---:|---:|---:|---:|---:|
{chr(10).join(suite_lines)}

Overall primary accuracy is **{format_rate(overall['primary']['accuracy'])}** and scope accuracy **{format_rate(overall['scope']['accuracy'])}** on **{overall['primary']['count']} labeled cases**. Labels are evaluated even when routing defers. There are {sum(r['expected']['expected_primary'] is None for r in results)} separate clarification cases. Primary macro F1 is {overall['primary']['macro_f1']:.3f}; scope macro F1 is {overall['scope']['macro_f1']:.3f}. The error log records **{len(failed)} cases with at least one expectation mismatch**; this count includes routing, domain coverage and explicit concern/evidence mismatches, not just classification errors.

Known-relevant retrieval Hit@5 is **{format_rate(overall['known_relevant_hit_at_5']['value'])}** on {int(overall['known_relevant_hit_at_5']['denominator'])} judged cases; MRR@5 is {overall['known_relevant_mrr_at_5']['value']:.3f}. General/typing provision relevance is unjudged, so those rows do not enter retrieval accuracy denominators. The existing source judgments are partial; unlisted hits may also be relevant. Results reset rank per supported component and count each found provision once for known-relevant recall.

Exact source-quotation integrity is {format_rate(overall['quote_integrity']['value'])} on {int(overall['quote_integrity']['denominator'])} diagnostic claims. Excerpts select the first retrieved candidate without relevance labels. This validates text/citation provenance; it does not certify that the chosen excerpt answers the question or applies today.

## Screening and errors

| Development screen | Observed | Target | Result |
|---|---:|---:|---|
{gate_lines}

Classifier screens retain the existing owner-authorized numerical policy. Additional retrieval/system screens are AI-proposed development criteria, not formal adviser acceptance. Missed screens and cases are retained; no thresholds, model weights or frozen expected labels were changed to improve this run's numbers.

{issue_lines}

Full details are in `error_log.jsonl` and `results.csv`. Per-question predictions retain label probabilities, component queries, ranking/citation IDs, exact-source previews and verification/blocking reasons.

## Confidence and uncertainty

Primary label ECE is {overall['primary']['calibration']['ece']:.3f}; scope ECE is {overall['scope']['calibration']['ece']:.3f}. Multiclass Brier scores and negative log likelihood, reliability bins and confusion matrices are in `metrics.json`. Calibration is measured on labels, not legal correctness. It was not refitted here.

The descriptive family-cluster bootstrap 95% interval for primary accuracy is {interval_text}, using 2,000 replicates and a fixed seed. Related variants stay together. The source suites and strata are reported separately because they have different class/scenario composition. These reused AI cases do not support a fresh independent accuracy claim. At 100%/0% observed outcomes the bootstrap can collapse to one value; this cannot rule out unseen failures. The intervals do not measure AI-generator bias or prove semantic independence between source suites.

## Actual answers and final acceptance

Current-guidance candidate coverage is **{format_rate(overall['current_guidance_candidate_coverage']['value'])}**. The real source/claim review store is empty, so current guidance remains blocked. This is a documented operational limitation. An all-declining system is not assigned perfect legal accuracy.

No actual LLM-generated answers or real licensed reviews were supplied. Legal-answer accuracy, unsupported-claim rate and false declines on verified-current answerable questions are **unavailable**, not zero. Supported routing deferral ({format_rate(overall['supported_routing_deferral']['value'])}) is a separate diagnostic and is not a legally adjudicated false-decline rate.

The offline `answer_evaluation.py` scorer and published schemas are ready for future externally supplied drafts and separate operator legal reviews. Exact answer/question/protocol bindings and complete claim review are required. Normal scoring rejects software fixtures. Raw draft scores cannot override Item 12 source/display gates, and reviewer credentials require external authentication.

Fresh independent human questions/labels, currentness/source-coverage work, licensed Philippine legal review of selected generated answers and formal acceptance remain pending. The existing independent-intake form still contains zero authored questions and is correctly rejected. This version executes development only; it cannot relabel these cases as a final holdout.

## Reproducibility and preservation

{len(preservation['sha256'])} parent/source/data bindings were checked; {len(preservation['changed_files'])} changed. Original legal data, five cleaned review workbooks, the frozen reviewed seed, AI source datasets and evaluated model/retrieval/verifier packets are preserved. The new source cases, predictions and reviews contain no fabricated human authorship or approval.

Commands: [pipeline README](C:/IA/dataset/pipelines/item13/README.md). Key files: `protocol_freeze.json`, `case_manifest.json`, `split_membership.json`, `predictions.jsonl`, `metrics.json`, `results.csv`, `error_log.jsonl`, `software_tests.json`, `preservation_audit.json`, `readiness.json`, and `schemas/`.

![Classification confusion](classification_confusion.png)

![Label calibration](label_calibration.png)
'''
    (output / 'EVALUATION_REPORT.md').write_text(text, encoding='utf-8')


def build(output):
    protocol = read(HERE / 'protocol.json')
    verify_packet(ROOT / protocol['verifier'], runtime=True)
    parents = snapshot_parents(protocol)
    for path, expected in parents.items():
        if sha(ROOT / path) != expected: raise ValueError('Parent/source binding changed before run: ' + path)
    from test_evaluation import EvaluationTests
    stream = io.StringIO()
    checked = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EvaluationTests))
    if not checked.wasSuccessful():
        print(stream.getvalue()); raise ValueError('Evaluation software tests failed')
    output = prepare(output, protocol)
    (output / 'software_tests.log').write_text(stream.getvalue(), encoding='utf-8')
    tests = {'tests_run': checked.testsRun, 'failures': len(checked.failures), 'errors': len(checked.errors),
             'passed': checked.wasSuccessful(), 'independent_legal_validation': False}
    save(output / 'software_tests.json', tests)
    results, metrics = run(output)
    from answer_evaluation import ANSWER_SCHEMA, ANSWER_REVIEW_SCHEMA, evaluate_answers
    from check_independent_intake import check
    cases = [r['expected'] for r in results]
    save(output / 'answer_metrics.json', evaluate_answers(cases, [], [], sha(output / 'protocol.json'), as_of=protocol['as_of']))
    save(output / 'independent_intake_status.json', check(ROOT / 'outputs/pre-item12-repair-2026-10-17/human_gold_intake.jsonl'))
    changed = [path for path, expected in parents.items() if sha(ROOT / path) != expected]
    preservation = {'passed': not changed, 'changed_files': changed, 'sha256': parents}
    save(output / 'preservation_audit.json', preservation)
    if changed: raise ValueError('Preservation check failed')
    figures(output, metrics)
    report(output, results, metrics, tests, preservation)
    schemas = output / 'schemas'; schemas.mkdir()
    for name, schema in [('case', CASE_SCHEMA), ('answer', ANSWER_SCHEMA), ('answer_review', ANSWER_REVIEW_SCHEMA)]:
        save(schemas / (name + '.schema.json'), schema)
    snapshot = output / 'source_snapshot'; snapshot.mkdir()
    for path in HERE.iterdir():
        if path.is_file(): shutil.copyfile(path, snapshot / path.name)
    gates_met = all(g['passed'] for g in metrics['screening_gates'])
    save(output / 'readiness.json', {'offline_evaluation_implementation_completed': True,
        'development_run_completed': True, 'all_development_screens_met': gates_met,
        'failed_development_screens': [g['metric'] for g in metrics['screening_gates'] if not g['passed']],
        'actual_generated_answer_evaluation_completed': False, 'independent_final_evaluation_completed': False,
        'licensed_legal_review_completed': False, 'formal_item13_acceptance_completed': False,
        'all_project_issues_closed': False, 'answer_generation_allowed': False, 'deployment_allowed': False})
    save(output / 'dataset_inventory_addendum.json', {'new_ai_development_questions': 0 if protocol.get('parent_evaluation') else 24,
        'new_system_scenario_families': 0 if protocol.get('parent_evaluation') else 8,
        'reused_system_questions': 24 if protocol.get('parent_evaluation') else 0, 'reused_general_and_typing_questions': 200,
        'reused_retrieval_queries': 67, 'total_evaluation_cases': 291,
        'new_training_examples': 0, 'new_independent_human_questions': 0, 'new_legal_authorities': 0})
    verify_freeze(output)
    save(output / 'run_manifest.json', {'version': protocol['version'], 'as_of': protocol['as_of'],
        'status': 'offline_development_evaluation_completed', 'owner_authorization': 'Item 13 build and focused repair authorized by project owner',
        'parent_evaluation': protocol.get('parent_evaluation'),
        'python': platform.python_version(), 'protocol_freeze_sha256': sha(output / 'protocol_freeze.json'),
        'classifier': protocol['classifier'], 'retrieval': protocol['retrieval'], 'verifier': protocol['verifier'],
        'source_sha256': read(output / 'case_manifest.json')['source_sha256'],
        'runtime_source_sha256': read(output / 'protocol_freeze.json')['runtime_source_sha256'],
        'case_count': len(results), 'tests': tests, 'screening_gates_passed': gates_met,
        'live_llm_calls': 0, 'new_model_fitting': False, 'independent_human_evaluation': False,
        'formal_item13_acceptance_completed': False, 'deployment_allowed': False, 'answer_generation_allowed': False})
    save(output / 'artifact_checksums.json', {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob('*')) if p.is_file()})
    print(__import__('json').dumps({'version': protocol['version'], 'cases': len(results), 'tests': tests,
        'primary_accuracy': metrics['overall']['primary']['accuracy'], 'scope_accuracy': metrics['overall']['scope']['accuracy'],
        'cases_with_findings': metrics['cases_with_any_issue'], 'all_development_screens_met': gates_met}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve())
