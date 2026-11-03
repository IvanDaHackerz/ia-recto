# Website classifier and source repair

The reproduced spelling, concern-handling and source-selection failures have been repaired and checked in the local application and real website. This is a development improvement, not independent human or legal acceptance.

Active stack: **item10-classifier-v1.5.30, item11-retrieval-v1.3.16, item12-verifier-v1.0.23**. The running website is http://127.0.0.1:5174/.

## Changes

- Local spelling repair no longer restores vowels or invents word boundaries in ordinary words as freely. “kind”, “hiring” and “liking” survive the reported transformations; the original typing-noise, literal, name, negation and idempotence checks pass.
- Employment detection requires an employment relationship or an intrinsic labor issue. “I must pay for repair” no longer creates an employment concern. Employer industry is distinguished from an actual banking, insurance or medical-service complaint.
- Rule questions stay connected to their existing concern. A new scope exclusion takes precedence over shared vocabulary, so an exact minimum-wage question remains separate from unpaid wages.
- Natural descriptions of household and overseas employment are recognized. Actual requests or reported discrepancies are retained instead of being discarded as actor introductions. Recognized financial-service concerns do not ask again what the payment was for.
- Disciplinary charges are distinguished from unexplained monetary charges.
- Retrieval uses explicit query concepts and relevant headings, with procedural subtopics for records, confidentiality, representation and internal redress. Unrelated effectivity provisions, recruitment fees, employee-resignation rules and quantity provisions are filtered from the demonstrated concerns.
- **Enclosing-rule coverage is preserved.** Its exact stored coverage text is carried into source conditions. A generic section heading no longer strips away a hospital-only rule's applicability. Conditions remain source-bound and do not grant legal approval.
- Local passages and LLM context share the topical check. Identical local quotations appear once. Irrelevant same-domain evidence cannot start a provider request in the adapter regression.
- Topic, coverage and label confidence remain available in diagnostics on local, clarification, referral and generated paths. Source excerpts are clearly labeled; they are not presented as AI explanations or findings about the user's rights.

The learned atomic weights, feature vocabulary, original training membership and thresholds are preserved. Calibration was replayed only on the original training folds; diagnostic/evaluation questions were not fitted. The original 362 indexed chunks / 353 provisions and all their parent/chunk text are unchanged. Derived rule-coverage restrictions were added; no source was promoted to legal approval or refreshed as current law.

## Completed checks

| Check | Result |
| --- | --- |
| Original website questions, replayed through the application with AI off | 50/50 expected paths; 46/46 labeled cases |
| Additional synthetic development questions | 24/24 expected paths; 23/23 labeled cases |
| Real website checks, desktop and mobile | 12/12 expected paths/labels; 12/12 diagnostics available |
| Repeated passages in the final browser pass | 0 |
| Browser quotations are exact spans of stored text | True |
| Backend tests | 205 passed |
| Frontend tests | 26 passed; build and lint passed |
| Packaged classifier / retrieval / verifier checks | 69 / 49 / 37 passed |

The 24 additional questions and 12 browser questions were new when authored, then inspected during repair. **They are now development/regression cases, not an untouched holdout or a human-written gold set.** A routing match or exact quotation does not establish legal-answer correctness. Some in-scope questions correctly show a source limitation.

The complete 436-input older development replay was rerun on this exact stack, with 0 independent human questions and zero LLM calls. Topic macro-F1: **1.0000**; coverage macro-F1: **1.0000**. Route matches: **432/436**. Known relevant Hit@5: **93/93**. These are reused synthetic-development results. The four older clarification expectations for already recognizable labor questions are preserved in the raw errors rather than silently relabeled for the broader general-information policy. The Performance page is bound to the new replay; the older full-AI replay remains marked as a different inference version.

## Remaining limits

- This repair did not test live LLM prose, latency, provider reliability or paid end-to-end generation. Adapter/validation tests use mocks; the website submissions used AI off. AI availability is restored afterward for new user submissions.
- Final-pay/COE and main thirteenth-month related-source gaps/reviews remain. A normal-hours passage also does not by itself resolve every compensable-time scenario. The application must state a source limit where the stored material is insufficient.
- Exact source identity and local topic matching are not legal entailment, current-law verification or a guarantee for unfamiliar wording. Fresh independent questions, legal review and owner acceptance remain pending.
- The Impeccable context loader reported a stale design metadata sidecar at `UI/UX/app/.impeccable/design.json`. Its optional `document` refresh was kept separate from this repair.

## Evidence

- `summary.json`, `regression-results.json` and `fresh_synthetic-results.json`: 74 application checks and complete packets.
- `browser-accepted-results.json`, `browser-summary.json`: the final complete 12-question website pass, with displayed fields and passages. `browser-new-results.json` preserves all 27 observations across development passes; the accepted file is its verified final 12-row suffix.
- `warranty-final-desktop.jpg`, `warranty-final-mobile.jpg`: rendered proof.
- `outputs/local-pipeline-evaluation-v1.6.6`: complete current-stack replay, preserved expectations and errors.
- `backend-tests-accepted.log`, `frontend-checks.json`, and the packaged software-test logs: verification records.
- Earlier failed/intermediate builds and observations are preserved. `round1-summary-scorer-mismatch.json` used unmapped internal route names; the final scorer maps those names explicitly without changing raw questions or observations.

No live provider call was made for these repairs. Changes are local; this task did not push a GitHub update.
