# Local pipeline evaluation and repair

Completed 19 October 2026. Development use only.

The current local classifier, retrieval and verifier now run together on a frozen development packet. The Performance page defaults to these measured results and retains the earlier conditional-LLM comparison separately. **No external LLM calls, generated legal answers, new training questions or model fitting were used in this work.**

## Current artifacts

- Classifier: `outputs/item10-classifier-v1.5.12`, parent v1.5.11.
- Retrieval: `outputs/item11-retrieval-v1.2.8`, parent v1.2.7.
- Verifier: `outputs/item12-verifier-v1.0.7`, parent v1.0.6.
- Frozen cases: `outputs/local-pipeline-cases-v1.1.0`.
- Final evaluation: `outputs/local-pipeline-evaluation-v1.1.0`.
- Original pre-repair evaluation: `outputs/local-pipeline-evaluation-v1.0.0`, preserved with its original cases and results.
- Website result binding: `backend/application/performance_current.json`, pinning metrics, observations and protocol hashes.

The evaluator is `backend/evaluate_local_pipeline.py`. The final packet archives its evaluator and metric implementation, frozen inputs/expectations, observations, errors, protocol and checksums. `artifact_audit.json` beside this report verifies both evaluation packets and all three new runtime packages.

## What was measured

There are **436 input forms from 171 wording families**: the exact 424 earlier AI development forms plus 12 joined-concern regressions. Of these, 425 have topic/coverage labels and 11 have routing-only expectations. There are **zero independent human questions**. Expectations were frozen before inference; the evaluator passes only question text to the runtime and scores expectations afterward.

The main path runs real classification, retrieval and current-guidance preflight with `normalizer=None`. A network guard blocks the evaluator's HTTP opener. Neither wording nor explanation generation is invoked. Candidate provenance/metadata/domain checks use the real verifier. A separate diagnostic path submits exact stored excerpts to citation postflight; those are recorded quotations, not generated legal explanations or approval of current law.

| Metric | Final result |
|---|---:|
| Topic label accuracy | 425/425 (100.0%) |
| Coverage label accuracy | 425/425 (100.0%) |
| Topic / coverage macro F1 | 1.000 / 1.000 |
| Expected next-step route | 434/436 (99.5%) |
| Partial-support recall | 135/135 (100.0%) |
| Routing-only clarification | 11/11 |
| Known-relevant Hit@1 | 73/93 (78.5%) |
| Known-relevant Hit@5 | 93/93 (100.0%) |
| Mean known-relevant recall@5 | 92.5/93 (99.5%) |
| Known-relevant MRR@5 | 0.855 |
| Unsupported forms admitted to retrieval | 0/80 |
| Candidate integrity checks | 2,331/2,331 passed |
| Exact diagnostic excerpt claims | 471/471 passed |
| Wrong-domain candidate leaks | 0 |
| Inputs retaining closed live permissions | 436/436 |
| Unapproved explanations withheld | 436/436 |
| LLM requests / generated legal answers evaluated | 0 / 0 |

Label accuracy scores the raw predicted label even when the chosen route asks for clarification. Therefore matching labels do not imply a matching route or an approved answer. Hit@5 means at least one known relevant provision is in the first five for a judged concern group; it does not mean every candidate is relevant. Recall@5 is slightly below 100% because one judged group has more than one known relevant provision. The joined-regression stratum has 10/10 Hit@5 but 0/10 Hit@1, so first-result ranking still has room to improve.

Main-path latency was approximately **149 ms median / 207 ms p95** on this machine. It includes classification, retrieval and current-guidance preflight, and excludes the separately measured diagnostic excerpt postflight. It is not an LLM response-time estimate.

Topic ECE is **0.130**. Most topic predictions have approximately 87.2% label confidence; one tentative prediction is 31.2%. Confidence has not been validated on future users. Descriptive 95% family-cluster bootstrap ranges are archived in `metrics.json`: route match about 98.8–100.0%, and topic/coverage/Hit@5 100–100% because the inspected packet has no errors on those endpoints. Those degenerate ranges are **not population confidence bounds or evidence of certainty**.

## Repairs and before/after comparison

The pre-repair run exposed noisy-word recognition, consumer-label concern detection, and lexical retrieval misses. The repairs add unique typing anchors for cashier, security, tenure, letter, bargaining, unit, explain and raise; recognize an explicit net-quantity plus product-label concern; and expand retrieval concepts for Tagalog `sukli`/shortchanging and labeling. The rules apply to concepts, not evaluation case IDs. Ambiguous `prdct` and `pnson` remain unresolved when their meaning cannot be established. Scope exclusions retain priority.

The unchanged original 424-form stratum provides the direct comparison:

