# Item 10 — Human review and classifier training plan

Current implementation: **classifier v1.5.6**, retrieval binding **v1.2.5** and verifier binding **v1.0.3**. The classifier passes 60 software checks; its local API passes 30 boundary/HTTP checks. The 11 inspected routing scenarios now take their expected routes. Learned weights, features, calibration and thresholds are inherited unchanged. Formal evaluation, metric presentation, owner terminal testing, website and LLM integration remain deferred. [Implementation report](C:/IA/outputs/classifier-preintegration-v1.0.0/IMPLEMENTATION_REPORT.md). [Backend interface](C:/IA/backend/classifier/README.md). Older numeric results retain their historical roles.


Item 10 converts the Item 9 synthetic seed set into a reviewed training dataset, trains reproducible classifier baselines, selects operating thresholds, and produces a versioned model package. Training must not begin merely because the Item 9 validator passed. That validator checks structure, not whether every question sounds natural or has the correct legal-scope label.

## Historical v1.4.0 exploratory results — 17 October 2026

The historical **item10-classifier-v1.4.0** candidate implemented a focused partial-support repair. Fragment accounting preserves each concern, background and follow-up; unresolved concerns require clarification. Supported and excluded components remain separate, and excluded concerns are omitted from retrieval requests.

On the previously opened synthetic set, now used only as regression evidence, partial-support recall improves from **7/11 to 11/11**, with precision 1.000. Four original errors are corrected, with no new classification regressions. Classification accuracy is 99/100 on this inspected set. The original v1.3.1 once-unseen result (95/100) is preserved and has not been replaced by a new independent-test claim.

Forty software tests and 59 frozen-data checks passed. The training rows, taxonomy definitions and underlying atomic classifier weights are unchanged; grouped calibration was refitted on training data only and thresholds selected on validation. The three known development partitions pass their targets. Opened-set regression coverage is **69% versus the 70% target**, so overall acceptance remains incomplete and deployment is disabled. A fresh independent holdout is still required.

[Partial-support repair report](C:/IA/outputs/item10-classifier-v1.4.0/PARTIAL_SUPPORT_FIX.md). [Current experimental model card](C:/IA/outputs/item10-classifier-v1.4.0/MODEL_CARD.json). [Preserved original accuracy report](C:/IA/outputs/item10-classifier-v1.3.1/ACCURACY_REPORT.md).

Use the isolated `C:/IA/.venv-item10/` environment. `train_logical_classifier.py --scope-constraints --calibration temperature --parent-run C:/IA/outputs/item10-classifier-v1.3.1 --run-dir <new-directory>` reproduces the focused development repair. `test_logical_classifier.py` checks membership, calibration, replay and routing. `evaluate_partial_support_repair.py` explicitly records opened-test regression use. Both current and legacy final-test entry points block reuse of the old source as fresh evidence. Executable source scripts retain their project-relative layout; output copies are provenance snapshots.

## Review/consolidation status — 17 October 2026

The five assigned human reviews have been consolidated. [Reviewed dataset v1.0.0](../../processed/item10/reviewed_v1.0.0/README.md) contains 661 included questions and 11 retained human rejections. The returned workbooks and Item 9 seed remain unchanged. Cleaned copies are in `outputs/item10-review-cleaned/`; all 672 reviewed rows are complete, including the rejected rows retained for audit.

Project-owner-authorized AI cleanup corrected decision-field inconsistencies, scope-label overrides, wording/scenario changes, language metadata, and context-specific seafarer referrals. It is disclosed in every record and in the change log; it is not a second independent human annotation. The 11 rejected variants remain excluded as conservative variant selection, without adopting unsupported exact-duplicate or leakage claims.

The new version assigns 459 train, 102 validation, and 100 test questions. It preserves original question IDs, scenario_group_id, and original_split. A separate leakage_group_id groups rights/steps variants of the same underlying single-issue scenario together. This removes the 42 detected validation/test overlaps without changing Item 9.

`review_cleanup_decisions.json` records explicit adjudications and input checksums. `consolidate_reviews.py` creates the versioned data and workbook-edit payload. `validate_reviewed_dataset.py` checks source preservation, workbook consistency, label/topic/routing alignment, split grouping, and provenance. Use `--freeze` only after validation passes. The consolidation script refuses to overwrite an already frozen version; further changes need a new version.

`repair_review_workbooks.mjs repair` authors the cleaned copies with Artifact Tool using the bundled Codex dependency runtime. It also refuses to overwrite frozen workbooks. The runtime Node package directory can be supplied with CODEX_ARTIFACT_NODE_ROOT. After freezing, run `validate_reviewed_dataset.py` without `--freeze` for a read-only checksum and consistency audit.

The review phase is complete. Formal final evaluation remains gated on the independent human-written/labeled gold set and recorded team/adviser targets. No model was trained by the original cleanup; the later owner-authorized exploratory results are recorded above.

Human-review instructions: [`ANNOTATION_GUIDE.md`](ANNOTATION_GUIDE.md)

## AI-reviewed development benchmarks — 17 October 2026

