"""Finish the disclosed development regression report without provider calls."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(ROOT))
from backend.terminal_test import load_runtime
from backend.application.development_explanation import checked_claims
from backend.application.source_issues import issue_for
from dataset.pipelines.item11.query_relevance import source_relevance


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def observations(name):
    return [json.loads(line) for line in (BASE / name / 'observations.jsonl').read_text(encoding='utf-8').splitlines()]


def ledger_totals(path):
    db = sqlite3.connect(f'file:{path.resolve().as_posix()}?mode=ro', uri=True)
    rows = db.execute('SELECT day,count(*),sum(estimate),sum(input_tokens),sum(output_tokens) FROM calls GROUP BY day').fetchall()
    db.close()
    return [{'day_utc': d, 'requests_including_reservations': n, 'estimated_usd': round(cost, 9),
             'input_tokens': it, 'output_tokens': ot} for d, n, cost, it, ot in rows]


cases = read(BASE / 'cases.json')
verifier = load_runtime()
latest = {}
for phase in ['final-replay', 'targeted-final', 'project-definition-final']:
    for observation in observations(phase):
        latest[observation['case']['case_id']] = (phase, observation)
gaps = {f'AI100_{n:03d}' for n in [*range(6, 11), *range(26, 31), *range(41, 46), 94]}
reading_flags = {
    'AI100_038': 'Dismissal notice summary needs closer checking for omitted procedural steps.',
    'AI100_048': 'Venue, filing, and mediation roles need closer separation.',
    'AI100_056': 'Remedy timing is incompletely qualified; a second safety paragraph drifts from the quality issue.',
    'AI100_079': 'Two components produce repetitive safety discussion; the defense qualification needs closer checking.',
    'AI100_085': 'Opening remedy statement can imply availability before the later correction-period condition.',
    'AI100_089': 'Complaint logging and procedure detail need source-level scrutiny beyond citation identity.',
}
rows = []
for case in cases:
    cid = case['case_id']
    phase, observation = latest[cid]
    packet = observation['normalized']['packet']
    explanation = packet['explanation']
    assessment = observation['normalized']['assessment']
    row = {'case_id': cid, 'last_observation_phase': phase, 'source_gap_audit': cid in gaps,
           'last_live_status': explanation['status'], 'last_live_reason': explanation['reason'],
           'label_and_route_matches': {k: assessment[k] for k in ['primary_correct', 'scope_correct', 'route_correct', 'domain_correct']},
           'independent_legal_review': False}
    if explanation['status'] == 'generated':
        components = []
        for component in packet['result']['components']:
            gates = {g['chunk_id']: g for g in component['evidence_gates']}
            eligible = [h for h in component['candidates'] if h['chunk_id'] in gates
                        and not (set(gates[h['chunk_id']]['reasons']) - {'scoped_currentness_review_missing'})
                        and not verifier.check_candidate(h, component['allowed_domain'])
                        and not issue_for(h)
                        and source_relevance(component['query'], component['allowed_domain'], h) > 0]
            components.append({'component_id': component['component_id'], 'query': component['query'], 'sources': eligible[:3]})
        draft = {'paragraphs': [{'component_id': c['component_id'], 'text': c['text'],
                                'evidence': [{'chunk_id': v['chunk_id'], 'quote': v['quote']} for v in c['citations']]}
                               for c in explanation['claims']]}
        try:
            checked_claims(draft, components)
            row['current_local_checks_pass'] = True
        except (ValueError, TypeError, KeyError) as error:
            row.update(current_local_checks_pass=False, current_local_failure=str(error))
    if cid in reading_flags:
        row['AI_engineering_reading_flag'] = reading_flags[cid]
    rows.append(row)

checkpoint = {
    'method': 'Last observation per frozen question: final-replay, then targeted-final, then project-definition-final; never select the best response.',
    'role': 'Posthoc cached/live development regression checkpoint; not a fresh full-100 provider run or independent acceptance test.',
    'unique_questions': len(rows), 'missing_observations': len(cases) - len(latest),
    'last_live_status_counts': dict(Counter(r['last_live_status'] for r in rows)),
    'last_live_withheld_reasons': dict(Counter(r['last_live_reason'] for r in rows if r['last_live_status'] != 'generated')),
    'current_local_generated_pass': sum(r.get('current_local_checks_pass') is True for r in rows),
    'current_local_generated_fail': sum(r.get('current_local_checks_pass') is False for r in rows),
    'label_and_route_matches': {k: sum(r['label_and_route_matches'][k] is True for r in rows) for k in rows[0]['label_and_route_matches']},
    'posthoc_source_gap_case_ids': sorted(gaps), 'AI_reading_flags_are_not_exhaustive_or_independent': True,
    'new_provider_calls': 0, 'legal_accuracy': None, 'cases': rows,
}
save(BASE / 'completed-checkpoint.json', checkpoint)

phase_names = ['first-pass', 'post-repair', 'post-repair-final', 'repaired-confirmation', 'final-replay', 'targeted-final', 'project-definition-final']
phases = {}
for name in phase_names:
    metrics = read(BASE / name / 'metrics.json')
    phases[name] = {k: metrics.get(k) for k in ['input_forms', 'pending', 'successful_packets', 'explanation_status',
                   'non_generated_reasons', 'failure_codes', 'validation_failures', 'latency_ms', 'usage']}
    routing = metrics['routing_and_retrieval']
    phases[name]['matches'] = {'primary': routing['primary']['accuracy'], 'scope': routing['scope']['accuracy'],
                              'route': routing['route_match'], 'domain': routing['domain_match']}
local = read(ROOT / 'outputs/local-pipeline-evaluation-v1.6.15/metrics.json')
baseline = local['strata']['all']['baseline']
test_log = (BASE / 'backend-completed-tests.log').read_text(encoding='utf-8', errors='replace')
software_pass = 'Ran 238 tests' in test_log and '\nOK\n' in test_log
summary = {
    'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'dataset': read(BASE / 'case-manifest.json'),
    'artifacts': read(ROOT / 'CURRENT_ARTIFACTS.json'), 'phases': phases,
    'checkpoint': {k: v for k, v in checkpoint.items() if k != 'cases'},
    'preservation': read(BASE / 'preservation-final.json'), 'classifier_recheck': read(BASE / 'classifier-v44-recheck.json'),
    'previous_436_AI_off_regression': {
        'inputs': local['counts']['input_forms'], 'primary': baseline['primary']['accuracy'], 'scope': baseline['scope']['accuracy'],
        'primary_macro_f1': baseline['primary']['macro_f1'], 'scope_macro_f1': baseline['scope']['macro_f1'],
        'route': baseline['route_match'], 'hit_at_5': baseline['known_relevant_hit_at_5'],
        'unsupported_admission': baseline['unsupported_admission'], 'evidence_checks': local['evidence_checks']},
    'software_tests': {'backend_count': 238, 'backend_passed': software_pass,
                       'classifier_build_tests': 69, 'retrieval_build_tests': 50, 'verifier_build_tests': 37,
                       'note': 'Software tests and AI response accuracy are separate.'},
    'runtime_health': read(BASE / 'runtime-health-completed.json'),
    'batch_cost_ledger_all_days': ledger_totals(BASE / 'live-budget.sqlite3'),
    'website_ledger_all_days_includes_earlier_work_not_task_cost': ledger_totals(ROOT / '.local/website/usage.sqlite3'),
    'legal_accuracy_measured': False, 'independent_human_reviews': 0, 'formal_acceptance_completed': False,
    'remaining_issues': [
        'Same-model support judgments still accept incomplete or misattached conditions; engineered guards are not an entailment proof.',
        'Some long or joined questions still produce repetitive components or adjacent-topic discussion.',
        'Sixteen questions have a genuine source-coverage/held-authority gap; topic confidence cannot repair that gap.',
        'AI responses can remain withheld after one bounded correction; the last project-contract recheck was withheld.',
        'Latency remains variable, with roughly 11.5-second median and 20.5-second p95 on the 26 targeted checks.',
        'No independent human-written/legally reviewed acceptance evaluation or current-law approval is claimed.',
    ],
}
if (BASE / 'browser-completed-check.json').exists():
    summary['final_browser_check'] = read(BASE / 'browser-completed-check.json')
save(BASE / 'summary.json', summary)

report = f'''# AI-on usability repair and development regression report

The classifier and retrieval routing improved on the inspected development questions. The AI explanation stage is still uneven. This report does not certify the system as completely usable or legally reliable.

## Questions and protocol

The frozen set contains **100 new fictional AI-authored questions**: 50 labor, 40 consumer, and 10 mixed labor/consumer. Expected labels were saved before inference. All 100 are within the project's topics; this batch cannot measure out-of-scope or partial-support recall. It contains no personal chat text and no independently human-written questions. The original question hash remains `{summary['dataset']['cases_sha256']}`.

Questions cover wages, hours, rest days, overtime, holiday pay, thirteenth-month pay, employment status, dismissal, final pay/COE, SEnA, consumer rights, defects, warranties, remedies, deceptive sales, advertising, prices, shortchanging, safety, services, online sales, complaints, and joined concerns. Repeated repair runs reuse these same 100 questions; they are not additional unique questions or a fresh holdout.

## Observed runs

| Run | Returned / intended | Generated | Withheld | Meaning |
| --- | ---: | ---: | ---: | --- |
| First pass | 100 / 100 | 56 | 44 | Original baseline |
| Repaired confirmation | 100 / 100 | 70 | 30 | Intermediate repaired stack |
| Latest broad replay | 98 / 100 | 70 | 28 | Stopped at conservative $0.50 bulk cost admission; 2 pending |
| Targeted final checks | 26 / 26 | 16 | 10 | Affected and pending questions; selection was posthoc |
| Final project-definition check | 1 / 1 | 0 | 1 | Still omitted a material condition; safely withheld |

The first-pass topic, topic-coverage, and route matches were **96/100, 97/100, and 95/100**. The selected classifier's later direct recheck matched all 100 frozen expectations; no learned weights, vocabulary, calibration, thresholds, or training membership were changed, and all 459 original training feature rows are preserved. These are development results after inspecting failures, not an estimate of population accuracy or proof against overfitting.

The last-observed checkpoint now has **100/100 recorded questions**, including the two previously pending cases, with **{checkpoint['last_live_status_counts'].get('generated', 0)} generated and {checkpoint['last_live_status_counts'].get('withheld', 0)} withheld**. Current local checks accept {checkpoint['current_local_generated_pass']} of those captured generated results and flag {checkpoint['current_local_generated_fail']}. This checkpoint combines cached broad-run observations and fresh targeted observations, always retaining the latest result, including failures. It is **not a fresh final 100-question AI pass**, and generated does not mean correct. Per-case source phase, local validation, and remaining AI-reading concerns are in `completed-checkpoint.json`.

The smoke run and deliberately interrupted 44-result run are retained in their original directories. No best-response selection or removal of failed/pending cases was used. Original first-pass and intermediate metrics remain unchanged.

## Repairs

- Improved English/Taglish scenario grouping, employment background handling, follow-up questions, consumer purchase recognition, and native dismissal wording. Independent concerns and excluded topics retain their own boundaries.
- Improved facet selection for wage timing, overtime, product quality, services, advertising, and online transactions. Removed specialized or unrelated authorities from ordinary questions, including substituting normal-hours text for the held counted-time authority.
- Expanded exact source quotation options so later warranty clauses can be selected. Sources remain tied to their own question component, with complete citation identities and exact spans.
- Added locally enforced output contracts and one bounded correction with actionable support feedback. The support critic now checks conditions, actor identity, implication direction, material exceptions, and personal case findings more closely.
- Added specific checks for observed condition-dropping and reversal errors in employment status, loss deductions, payment-by-results settlement, warranty roles, remedy periods, returns, and numerical claims. Typographic hyphens and procedural words no longer produce several false quantity mismatches.
- A final live browser check exposed a price-list exception incorrectly attached to the price ceiling. Added an explicit source-support instruction and regression-tested local rejection for that error. Earlier frozen provider runs predate this last guard; captured outputs are revalidated locally instead of being relabeled as new live approvals.

Canonical source records remain byte-identical to the earlier selected corpus. Source holds and current-applicability gates remain active. No withheld authority was promoted just to obtain an answer.

## Verification and timing

The final backend suite passed **238/238 tests**: `{software_pass}`. Selected builds passed classifier **69/69**, retrieval **50/50**, and verifier **37/37** software tests. The prior 436-question AI-off regression retained **425/425 labeled matches per head**, macro F1 **1.0 on this reused development set**, **432/436 route matches**, **93/93 known-relevant Hit@5**, and **0/80 unsupported admissions**. Its 1,605 candidate-integrity checks and 432 recorded-excerpt provenance checks had zero failures. Four historical route-policy differences remain disclosed.

The first 238-test attempt encountered a Windows connection-aborted error in the busy-server HTTP test. That failed log is preserved as `backend-price-repair-first-attempt.log`. One unchanged-code rerun passed all 238; this intermittent connection-test result is not hidden.

The latest broad replay had median **13.0 s**, p95 **29.6 s**, and maximum **36.3 s**. The 26 targeted checks had median **11.5 s**, p95 **20.5 s**, and maximum **22.3 s**. Some earlier provider calls timed out or hit the cost gate; none of the 26 targeted packets recorded a provider failure code. Additional corrections and source-support checking add latency; speed is not fully resolved.

Citation audits passed exact-span, source-identity, domain and hold checks for **211/211 citations** in the latest broad replay and **47/47** in the targeted run. These checks establish source integrity, not semantic entailment or current law. AI engineering reading still identified repetitive paragraphs, incomplete procedure summaries, and ambiguous timing/conditions among accepted results. The same-model critic is not an independent legal reviewer.

The final website check of the fictional Taglish price question generated an explanation in **10.028 s**, with **3 LLM calls and one correction**. The misplaced price-display exception was absent from that response. Topic confidence was **88.0%**, and topic-coverage confidence **94.0%**. AI remained on and device history saving remained off. This is one browser regression check, not a replacement full-set evaluation.

The dedicated batch ledger records **769 provider attempts/reservations**, approximately **$0.55138**, including replays, diagnostics and repair calls. It includes 2,302,817 input and 326,784 output tokens. The conservative original bulk cap was honored; targeted repairs used a separately frozen cumulative $0.59 ceiling. Costs are local estimates, not a verified provider invoice. The website ledger is reported separately, includes earlier work, and must not all be attributed to this test.

## Remaining work and release status

1. **Source coverage:** 16 source-gap cases remain: 006–010, 026–030, 041–045, and 094. Ten were known before inference; six were identified posthoc. Counted-time authority is held, and the current approved source context does not settle every thirteenth-month, final-pay, or COE question. All 100 remain in the reported denominator.
2. **Explanation reliability:** some outputs still omit or misattach conditions, blur procedural roles, or repeat adjacent issues despite a support pass. Specific AI-reading flags are retained; they are not an exhaustive semantic review. The project-definition final response was withheld rather than counted as a successful explanation.
3. **Unseen questions and human evaluation:** these repairs were informed by the test failures. Independent generalization, legal interpretation, and current applicability remain unmeasured. A question's label confidence is not its legal-answer accuracy.
4. **Latency and fallback quality:** generation plus source checking can take 10–30 seconds, and a safe source-only fallback remains necessary. Always displaying an unqualified generated legal conclusion would hide these failures.

Active stack: **classifier v1.5.44 / retrieval v1.3.33 / verifier v1.0.40**. The AI-off display metrics point to `outputs/local-pipeline-evaluation-v1.6.15`; historical AI evaluations remain separate. The running API's identity is checked against the final source. Development AI explanations are enabled; legal/currentness approval and deployment gates remain closed.

## Evidence

- `cases.json`, `case-manifest.json`: frozen input and authorship provenance.
- Each run's `protocol.json`, `freeze.json`, `source_snapshot`, `observations.jsonl`, `provider-completions.jsonl`, and `metrics.json`: original evidence and failure accounting.
- `completed-checkpoint.json`: latest observation per question and current local revalidation.
- `summary.json`: machine-readable results and separate cost ledgers.
- `backend-completed-tests.log`, selected build test logs, `preservation-final.json`: software and preservation checks.
- `runtime-health-completed.json`, `browser-completed-check.json`, and browser screenshot: final website connection and UI evidence.
- `completed-checksums.json`: hashes of the final report, key evidence, and changed production source.

This is a useful repaired development preview. It is not a completed independent legal-quality acceptance test.
'''
(BASE / 'REPORT.md').write_text(report, encoding='utf-8')
paths = [ROOT / 'CURRENT_ARTIFACTS.json', ROOT / 'backend/classifier/config.json',
         ROOT / 'backend/application/grounding.py', ROOT / 'backend/application/development_explanation.py',
         ROOT / 'dataset/pipelines/item10/clause_classifier.py', ROOT / 'dataset/pipelines/item10/scope_constraints.py',
         ROOT / 'dataset/pipelines/item10/classifier_runtime.py', ROOT / 'dataset/pipelines/item11/query_relevance.py',
         *[BASE / f for f in ['REPORT.md', 'summary.json', 'completed-checkpoint.json', 'cases.json', 'case-manifest.json',
                              'backend-completed-tests.log', 'runtime-health-completed.json', 'browser-completed-check.json',
                              'browser-completed.jpg', 'browser-price-before-final-guard.json',
                              'backend-price-repair-first-attempt.log', 'finish_report.py']]]
for phase in phase_names:
    paths.extend(BASE / phase / f for f in ['observations.jsonl', 'metrics.json', 'freeze.json'])
save(BASE / 'completed-checksums.json', {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
                                        for path in paths if path.exists()})
print(json.dumps({'unique_questions': len(rows), 'checkpoint': {k: checkpoint[k] for k in ['last_live_status_counts',
                  'current_local_generated_pass', 'current_local_generated_fail', 'label_and_route_matches']},
                  'backend_tests_passed': software_pass}))
