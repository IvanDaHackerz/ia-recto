# Submission-readiness engineering report

Recorded 2026-10-31T23:06:35.710901+08:00. The local prototype has been exercised with 100 newly worded fictional Philippine questions and a complete AI-on repair replay. Reading those answers led to source-guard/context repairs, eight targeted AI checks and three source-qualification confirmations. The last review quarantined the ambiguous religious-rest scheduling provision and enforced the quantity rule's inherent-variations qualification; these final controls were checked offline and through the complete software suite. **All recorded batch AI results predate those last two controls.** The final classifier/retrieval local replay covers all 100 cases. Original results, failures, raw synthetic provider drafts and immutable package checks remain preserved. This is an engineering readiness check; it does not certify independent legal-answer accuracy or public deployment.

## Questions and protocol

30 labor, 30 consumer, 25 mixed and 15 outside-scope questions; 51 English, 36 Taglish and 13 noisy Taglish. [All questions](QUESTIONS.md), [frozen expectations](live-cases.json), [acceptance criteria](acceptance-criteria.json). Wording was compared with 1,199 earlier unique questions: zero exact duplicates and no nearest overlap above the recorded 0.72 text-similarity threshold. Topic families overlap; fresh wording is not statistical independence.

Expected labels/routes and nonexhaustive known-relevant source IDs for 54 cases were frozen before inference. No expected labels were changed after testing. The 100 cases never entered model fitting or calibration. Once inspected to guide repairs, they became opened development cases.

## Measured results

On the final classifier/retrieval stack with AI off, all 100 questions match their expected topic, coverage and route, all 54 judged cases hit known-relevant evidence at five, and the 15 outside-scope questions retrieve zero candidates. These are opened synthetic development results. [Final local results](signed-final-local/metrics.json).

Errors count in the denominator. The original run's raw metrics summarize successful packets only; [the inclusive audit](first-pass-audit.json) corrects that presentation without editing the original record.

| Check | Original AI run | Intermediate AI replay (classifier 70/retrieval 57/verifier 64) |
|---|---:|---:|
| Response packets | 99/100 | 100/100 |
| Expected topic | 90/100 | 100/100 |
| Expected coverage | 91/100 | 100/100 |
| Expected route | 77/100 | 100/100 |
| Supported domains retained | 80/100 | 100/100 |
| All judged concerns hit a known-relevant source in top five | 42/54 | 54/54 |
| Outside-scope legal explanation claims | 0/15 | 0/15 |
| Citation integrity failures | 0 | 0 |

Post-repair macro F1: topic 1.0000; coverage 1.0000. These are scores on the opened synthetic repair set, not a professor's unseen-question accuracy. Per-question confidence concerns classifier labels; it does not measure legal correctness.

The final source checks rejected **20 of the intermediate run's 88 previously accepted claims** as regression counterexamples. This is evidence that same-model approval is fallible, not a measured legal-accuracy estimate. The eight-question recheck returned 8/8 packets: `{"generated": 6, "withheld": 2}`; fallback reasons: `{"citation_validation_failed": 1, "provider_unavailable": 1}`. Reading those answers exposed further overstatements. The subsequent three-question confirmation returned 3/3 packets: `{"generated": 2, "withheld": 1}`. Supplier liability received a disclosed source fallback. The two generated confirmations led to the final religious-source eligibility hold and quantity qualification check; they are historical diagnostic outputs, not approved final answer examples. [Eight-question results](final-targeted-audit.json), [historical confirmation answers](final-confirmation-ANSWERS.md), [last control audit](final-confirmation-guard-revalidation.json). A complete 100-question AI replay on the last runtime remains pending; it was not silently substituted with targeted results or allowed to exceed the study call cap.

AI replay outcomes: `{"generated": 52, "partially_generated": 18, "withheld": 30}`. Non-generation reasons: `{"citation_validation_failed": 7, "claim_support_failed": 3, "no_supported_explanation": 2, "provider_unavailable": 3, "supported_concern_required": 15}`. Read [every recorded answer and citation](repaired-ANSWERS.md), [raw replay metrics](repaired/metrics.json) and [the independent integrity audit of saved packets](repaired-audit.json). Integrity audit is independent code, not an independent legal reviewer.

Intermediate AI latency: median 13.9s, 95th percentile 34.3s, maximum 48.1s. Final shared evaluation ledger: 398 provider attempts, estimated $0.4408; not verified billing. Browser smoke calls are recorded separately in browser-smoke-observations.json and browser-final-observation.json. The study stop remains 400 attempts/$0.50 estimated. No private user chat text was used.

## Repairs and software checks

- Scoped language/context handling now recognizes the demonstrated private-workplace, Taglish work-duty, night-differential, certification and paid-service questions. A product charger is not a money charge. Special-worker, regulated-service and outside-scope exclusions remain active.
- Explicit separate concerns are retained, including a third inheritance concern. Anaphoric questions and workplace introductions stay with the issue they describe. Resignation notice remains distinct from employer dismissal.
- Retrieval focuses probation, price comparison/display, pay frequency, certification representations, resignation and product safety. Product-damages claims do not borrow warranty-expense liability rules.
- Explanations keep correction-period bounds distinct from remedy options, do not infer a refund from guaranty duration alone, and do not infer the absence of prorating law from a short excerpt. Source-reading notes preserve actors, alternatives and timing. Trailing internal quote IDs are removed without changing evidence or raw drafts.
- Provider work stops before the outer request deadline, leaving time for a readable fallback. A content revision is attempted only with enough time for another support check. Cancellation and fail-closed support/citation checks remain in place.
- Vite was patched to 8.3.3. The post-patch dependency audit reports zero vulnerabilities. No UI redesign was performed.

The atomic classifier coefficients, vocabulary, confidence thresholds and training membership remain unchanged from the original selected parent. Feature changes required recalibrating probabilities using only the original grouped training folds. Failed classifier candidates v1.5.68 (incompatible calibration) and v1.5.71 (changed an established context representation) are preserved and were never selected. Final packages: **outputs/item10-classifier-v1.5.72**, **outputs/item11-retrieval-v1.3.59**, **outputs/item12-verifier-v1.0.65**.

Final package checks: 69 classifier tests, 60 retrieval tests, 37 verifier tests, and 52/52 verifier development scenarios. The additional submission regression module has 40 tests, plus an application-level hold/export regression. See project-checks-release.log for the full final backend/frontend/dependency/metric reconciliation run; package and backend tests overlap and must not be added as independent accuracy samples.

The frozen 436-input local replay records topic 425/425, coverage 425/425, route 432/436. [Local replay](../local-pipeline-evaluation-v1.6.35/metrics.json). The expected four historical route-policy differences remain documented in that replay; unlabeled diagnostic cases are not included in label denominators.

The historical retrieval benchmark retains its original labels: 56/56 positive queries hit at five; 10/11 old negative expectations match. IR_NEG_11 now has a bounded official final-pay/COE statement available, so its old no-evidence expectation is intentionally not silently relabeled.

## What remains before final acceptance

Have another person try their own questions, and have substantive legal interpretations/current source applicability reviewed. Same-model generation/support checks missed semantic errors in the original run; [initial reading notes](initial-review-notes.json) record them. The final replay must still be read alongside sources. MO28/OCR/handbook authority holds remain; current-guidance and deployment permissions remain closed. Provider failures or incomplete evidence may produce a disclosed fallback rather than a generated legal explanation.

Use [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) for the presentation. Run the launcher and use its printed URL. The runtime/config backups and original failures remain in this study folder. No Git commit, push or publication was performed.