At the project owner's explicit request, Codex reviewed and approved the two new 100-question sets for exploratory evaluation. [Versioned data and review logs](C:/IA/dataset/processed/item10/ai_reviewed_eval_v1.0.0/README.md) contain 100 general questions and 100 typing/clarification questions. There are 180 labeled records and 20 clarification tests; the latter retain null primary/scope labels. The typing set has 20 scenario families, each with five variants that must remain together.

All 200 decisions record an AI reviewer; no human review, independent human authorship or legal-professional approval is claimed. Ninety-one wording revisions and two topic corrections were recorded. The sets remain development benchmarks, excluded from training and unlocked for expected revisions during testing. They do not satisfy the independent human-written/labeled gold prerequisite below. The frozen 661-question reviewed seed is unchanged. [Full dataset inventory](C:/IA/dataset/DATASET_INVENTORY.md).

Five-person workbook guide: [`../../../outputs/item10-review-workbooks/GROUP_REVIEW_GUIDE.md`](../../../outputs/item10-review-workbooks/GROUP_REVIEW_GUIDE.md)

## Decisions recorded

The owner-approved [evaluation policy](C:/IA/dataset/pipelines/item10/EVALUATION_POLICY.md) defines metrics, clarification/routing behavior and development/test data boundaries. Targets and approval status are mirrored in [evaluation_policy.json](C:/IA/dataset/pipelines/item10/evaluation_policy.json). The repaired candidate selected experimental confidence cutoffs of 0.80 primary / 0.85 scope on validation. Development targets pass, but opened-set regression coverage is 69% versus the 70% target; these are not approved live thresholds. Project-owner exploratory authorization is recorded; required formal team/adviser approval and human gold remain outstanding.

- MVP classifier languages: **English and Taglish**.
- Classification design: a four-way primary label plus a separate three-way scope label.
- Proposed performance and abstention thresholds below are recorded for later team/adviser approval before the locked final test.
- MVP review policy: one assigned human reviewer per row. Independent double annotation and agreement scoring are not mandatory; their omission will be disclosed as a project limitation.
- Human review and owner-authorized consolidation are complete. The independent gold test set and team/adviser target approval remain pending before final model training and evaluation.

## What the classifier must decide

The project needs more than one prediction:

1. `primary_label`: `labor`, `consumer`, `mixed`, or `out_of_scope`.
2. `scope_label`: `fully_supported`, `partially_supported`, or `unsupported`.
3. Supported and excluded topic signals used for routing, retrieval filters, and referrals.
4. A calibrated confidence score and an abstain/clarify outcome for uncertain questions.

The four-way label and scope label must remain separate. A mixed labor-and-consumer question can be fully supported, while a supported consumer issue combined with a banking issue is only partially supported.

## Prerequisites requiring human attention

### 1. Review the 672 Item 9 questions

Open `dataset/processed/item9/classifier_questions.csv` and review every row before it becomes approved training data. For each row:

- correct awkward English or Taglish without changing its intended scenario;
- confirm `primary_label`;
- confirm `scope_label`;
- confirm supported and excluded topic IDs;
- confirm the routing action and referral IDs;
- record the reviewer and review notes; and
- change `annotation_status` only after the row has actually been checked.

Deleting a bad question is better than approving an ambiguous one. Do not change the `question_id`, `scenario_group_id`, or assigned split while editing wording.

### 2. Decide the supported languages

The current dataset covers English and conversational English-Taglish. It does not adequately cover questions written entirely in Filipino or regional languages.

Recommended MVP decision: officially support English and Taglish for classifier evaluation. Preserve Filipino-only input, but route it through a recorded normalization or clarification fallback until a reviewed Filipino dataset is added. If full Filipino is declared supported now, more human-written Filipino questions must be collected before training.

### 3. Confirm the two-output classification design

Recommended design:

- train a four-way primary classifier;
- train or implement a separate scope detector for `fully_supported`, `partially_supported`, and `unsupported`; and
- use topic predictions or deterministic routing rules to select referrals.

Do not train only the four-way label. The `mixed` class alone cannot distinguish a fully supported labor-plus-consumer question from a supported-plus-excluded question.

### 4. Create an independent gold test set

The current test rows came from the same generator as the training rows. Group-safe splitting prevents direct paraphrase leakage, but it does not eliminate generator-style bias.

Before final evaluation, create an independently written and human-labeled gold set that:

- is not produced by `build_item9.py`;
- contains English and natural Taglish;
- includes all four primary labels;
- includes fully supported, partially supported, and unsupported cases;
- includes short, vague, misspelled, incomplete, and multi-issue questions;
- contains difficult boundary cases; and
- is locked before model tuning.

A practical MVP target is at least 100 independently written questions. More is better, but quality and independence matter more than artificially increasing the count.

### 5. Agree on annotation quality control

At least one reviewer must check every training row. The MVP will not require a second independent reviewer or agreement statistics because the team considers that workflow too burdensome. This limitation must be stated in the methodology and evaluation report. If convenient, uncertain rows may still be discussed by the group or escalated to the project lead without turning the process into formal double annotation.

The legal professional required by the proposal does not need to rewrite every classifier question, but should review the annotation guide and a sample of difficult legal-scope boundaries if that review can be arranged.

