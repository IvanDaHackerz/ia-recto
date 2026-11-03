# AI-on usability repair and development regression report

The classifier and retrieval routing improved on the inspected development questions. The AI explanation stage is still uneven. This report does not certify the system as completely usable or legally reliable.

## Questions and protocol

The frozen set contains **100 new fictional AI-authored questions**: 50 labor, 40 consumer, and 10 mixed labor/consumer. Expected labels were saved before inference. All 100 are within the project's topics; this batch cannot measure out-of-scope or partial-support recall. It contains no personal chat text and no independently human-written questions. The original question hash remains `bcab548029507c3ec4f1f54246ff4931f99cb9cb118052f96bbcfa78414eae70`.

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

The last-observed checkpoint now has **100/100 recorded questions**, including the two previously pending cases, with **73 generated and 27 withheld**. Current local checks accept 73 of those captured generated results and flag 0. This checkpoint combines cached broad-run observations and fresh targeted observations, always retaining the latest result, including failures. It is **not a fresh final 100-question AI pass**, and generated does not mean correct. Per-case source phase, local validation, and remaining AI-reading concerns are in `completed-checkpoint.json`.

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

The final backend suite passed **238/238 tests**: `True`. Selected builds passed classifier **69/69**, retrieval **50/50**, and verifier **37/37** software tests. The prior 436-question AI-off regression retained **425/425 labeled matches per head**, macro F1 **1.0 on this reused development set**, **432/436 route matches**, **93/93 known-relevant Hit@5**, and **0/80 unsupported admissions**. Its 1,605 candidate-integrity checks and 432 recorded-excerpt provenance checks had zero failures. Four historical route-policy differences remain disclosed.

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