| Metric on identical original inputs and expectations | Before | After |
|---|---:|---:|
| Topic labels | 413/414 | 414/414 |
| Coverage labels | 413/414 | 414/414 |
| Expected routes | 417/424 | 422/424 |
| Known-relevant Hit@5 | 78/83 | 83/83 |
| Known-relevant Hit@1 | 71/83 | 73/83 |

The additional 12 joined-concern regressions retain 12/12 expected routes and 11/11 topic/coverage labels. Ten have judged retrieval groups, all hitting a known relevant provision in the first five. These regressions exercise supported-plus-excluded concerns across connectors/order, fully supported labor-plus-consumer concerns, negation, and an unidentified dispute requiring clarification.

Classifier package lineage confirms unchanged atomic weights, feature vocabulary, calibration, thresholds and training membership. The retrieval records and semantic vectors are byte-identical to the parent; the build reused 719 vectors. No legal-source reviews, canonical texts or currentness permissions were added. The original packets remain preserved.

### Retrieval-judgment correction

The first new English joined-concern case says an employer owes **wages**, but its initial preparation mistakenly assigned the overtime article (Art. 87) as a known relevant provision. That is an invalid judgment. The corrected case freeze explicitly marks retrieval for `joined_english` as **unjudged**, with no relevant IDs. Its question and classification/routing expectations are unchanged. The correction is recorded in `freeze.json`; all original 424 forms and expectations remain identical. This reduces the combined judged retrieval denominator from 94 to 93. The original 88/94 result is preserved, but should not be compared directly with final 93/93 as if the judgments were identical. The table above compares only the unchanged 83 original concern groups.

## Remaining limitations

Two noisy forms still choose clarification instead of the expected out-of-scope referral:

- `EVAL_090__noisy`: exact pension computation with ambiguous `pnson` and compressed wording.
- `EVAL_100__noisy`: prediction of a municipal employee's appeal outcome with compressed `mnnalo` and `i-prdct`.

Their raw labels match the recorded out-of-scope expectations, and neither receives unsupported retrieval or a legal answer. They remain recorded routing errors. The Performance question explorer labels them **“Labels match; route differs.”** No threshold was lowered to force a referral. These are useful cases for a later current-stack conditional-wording comparison.

All scores are from AI-authored development inputs inspected during repairs. Repeated families, hand-authored expectations, reused inputs and implementation selection prevent an independent generalization claim. Software tests and exact quotations do not establish current legal correctness. Independent evaluation/owner acceptance, scoped source/currentness reviews, contact follow-up, a current-stack conditional-LLM comparison, and actual generated-answer evaluation remain pending. The older Item 13 screening run is still historical and has not been relabeled as a current formal acceptance run.

## Verification

- **258 distinct software tests passed:** 65 classifier, 43 retrieval, 37 verifier and 113 backend/normalization/terminal/local-evaluator/application tests. The 65 classifier checks reran during verifier packaging and are counted once. Provider behavior in software tests is mocked; no paid requests occurred.
- Meaningful checks cover training wordform preservation, ambiguous-word handling, scope exclusion priority, known-provision retrieval, frozen-input tampering, family intervals, verifier gates, historical-result preservation and per-case evidence output.
- **261 numeric comparisons passed** between the page's calculations and the saved local/historical metrics, with exact confusion-matrix, language/empty-filter and withheld-label checks.
- Frontend TypeScript/Vite build and ESLint passed. Impeccable detector returned no findings on the changed UI/data targets.
- Desktop and a 390px browser viewport were inspected (captures are 375px content width after scrollbar). Current/historical selection, historical Pipeline selection and language filters work. Technical tables scroll internally; the document does not overflow horizontally. The fresh scoped finish reviewer returned **ship**, with no material fixes.
- Local API through the Vite proxy returns 436 current cases, baseline-only availability, matching current bindings, 424 historical cases and the historical stack-mismatch disclosure. Health reports ready. This check contacted only loopback.
- New package/evaluation checksums pass, and generation, display/current-guidance, deployment and independent-acceptance permissions remain closed.

Evidence: `backend-tests.log`, `artifact_audit.json`, runtime package software-test manifests, and `UI/UX/app/.impeccable/review/local-pipeline/`. The initial test-only Windows temporary-directory permission issue was corrected by using the workspace's temporary directory; the final 113-test run passes.

## Website behavior

Overview remains the simple view: topic/coverage scores, route match and inspectable questions. Detailed results holds F1, class scores, confusion matrices, confidence calibration, routing/retrieval and full-run evidence checks. The new local run is the default; **Previous LLM comparison** remains a separate historical option with its recorded stack. No report view invokes a model or adds questions to training.

Next work is a separately scoped current-stack conditional-wording comparison, followed by independent questions/owner testing and the outstanding source/generation approvals before legal explanations can be enabled. This local evaluation does not unlock those gates.
