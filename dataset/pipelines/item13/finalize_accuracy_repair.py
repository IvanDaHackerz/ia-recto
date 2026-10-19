"""Compare the frozen development rerun, preserve parents, then advance pointers."""
from __future__ import annotations
import difflib
from pathlib import Path
import sys

from evaluation_common import ROOT, read, rows, save, sha, verify_packet

PACKET = ROOT / 'outputs/item13-accuracy-repair-v1.0.0'
BEFORE = ROOT / 'outputs/item13-evaluation-v1.0.0'
AFTER = ROOT / 'outputs/item13-evaluation-v1.0.1'
VERSIONS = {'classifier': 'outputs/item10-classifier-v1.5.5',
    'retrieval': 'outputs/item11-retrieval-v1.2.4', 'verifier': 'outputs/item12-verifier-v1.0.2',
    'system_evaluation': 'outputs/item13-evaluation-v1.0.1'}


def preserve():
    freeze = read(PACKET / 'repair_freeze.json')
    groups = ['parent_sha256', 'immutable_data_and_prior_artifacts_sha256']
    changed = [name for group in groups for name, expected in freeze[group].items() if sha(ROOT / name) != expected]
    audit = {'passed': not changed, 'changed_files': sorted(set(changed)),
        'parent_bindings_checked': len(freeze[groups[0]]), 'data_and_prior_bindings_checked': len(freeze[groups[1]])}
    save(PACKET / 'preservation_audit.json', audit)
    if changed:
        raise ValueError('Frozen parent/data changed: ' + str(changed))
    return audit


def count(value):
    return f"{int(value['numerator'])}/{int(value['denominator'])}"


