"""Publish observed counts and limitations, including unsuccessful earlier rounds."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
baseline=read('baseline.json');development=read('accepted-development.json');contrast=read('accepted-contrasts.json')
first=read('reserved-final.json');opened=read('opened-reserve-regression.json');second=read('second-reserve-results.json')
before=read('latency-before-final.json');after=read('latency-after-final.json');application=read('application-check.json')
current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text());history=json.loads((ROOT/current['local_pipeline_evaluation']/'metrics.json').read_text())
s=history['strata']['all']['baseline'];payloads=application['payload_measurements']
old_chars=sum(p['source_characters'] for p in payloads);new_chars=sum(p['compact_source_characters'] for p in payloads)
summary={'classifier':current['classifier'],'retrieval':current['retrieval'],'verifier':current['verifier'],
 'new_synthetic_forms':233,'taxonomy_fields':42,'independent_human_questions':0,'external_ai_calls':0,
 'development_before':{'route_matches':baseline['counts']['route_correct'],'total':baseline['total'],'label_matches':baseline['counts']['primary_correct'],'label_total':84},
 'development_after':{'route_matches':development['counts']['route_correct'],'total':development['total'],'label_matches':development['counts']['primary_correct'],'label_total':84},
 'contrast_development':{'passed':contrast['passed'],'total':contrast['total']},
 'first_reserved_before_further_repair':{'passed':first['all_passed'],'total':first['total'],'role_now':'opened development'},
 'opened_reserve_regression':{'passed':opened['all_passed'],'total':opened['total']},
 'second_unused_wording_check':{'passed':second['passed'],'total':second['total'],'used_for_tuning':False},
 'raw_latency':{'before':before,'after':after,'median_reduction_percent':100*(before['median_ms']-after['median_ms'])/before['median_ms']},
 'source_context':{'samples':len(payloads),'before_characters':old_chars,'after_characters':new_chars,
  'reduction_percent':100*(old_chars-new_chars)/old_chars,'all_complete_sources_retained':all(p['full_sources_preserved'] for p in payloads)},
 'historical_reused_inputs':436,'historical_topic_accuracy':s['primary']['accuracy'],'historical_scope_accuracy':s['scope']['accuracy'],
 'historical_route_match':s['route_match'],'historical_primary_macro_f1':s['primary']['macro_f1'],
 'historical_scope_macro_f1':s['scope']['macro_f1'],'historical_local_latency_ms':s['latency_ms'],
 'historical_route_mismatches':{'intended_policy_changes':4,'excluded_concern_clarification_deferrals':4},
 'remaining_limits':['No independent human gold or legal-answer correctness measurement.',
  'Four historical excluded-topic questions still clarify instead of referring immediately.',
  'The existing final-pay/COE authority gap remains; missing sources cannot supply a grounded explanation.',
  'No live LLM output or provider-latency evaluation in this repair.']}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
report=f'''# Scope flexibility and explanation repair — 20 October 2026

The main observed problems were routing and text segmentation, incomplete bilingual concepts, and background words overriding a real concern. The tests do not establish a statistical diagnosis of overfitting or underfitting. The selected model remains word/character TF–IDF plus logistic regression, composed into coherent domain/coverage decisions with declared scope constraints and grouped probability calibration. It is not an LLM classifier.

Active artifacts: **{Path(current['classifier']).name}**, **{Path(current['retrieval']).name}**, **{Path(current['verifier']).name}**. Original atomic coefficients, vocabulary, training membership and thresholds are unchanged. Only probability calibration was refitted on the original training folds, with shared atomic facts purged between folds. None of these diagnostic questions was fitted. A hybrid embedding candidate was compared on development data and performed worse; it was not selected. Historical source text, trusted approvals and deployment gates were preserved.

## What changed

- An understandable wage concern no longer needs its employment category before general sources can be searched. The application retains the original question and states that private-sector applicability is unconfirmed; it asks the category as a follow-up. Explicit government, overseas, domestic and seafarer concerns stay excluded.
- Added guarded Tagalog/English concepts for wages, work status, COE, ordinary purchases, defects and safety. Pay/notice or a generic service alone is not proof of a supported concern.
- Separates job introductions, temporal context and payment details from independent complaints. A hospital or insurer can be an employer. Explicit specialized worker categories take precedence over private company ownership; negated categories are not propagated.
- Preserves supported versus excluded predicates in joined concerns, including privacy. Distinguishes phone hardware from a service plan, an electricity-related product from utility billing, and general wage-setting context from exact changing rates.
- Ambiguous payment wording and uninterpretable text clarify. Added reverse-order child-custody and cooking-request exclusions after the first reserved diagnostic exposed false admissions.
- Both output heads now reuse the same joint inference and decision pass. Exact numerical equivalence to separate head inference is tested. No global query cache or cross-user reuse was added.
- Consumer search aliases can yield multiple same-domain predicates while retaining the original labels, scope and exclusion checks.
- The explanation prompt asks for a specific useful general rule, material qualifications and a relevant missing fact/next step only when sourced. Complete authorities remain in the prompt; long duplicate proof passages become previews with offsets. Local code restores exact proof, then all existing citation, quantity and support checks still run.
- Provider attempts expose elapsed milliseconds per stage without question/key contents. Clear specialized-scope questions with no observed corruption no longer trigger a paid vocabulary fallback merely because the wording dictionary is small. Corrupted wording still follows the existing conditional path.

## Scope-wide tests — external AI off

There are **233 distinct new synthetic forms**, covering **all 42 taxonomy fields** plus ambiguity, noise, mixed topics, negation and incidental context. They have no exact normalized matches to the original training/validation/test and earlier general/typing datasets. These are AI-authored diagnostics, **not independent human gold**. Cases, expectations, source snapshots and hashes are included in this folder.

| Set | Observed result | Role |
| --- | --- | --- |
| First 102 questions, before repair | {baseline['counts']['route_correct']}/102 routes; {baseline['counts']['primary_correct']}/84 explicit topic/coverage labels | Baseline |
| Same 102, after repair | {development['counts']['route_correct']}/102 routes; {development['counts']['primary_correct']}/84 topic/coverage labels | Inspected development |
| 51 contrastive questions | {contrast['passed']}/51 | Inspected development |
| First reserved 50, original result | {first['all_passed']}/50 routes; 42/42 taxonomy labels | First frozen diagnostic, then opened for repair |
| Same 50 after further repair | {opened['all_passed']}/50 | Regression only; not an untouched score |
| Separate 30 unused wordings | {second['passed']}/30 | Frozen before predictions; not used for tuning |

The last check has 16 supported, six excluded, four ambiguous/noisy and four unrelated questions. For unrelated questions, referral or clarification is acceptable; admission as supported is not. Its small, synthetic sample cannot establish real-user accuracy. The first reserve's three failures and later role change remain visible in `reserved-final.json` and `reserve_exposure.json`.

The full application also completed **153/153 local development checks**: readable responses, zero provider calls, closed legal gates and intact domain/source checks. Final-pay/COE remains a known source-availability gap. No missing authority or quoted text was fabricated.

## Historical metrics and remaining differences

The updated checksum-pinned **436-input / 171-family** replay retains **425/425 primary** and **425/425 coverage** matches, with macro F1 **1.000** for each head. These repeatedly inspected synthetic results are regression evidence, not independent accuracy. There are **428/436 exact route matches**. Four differences are intended wage/category-policy changes against unchanged old clarification expectations. Four are conservative clarification deferrals for excluded investment, seafarer-record and municipal-appeal wording. Original expectations were not rewritten to inflate the score. All 436 keep legal permissions closed; 2,361 candidate checks find no integrity or cross-domain leaks.

The four excluded-topic deferrals remain visible in the new historical `errors.json`. Exact current final-pay/COE authority, independent human questions, legal source/currentness approval and live generated-answer evaluation remain outstanding. Confidence is a label estimate under the calibration distribution, not legal correctness. The existing performance page reads the refreshed local replay and keeps older LLM comparisons historical.

## Timing and explanation checks

On this machine, 120 matched warm single-question raw-classifier calls per version give median **{before['median_ms']:.2f} → {after['median_ms']:.2f} ms** ({summary['raw_latency']['median_reduction_percent']:.1f}% lower), and p95 **{before['p95_ms']:.2f} → {after['p95_ms']:.2f} ms**. Cold loading is excluded, profiling is disabled, and processes are separate. This is not end-to-end LLM latency. The historical local classifier/retrieval/verifier median is **{s['latency_ms']['median']:.1f} ms**.

For 12 source-context samples, serialized source characters fall **{old_chars:,} → {new_chars:,}** ({summary['source_context']['reduction_percent']:.1f}% smaller), retaining every complete parent text. Contract tests verify offsets and restored proof. **No live provider calls were made**: improved output style and reduced provider latency have not been empirically established by this repair. Actual provider latency includes generation and a separate support check; rejected drafts still use a readable, explicitly local fallback.

## Verification and use

- Backend: **187 tests pass** (`backend-tests-complete.log`), including provider failure, cancellation, history isolation, source checks and normalization export-plan identity/bounds.
- Core package checks: **69 classifier, 47 retrieval and 37 verifier tests pass** in the selected verifier packet.
- Frontend: **24 tests**, lint and production build pass. No interface redesign was made.
- Metrics reconciliation and historical artifact preservation pass. No external API spending; no fresh legal approval.

Restart an older manually launched website/API after pulling changes, then open the URL printed by `start-website.ps1`. Use AI off to inspect classification, routing and sources. Enabling AI adds the conditional wording layer and source-bound explanation path; this repair does not promise an AI-generated legal answer when evidence or support checks fail.
'''
(HERE/'REPORT.md').write_text(report,encoding='utf-8')
status_path=ROOT/'backend/normalization_status.json';status=json.loads(status_path.read_bytes())
status.update(version='conditional-normalization-v3.0.1',latest_gate_repair='Clear specialized-scope context can bypass dictionary-only fallback; observed corruption still triggers conditional interpretation.',
 latest_gate_repair_report=HERE.relative_to(ROOT).as_posix(),latest_gate_repair_live_provider_test_completed=False,
 historical_live_provider_test_version='conditional-normalization-v3.0.0')
status_path.write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'new_forms':233,'latest_unused_wording_check':f"{second['passed']}/{second['total']}",'raw_median_reduction_percent':summary['raw_latency']['median_reduction_percent']}))