### 6. Set success and safety thresholds before looking at test results

Choose the minimum acceptable classifier performance and abstention policy before opening the locked test results. Recommended starting targets for discussion are:

- macro F1 of at least 0.80 for the four primary labels;
- recall of at least 0.85 for `out_of_scope`;
- recall of at least 0.80 for partially supported or mixed-boundary questions;
- no class with recall below 0.70; and
- uncertain predictions below the selected confidence threshold must ask for clarification or decline instead of forcing a label.

These are proposed project thresholds, not legal or industry standards. The team and adviser should approve or adjust them before final testing.

### 7. Protect any real user data

Synthetic questions contain no personal data. If real questions are later collected, remove names, employers, addresses, case numbers, phone numbers, account numbers, and other identifying details. Record consent and collection provenance where required. Never send an unredacted real legal problem to an external LLM merely to expand the dataset.

## Training work to perform after prerequisites

### A. Freeze the reviewed dataset

- Export an approved dataset version rather than overwriting the Item 9 seed file.
- Preserve the original synthetic file for provenance.
- Record dataset version, file names, row counts, label counts, language counts, reviewer status, and split assignments.
- Keep every `scenario_group_id` in only one split.
- Lock the independent gold test set against further tuning.

### B. Define reproducible baselines

Train and compare at least:

1. a majority-class or stratified dummy baseline;
2. word and character TF-IDF with logistic regression;
3. word and character TF-IDF with a linear support-vector classifier, with calibration if confidence scores are needed; and
4. optionally, a multilingual sentence-embedding or transformer classifier if the available hardware, time, and dataset size justify it.

With only hundreds of reviewed questions, classical linear baselines are important. A larger neural model is not automatically better and may overfit the synthetic writing style.

The external LLM API may be evaluated as a separately recorded routing fallback, but it should not replace the independently measured classifier promised in the proposal.

### C. Prevent training leakage

- Use only `question_text` as the main text input.
- Do not expose labels, topic IDs, referrals, routing actions, or split names as model features.
- Fit vectorizers and preprocessing only on the training split.
- Tune models and thresholds only on training and validation data.
- Open the locked test set once for the final selected configuration.
- Keep scenario groups intact during any cross-validation.

### D. Train the required outputs

- Four-way primary-domain classifier.
- Scope-support classifier or equivalent deterministic scope layer.
- Optional topic-level multi-label classifier if validation shows it is reliable enough.
- Confidence calibration and explicit `abstain_or_clarify` behavior.
- Referral selection based on verified topic/routing logic, not free-form model invention.

### E. Evaluate comprehensively

Report:

- accuracy;
- macro, micro, and per-class precision, recall, and F1;
- confusion matrices;
- performance by English versus Taglish;
- performance by fully supported, partially supported, and unsupported scope;
- performance on short, vague, misspelled, and multi-issue questions;
- calibration or confidence reliability;
- abstention coverage and error rate; and
- performance on the independent gold set.

Accuracy alone is insufficient because the safety-critical errors are asymmetric. Misclassifying an out-of-scope question as supported is more dangerous than declining a borderline supported question.

### F. Perform error analysis

Manually examine false positives, false negatives, confused labor/consumer examples, missed partial-support cases, Taglish failures, and overconfident predictions. Categorize the causes before changing data or model settings. Keep the final test set untouched while making improvements.

### G. Package the selected classifier

Save:

- the fitted text vectorizer or tokenizer;
- model weights;
- label mappings;
- preprocessing and normalization version;
- confidence and abstention thresholds;
- training-data version, source file names, and row counts;
- library versions and random seed;
- metrics and confusion matrices;
- error-analysis report;
- model card describing intended use and limitations; and
- a stable inference function returning structured JSON.

The inference result should include the original question, model version, primary label, scope label, topic signals, confidence, routing action, and whether clarification or referral is required.

### H. Add repeatable validation

The Item 10 pipeline should rebuild the model from the frozen reviewed data, reproduce the recorded metrics within expected tolerance, verify that no split leakage occurred, confirm that test data was not used for fitting, and run a small set of fixed routing checks before the model can be deployed.

## Items that are not classifier-training prerequisites

The following work remains important, but it does not block classifier training:

- reviewing the 182 Item 8 legal-document candidates;
- resolving all Item 7 OCR records;
- building the Item 11 retrieval index;
- implementing citation verification; and
- finishing the React interface.

Those components use the classifier later, but the classifier can be trained on reviewed questions without waiting for the legal-document pipeline to be fully complete.

## Formal final-evaluation readiness gate

Final model training/evaluation claims under the original plan require:

- the intended languages are declared;
- the primary and scope-label design is approved;
- the Item 9 rows selected for training are human-reviewed;
- the annotation guide is accepted;
- the independent gold test set is prepared and locked;
- the success thresholds are recorded; and
- any real questions have been anonymized and documented.

Until then, the frozen reviewed Item 10 seed supports the explicitly owner-authorized exploratory experiments above. This exception does not turn the AI development benchmarks into independent human gold, satisfy the final readiness gate, or authorize deployment. The original Item 9 file remains an unmodified synthetic seed.