def documents(metrics, summary):
    # Only current narrative documents change; frozen source/artifact documents do not.
    overall = metrics['overall']
    path = ROOT / 'README.md'
    text = path.read_text(encoding='utf-8')
    text = text.replace('classifier v1.5.4', 'classifier v1.5.5').replace('retrieval v1.2.3', 'retrieval v1.2.4')
    text = text.replace('current v1.2.3 index', 'current v1.2.4 index')
    text = text.replace('outputs/item12-verifier-v1.0.1/', 'outputs/item12-verifier-v1.0.2/')
    text = text.replace('outputs/item13-evaluation-v1.0.0/', 'outputs/item13-evaluation-v1.0.1/')
    text = text.replace('offline (v1.0.1)', 'offline (v1.0.2)')
    text = text.replace('Forty-nine classifier tests, 38 retrieval tests, 8 supporting tests and 59 frozen-data checks pass.',
        'The focused repair passes 53 classifier tests and 42 retrieval tests; prior supporting and frozen-data audit results remain preserved.')
    text = text.replace('**49 classifier and 38 retrieval tests**', '**53 classifier and 42 retrieval tests**')
    text = text.replace('gates and 49 software tests', 'gates and 53 software tests')
    text = text.replace('Eleven negative controls and 38 software tests passed.', 'Eleven negative controls and 42 software tests passed.')
    start = text.index("**Item 13's offline evaluator")
    end = text.index('\n\n', start)
    new = (f"**Item 13's focused development repair is complete (v1.0.1).** All {summary['tests']['evaluator']} evaluator tests and "
        f"all {len(metrics['screening_gates'])} development screens pass. On the same frozen 291 AI cases, primary/scope "
        f"classification are each **{count(overall['primary_accuracy'])}**, explicit concern/evidence checks are "
        f"**{count(overall['explicit_concern_match'])}**, known-relevant retrieval is **{count(overall['known_relevant_hit_at_5'])}**, "
        f"and quotation integrity is **{count(overall['quote_integrity'])}**. The eight targeted cases are fixed; "
        f"{metrics['cases_with_any_issue']} existing conservative routing deferrals remain. Current guidance is blocked and "
        "actual generated-answer accuracy is unmeasured. [Repair comparison](C:/IA/outputs/item13-accuracy-repair-v1.0.0/REPAIR_REPORT.md). "
        "These are inspected development results; independent/legal acceptance remains pending.")
    text = text[:start] + new + text[end:]
    start = text.index('The 291 cases reuse')
    end = text.index('\n\n', start)
    text = text[:start] + (
        'The repair reruns the exact frozen 291 cases and unchanged screening targets: 200 general/typing questions, '
        '67 retrieval queries and 24 AI-authored system questions across eight families. Classification is 268/268 per head; '
        'explicit concern/evidence checks improve from 31/39 to 39/39. All 11 development screens pass. '
        'Eleven existing cases retain conservative routing deferrals. Thresholds, model weights, calibration and expected labels are unchanged. '
        'All material remains inspected AI development evidence; no independent human questions were added.') + text[end:]
    start = text.index('Review and repair the [Item 13 findings]')
    end = text.index('\n\n', start)
    text = text[:start] + (
        'The targeted Item 13 software repair is complete. Review the '
        '[comparison and remaining limits](C:/IA/outputs/item13-accuracy-repair-v1.0.0/REPAIR_REPORT.md). '
        'Actual generated-answer evaluation needs a controlled LLM drafter and resolved source/support-review prerequisites. '
        'Independent human questions, licensed legal review and formal approval remain pending. '
        'Live answering, deployment and Item 14 integration have not been enabled. The prior baseline, legal sources and frozen seed remain preserved.') + text[end:]
    path.write_text(text, encoding='utf-8')
    path = ROOT / 'dataset/DATASET_INVENTORY.md'
    text = path.read_text(encoding='utf-8').replace('v1.5.4', 'v1.5.5').replace('v1.2.3', 'v1.2.4')
    text = text.replace('49 software tests', '53 software tests').replace('38 retrieval tests', '42 retrieval tests')
    text = text.replace('Current audited version v1.0.1', 'Current artifact-binding version v1.0.2')
    text = text.replace('Its 31 software tests pass.', 'The repaired evaluator passes 34 software tests and all 11 unchanged development screens. The same 291 case bytes are reused; no questions are added by the repair.')
    text = text.replace('Classification 267/268 per head; explicit concern/evidence checks 31/39 miss the proposed screen.',
        'Repaired classification 268/268 per head; explicit concern/evidence checks 39/39 pass the unchanged screen. Eleven conservative routing deferrals remain.')
    for item, old, new in [(11, 'v1.1.2', 'v1.2.4'), (12, 'v1.0.1', 'v1.0.2'), (13, 'v1.0.0', 'v1.0.1')]:
        prefix = {11: 'retrieval', 12: 'verifier', 13: 'evaluation'}[item]
        text = text.replace(f'outputs/item{item}-{prefix}-{old}/', f'outputs/item{item}-{prefix}-{new}/')
    text += ('\nFocused Item 13 repair: the classifier, retrieval, verifier and evaluation packages are new versions of existing artifacts. '
        'The repair adds software regression controls, not training questions or independent human gold. '
        '[Repair comparison and preservation](C:/IA/outputs/item13-accuracy-repair-v1.0.0/REPAIR_REPORT.md).\n')
    path.write_text(text, encoding='utf-8')


