# Routing and concern-fragment repair — 26 October 2026

The owner authorized steps 1 and 2: repair three valid-question routing failures and stop background/follow-up sentences becoming extra concerns. The study directory retains the date of the interrupted start on 25 October.

## Result

Final selected stack: outputs/item10-classifier-v1.5.66, outputs/item11-retrieval-v1.3.54, outputs/item12-verifier-v1.0.61. All 96 selected routing/structure checks pass after inspection and repair. The three reported failures now route to a single labor or consumer component. This is development evidence, not an independent accuracy claim.

## Changes

- Keep temporal “saka lang”/“tsaka lang”, probation standards, product-operation descriptions and same-seller responses with their scenarios.

- Recognize retail condition descriptions such as refurbished/used items represented as new, without making a legal finding.

- Keep genuine employment complaints and information requests out of the background-only bucket. Retain excluded-job context, including seafarer versus generic overseas wording.

- Treat pure introductions and vague standards complaints as requiring clarification. Exclude negated category statements from context propagation.

- Attach scope/focus requests to an existing relevant concern. Preserve different actors, independent purchases/employment disputes and actual excluded concerns.

Original questions and a source-fragment accounting record remain available. The repairs change sentence grouping and explicit scope constraints; no new questions were fitted and no confidence threshold was lowered.

## Frozen checks

| Cohort | First check | Recheck after inspection |
|---|---:|---:|
| 40 previously inspected questions | 31/40 | 40/40 |
| 32 first reserved wording questions | 17/32 | 32/32 |
| 24 further wording questions | 23/24 | 24/24 |

All initial observations and intermediate failures remain in this directory. The 32- and 24-question cohorts were written/frozen before their respective first inference, then opened and used for repair after failures. Their later passing results are inspected rechecks, not fresh holdout results.

Before the first 32-question reserved check, NEW_032’s expected component count was corrected from one to two: unpaid overtime and a separate equipment-loss deduction should remain distinct. The original case file/hash and the pre-inference adjudication are preserved.

## Packaging and preservation

The selected classifier inherits its trained atomic model, feature vocabulary, probability calibration, thresholds and training membership unchanged. The retrieval rebuild updates integrity bindings: source records, semantic windows, vectors and coverage are byte-identical to the parent, and no law/source was added. Current-law reviews, legal-answer gates and deployment permissions remain unchanged.

Intermediate candidates and failed packaging attempts were preserved. A legacy repacker assumed files absent from this parent, so the existing preintegration packager was used. A later candidate failed an old background-introduction regression; it was not selected. The corrected release passes the required tests.

## Verification

Software checks pass: 45 concern regressions, 69 classifier package tests, 60 retrieval tests, 37 verifier tests and 285 backend tests. These suites overlap and should not be summed as independent questions. The selected application checks also pass 27 tests. See concern-final-source-tests.log, application-selected-tests.log, backend-final-tests.log and the sealed package software_tests.json files. Earlier backend-tests.log preserves the candidate failure and packaging errors; backend-final-tests.log records the corrected stack.

The final local replay (outputs/local-pipeline-evaluation-v1.6.31) covers 436 forms / 171 families. Topic and coverage each match 425/425 labeled inputs (macro F1 1.0 on this inspected development packet). Routes match 432/436. A known relevant provision appears in the top five for 93/93 judged concern groups, while top-one hits are 70/93. Outside-scope admissions are 0/80. Candidate integrity and recorded-excerpt checks pass; these checks do not establish legal correctness.

Four frozen historical route expectations differ from the existing conditional-general-information policy: SYS_05_2__clear, SYS_05_2__noisy, TYPE_081__clear, TYPE_081__noisy. Their original labels are preserved; no new route disagreement remains compared with the pre-repair replay.

Actual website submissions and visible results are saved in browser-evidence.json and browser screenshots. Website tests use AI off to isolate classification and source retrieval; the original AI-on preference is restored afterward. No provider credits were used.

## Limits and remaining work

- All questions are synthetic development inputs; inspected rechecks are not unseen validation.

- Expected component counts are structural judgments; they do not establish legal correctness.

- Classifier weights, vocabulary, probability calibration, thresholds and training membership were preserved.

- Source gaps and generated-answer quality were outside this task; no external LLM calls were made.

- The historical 436-question route expectations include preserved conservative-policy differences; consult the latest errors.json rather than claiming all historical routes match.

- This task does not close independent human evaluation, legal-source currentness review or unrestricted defense acceptance.
