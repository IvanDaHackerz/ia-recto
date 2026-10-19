# Current-stack wording comparison and validation handoff

Completed 19 October 2026. This is AI development validation, not independent human or legal-answer acceptance.

## Result

The conditional wording layer resolved the two remaining local routing mismatches in this frozen run. **436/436 conditional routes matched expectations**, compared with **434/436 without the wording LLM**. All 425 topic and coverage labels, partial-support recall, and 93 judged retrieval groups retained their baseline results. This step did not change the classifier, normalizer prompt/validation, retrieval or verifier policy.

| On the same 436 frozen forms | Local only | Conditional wording LLM |
|---|---:|---:|
| Topic labels | 425/425 | 425/425 |
| Coverage labels | 425/425 | 425/425 |
| Topic / coverage macro F1 | 1.000 / 1.000 | 1.000 / 1.000 |
| Expected routes | 434/436 | 436/436 |
| Partial-support recall | 135/135 | 135/135 |
| Known-relevant Hit@5 | 93/93 | 93/93 |
| Routing-only clarification | 11/11 | 11/11 |
| Unsupported admission | 0/80 | 0/80 |
| Wording LLM calls | 0 | 5 |
| Generated legal answers | 0 | 0 |

The two corrected routes are `EVAL_090__noisy` (exact retirement-pension computation) and `EVAL_100__noisy` (predicting a municipal employee's appeal outcome). Accepted interpretations retained their original concern and produced the expected out-of-scope referral. No salary amount, contribution history, employment status or case outcome was invented.

Three interpretations were accepted: these two plus `SYS_05_2__noisy`, which still correctly asks for missing context. All three received a disclosed Codex AI semantic audit before aggregate metrics were opened. Two match the recorded reference verbatim; the third has an equivalent `Pwede`/`Puwede` spelling variant. No meaning changes were flagged in those three audits. This tiny AI audit is not a validated semantic-preservation rate.

Two other proposals (`TYPE_086__noisy` and `TYPE_096__noisy`) failed existing wording checks and stayed on clarification. Rejected text was not classified or retrieved. Their clarification expectations still match; a rejection is not counted as an observed semantic change or automatically deemed an unnecessary rejection.

## Calls, usage and timing

The local gate bypassed **431/436 forms**. All **179 clear forms** bypassed; all five calls were noisy forms in the previously approved synthetic question set. Each had at most one request, with no retry. There were no provider-unavailable results.

Provider-reported usage was **4,435 input tokens and 729 output tokens including reasoning**. The token-rate estimate is **$0.00110265**, not an invoice, using Together's verified [pricing](https://www.together.ai/pricing) of $0.15 input / $0.60 output per million tokens. The study retained a $0.50 stop and a stricter five-request ceiling.

Median/p95 main-path time on this machine was about **121/147 ms local** and **121/150 ms conditional**. Those overall percentiles hide the five calls because calls were only 1.1% of inputs. For called inputs, total conditional-path time was **1.52 seconds median**, ranging **1.40–2.43 seconds**. These are single-run observations, not response-time guarantees.

The paired route difference was **+0.46 percentage points**. Its descriptive 95% family-resampling range was **0.00 to +1.20 percentage points** across 171 recorded families. The lower bound includes zero; this development result does not establish a population benefit. All label differences were zero. Reused development inputs, correlated wording variants and implementation selection prevent a fresh accuracy claim.

## Protocol and checks

- Full packet: `outputs/normalization-evaluation-v3.0.1`, including readable report, metrics, CSV, immutable observations, semantic audit and hashes.
- Input case bytes and judgments exactly match `outputs/local-pipeline-cases-v1.1.0`: 436 forms, 171 families, 425 labeled plus 11 routing-only. The earlier English wages/overtime judgment correction remains disclosed and unjudged; no expectations were changed for this comparison.
- Both paths use classifier v1.5.12, retrieval v1.2.8 and verifier v1.0.7. The wording normalizer is v3.0.0, Together `openai/gpt-oss-120b`.
- The local baseline supplied only a predeclared gate/export ceiling. All 436 inputs were replayed on both paths, alternating execution order: **872 real pipeline executions**. Only typed question text and normalizer hints enter provider requests, never labels, canonical references or relevance judgments.
- `BoundedProvider` rejects an unplanned question hash or excess request **before export**. Frozen inputs/runtime hashes are checked before and after execution. The five actual calls exactly match the frozen trigger plan.
- Offline reconciliation confirms all **436 baseline assessments** match the prior local run, all **431 bypassed conditional assessments** match their baseline, six label/route endpoints reconcile independently, and all **436 CSV rows** match the observed cases. Package and evaluation checksums pass. See `comparison_audit.json`.
- **872/872 generation/display/deployment boundary checks remain closed.** No classifier fitting, threshold change, source approval, generated legal answer or deployment occurred.
- The changed evaluator/normalization/terminal suites passed **54 software tests**, including three new tests for export limits, immutable local cases/trigger-plan tampering, and finalizing joined cases without optional reference metadata. The final evaluator-only rerun passed 11/11. Full backend verification is recorded in `backend-tests.log`; the full suite has 116 tests. Provider tests are mocked and make no paid calls.

The unexecuted v3.0.0 preparation is preserved with a superseded note. Its pre-inference metadata still included legacy initial-suite quota/source fields, so the corrected evaluator prepared v3.0.1 afresh before any provider call. No started run or failed provider response was overwritten or selectively retried.

## What is ready next

The existing conditional fallback now has a measured current-stack regression comparison. Keep its narrow trigger and conservative rejection behavior for development. The Performance page's default remains explicitly the local-only run; its separately labeled historical comparison remains unchanged. This work does not silently replace those displayed records.

Fresh independent testing is **prepared, not completed**: `human_intake.jsonl` contains 100 blank slots, and [HUMAN_TEST.md](HUMAN_TEST.md) explains authorship, blind annotation, overlap review and freezing. Codex has not supplied or signed human questions. The existing validator's minimum is 100 completed independent questions; natural typing and routing-only challenges should be declared before testing rather than chosen from observed failures.

The explanation handoff is [EXPLANATION_HANDOFF.md](EXPLANATION_HANDOFF.md), with a checksum-backed snapshot in `explanation_readiness.json`. There are zero trusted source reviews and zero trusted claim reviews. Scoped currentness checks and the MO 28 dependency remain unresolved. Current review bindings are question/component specific; enabling arbitrary new-question explanations needs an explicit reviewed policy design and actual generated-answer evaluation, not a blanket document approval or a switched flag.

Independent questions/annotation, required source/reviewer decisions, owner acceptance and generated-answer testing remain outstanding. The handoff files make those tasks concrete; they do not claim them complete or unlock legal explanations.