def finalize():
    if (PACKET / 'comparison.json').exists():
        raise ValueError('Repair already finalized; do not rewrite its evidence')
    audit = preserve()
    for path in VERSIONS.values():
        verify_packet(ROOT / path)
    verify_packet(ROOT / VERSIONS['verifier'], runtime=True)
    before, after = read(BEFORE / 'metrics.json'), read(AFTER / 'metrics.json')
    assert (BEFORE / 'cases.jsonl').read_bytes() == (AFTER / 'cases.jsonl').read_bytes()
    assert sha(AFTER / 'cases.jsonl') == read(PACKET / 'repair_freeze.json')['case_sha256']
    assert read(BEFORE / 'protocol.json')['screening_targets'] == read(AFTER / 'protocol.json')['screening_targets']
    old = {r['case_id']: r for r in rows(BEFORE / 'predictions.jsonl')}
    new = {r['case_id']: r for r in rows(AFTER / 'predictions.jsonl')}
    assert old.keys() == new.keys()
    fixed, new_findings, worsened = [], [], []
    for cid in old:
        b, a = old[cid]['assessment']['issues'], new[cid]['assessment']['issues']
        if b and not a: fixed.append(cid)
        if not b and a: new_findings.append(cid)
        if set(a) - set(b): worsened.append(cid)
    tests = {'classifier': read(ROOT / VERSIONS['classifier'] / 'software_tests.json')['tests_run'],
        'retrieval': read(ROOT / VERSIONS['retrieval'] / 'software_tests.json')['tests_run'],
        'verifier': read(ROOT / VERSIONS['verifier'] / 'software_tests.json')['item12']['tests_run'],
        'evaluator': read(AFTER / 'software_tests.json')['tests_run']}
    summary = {'role': 'Inspected AI development repair; no fresh independent performance claim',
        'before': BEFORE.relative_to(ROOT).as_posix(), 'after': AFTER.relative_to(ROOT).as_posix(),
        'case_sha256': sha(AFTER / 'cases.jsonl'), 'cases_unchanged': True, 'targets_unchanged': True,
        'fixed_case_ids': fixed, 'new_finding_case_ids': new_findings, 'worsened_case_ids': worsened,
        'remaining_case_ids': [cid for cid in new if new[cid]['assessment']['issues']],
        'tests': tests, 'all_development_screens_met': all(g['passed'] for g in after['screening_gates']),
        'metrics': {key: {'before': before['overall'][key], 'after': after['overall'][key]} for key in [
            'primary_accuracy', 'scope_accuracy', 'partial_support_recall', 'explicit_concern_match',
            'known_relevant_hit_at_5', 'known_relevant_mrr_at_5', 'quote_integrity',
            'negative_candidate_leakage', 'decisive_coverage', 'route_match', 'current_guidance_candidate_coverage']},
        'new_training_questions': 0, 'new_independent_human_questions': 0, 'live_llm_calls': 0,
        'deployment_allowed': False, 'answer_generation_allowed': False}
    if new_findings or worsened or not summary['all_development_screens_met']:
        save(PACKET / 'failed_comparison.json', summary)
        raise ValueError('New findings or failed screens; current pointers unchanged')
    # Validate persisted learned state, not just the object before serialization.
    sys.path.insert(0, str(ROOT / 'dataset/pipelines/item10'))
    import joblib
    b = joblib.load(ROOT / 'outputs/item10-classifier-v1.5.4/classifier.joblib')
    a = joblib.load(ROOT / VERSIONS['classifier'] / 'classifier.joblib')
    eb, ea = b['primary_model'].engine, a['primary_model'].engine
    assert joblib.hash(eb.atomic.model) == joblib.hash(ea.atomic.model)
    assert joblib.hash(eb.atomic.lexical) == joblib.hash(ea.atomic.lexical)
    assert joblib.hash(eb.joint_model) == joblib.hash(ea.joint_model)
    assert b['thresholds'] == a['thresholds']
    summary['weights_features_calibration_thresholds_unchanged'] = True
    save(PACKET / 'comparison.json', summary)
    diffs = []
    for name, live in [('scope_constraints.py', 'dataset/pipelines/item10/scope_constraints.py'),
                       ('retrieval.py', 'dataset/pipelines/item11/retrieval.py')]:
        diffs.extend(difflib.unified_diff((PACKET / ('before_' + name)).read_text(encoding='utf-8').splitlines(True),
            (ROOT / live).read_text(encoding='utf-8').splitlines(True), fromfile='parent/' + name, tofile=live))
    (PACKET / 'runtime_changes.patch').write_text(''.join(diffs), encoding='utf-8')
    table = '\n'.join(f"| {key.replace('_', ' ')} | {count(value['before'])} | {count(value['after'])} |"
        for key, value in summary['metrics'].items() if key != 'known_relevant_mrr_at_5')
    report = f'''# Item 13 focused accuracy repair

The seven wage/overtime retrieval misses and one Taglish privacy-scope miss are fixed on the **same frozen 291 AI development cases**. All **{len(after['screening_gates'])} unchanged development screens pass**. No new per-case findings were introduced.

| Check | Before | After |
|---|---:|---:|
{table}

Cases with any finding decreased from **{before['cases_with_any_issue']} to {after['cases_with_any_issue']}**. The remaining cases are the same conservative routing deferrals; confidence thresholds were not lowered. Relevant-provision ranking on the 56 existing judged system retrieval cases remains MRR@5 {after['overall']['known_relevant_mrr_at_5']['value']:.3f}. Quotation counts can change when an excluded concern stops reaching retrieval; the check measures provenance, not relevance or legal correctness.

## Changes and controls

The classifier now recognizes bounded Taglish disclosure verbs plus private-data objects and public/unauthorized context. Separate warranty concerns remain supported; private-data disclosure remains excluded. Tests cover negated disclosure, ordinary delivery addresses and reversed concern order.

Labor-only lexical expansion associates late wages with payment timing/frequency and unpaid overtime with additional compensation. Original query words and special overtime qualifiers remain. Expansion terms are ranking aids, never supplied facts, legal support or approval. No expected IDs or evaluation labels enter runtime.

Software tests pass: **{tests['classifier']} classifier, {tests['retrieval']} retrieval, {tests['verifier']} verifier and {tests['evaluator']} evaluator tests**. The verifier also passes its unchanged **50/50 AI development scenarios**. The opened original classifier regression remains **100/100**, with **92%** decisive coverage and **11/11** partial-support recall. These are inspected regression results.

All 291 case bytes and expected labels, source memberships, numerical screening targets, fitted weights, feature vocabulary, calibration and confidence thresholds are unchanged. The new index contains the same 362 chunks / 353 provisions / 12 documents and identical semantic vectors. No training data or legal authority was added. No LLM calls occurred.

## Preservation and versions

{audit['parent_bindings_checked']} old-parent file bindings and {audit['data_and_prior_bindings_checked']} data/prior-artifact bindings match the pre-repair snapshot. Prior evaluated versions remain available. Current development packages are classifier v1.5.5, retrieval v1.2.4, verifier v1.0.2 and evaluation v1.0.1. `comparison.json` contains complete before/after rates, uncertainty intervals, fixed/remaining IDs and regression checks; `runtime_changes.patch` records the two behavior changes.

## Remaining work

Eleven conservative routing deferrals remain; passing aggregate development screens does not mean every expected route matches. The final-pay/COE evidence gap and prior source/currentness/contact prerequisites remain. The real review store still has zero current-guidance approvals, so current guidance remains blocked.

These reused AI cases provide development evidence, not independent human gold or real-world legal accuracy. Fresh independent human questions, source/support review, licensed Philippine legal review of selected actual generated answers and formal acceptance remain pending. Actual generated-answer accuracy and legal false-decline rates are unmeasured. The next development work is a controlled LLM draft adapter and its offline answer evaluation after required source/support conditions are resolved; Item 14 UI integration has not started. Live answering and deployment remain disabled.
'''
    (PACKET / 'REPAIR_REPORT.md').write_text(report, encoding='utf-8')
    save(PACKET / 'dataset_inventory_addendum.json', {'new_training_questions': 0, 'new_independent_human_questions': 0,
        'new_legal_authorities': 0, 'new_system_cases': 0, 'reused_frozen_system_cases': 291,
        'new_classifier_regression_methods': 4, 'new_retrieval_regression_methods': 4, 'new_evaluator_freeze_tests': 3})
    documents(after, summary)
    preserve()
    current = read(ROOT / 'CURRENT_ARTIFACTS.json')
    current.update(VERSIONS)
    current.update(accuracy_repair=PACKET.relative_to(ROOT).as_posix(),
        item13_status='offline_development_repair_completed_with_conservative_deferrals',
        item13_all_development_screens_met=True, item13_failed_development_screens=[],
        item13_formal_acceptance_completed=False, all_project_issues_closed=False,
        answer_generation_allowed=False, deployment_allowed=False, current_guidance_allowed=False)
    save(ROOT / 'CURRENT_ARTIFACTS.json', current)
    save(PACKET / 'current_artifacts_after.json', current)
    save(PACKET / 'artifact_checksums.json', {p.relative_to(PACKET).as_posix(): sha(p)
        for p in sorted(PACKET.rglob('*')) if p.is_file()})
    print(__import__('json').dumps({'fixed_cases': fixed, 'remaining_cases': len(summary['remaining_case_ids']),
        'all_screens_met': True, 'tests': tests, 'old_files_changed': 0}, indent=2))


if __name__ == '__main__':
    finalize()
