# Classifier evaluation policy — v1.0.0

Prepared and approved by the project owner on 17 October 2026 for exploratory baseline training and evaluation. Team/adviser approval and the independent human holdout remain outstanding for formal final evaluation. The owner explicitly authorized proceeding with statistics, confidence scores and an explanation of the tests. This does not authorize deployment or change the frozen dataset.

The four primary labels remain `labor`, `consumer`, `mixed`, and `out_of_scope`. Scope remains a separate prediction: `fully_supported`, `partially_supported`, or `unsupported`. English and Taglish are the intended languages. Clarification is a routing action, not a fifth primary class.

## Approved development success targets

These are project targets, not legal or industry standards. The existing Item 10 plan supplies the primary macro F1, out-of-scope recall, mixed/partial recall and minimum class-recall targets. The approved policy adds an overall scope target and explicit routing targets so abstaining on every question cannot count as success.

| Measure | Initial target | Meaning |
|---|---|---|
| Primary classification macro F1 | At least 0.80 | Average the four classes equally; do not let a strong class hide a weak one. |
| Scope classification macro F1 | At least 0.80 | Measure the separate three-way scope prediction. |
| Out-of-scope recall | At least 0.85 | Correctly identify at least 85% of truly out-of-scope questions. |
| Mixed-class recall | At least 0.80 | Correctly identify mixed concerns. |
| Partially-supported scope recall | At least 0.80 | Recognize when only part of a question is covered. |
| Recall of every primary class | At least 0.70 | No primary class may be ignored to improve the average. |
| Clarification on the current incomplete-question benchmark | At least 16 of 20 questions | Ask a relevant clarifying question rather than forcing a class-dependent answer. Report family results too: these are only four underlying incomplete scenarios. |
| Unsupported questions admitted for substantive answering | At most 5% | Of all truly unsupported classifiable questions, at most 5% may receive an answer-eligible routing decision, including partial-answer routing. This is a routing metric, not a measurement of actual generated-answer safety. |
| Decisive routing coverage | At least 70% | On classifiable questions, at least 70% receive a supported, partial, or unsupported routing decision instead of clarification. Referrals count as decisive routing; forced answers do not. |

Primary/scope classification metrics use every classifiable row, including rows where the routing layer abstains. Report routing coverage and admitted-error rates separately. Abstention must not remove difficult rows from the classification denominator. Apply comparison targets to raw values before rounding. Report numerators, denominators, per-class support and uncertainty; passing a target on a small synthetic sample does not establish real-user performance.

Use validation and development results to select a candidate. Keep final-test results separate. A failed target means investigate and revise in development, not silently lower the target after seeing final-test results. Any target change receives a policy version, date, reason and approval record. A revised target requires a fresh independent holdout for renewed final claims when the old test influenced that change.

## Routing rules

| Situation | Required behavior |
|---|---|
| Confident supported labor or consumer topic, fully supported scope | Permit retrieval within the identified topic. Substantive answering still requires eligible evidence and citation checks. |
| Confident supported labor plus supported consumer topics | Route as mixed / fully_supported and handle the components separately. |
| Confident supported and excluded components | Route as mixed / partially_supported. Identify the supported component, retrieve only for that component, explain the limitation and use a recorded referral for the excluded component. |
| Confident excluded-only concern | Route as out_of_scope / unsupported. State the coverage limit and use an appropriate recorded referral. Do not generate substantive excluded-topic advice. |
| Low confidence, conflicting outputs, unrecognized context, or missing facts that can change coverage | Ask a short clarifying question. Do not describe uncertainty as proof that the topic is excluded. |
| Supported topic but insufficient eligible evidence | Keep the domain/scope finding separate from the evidence gap. Ask for needed facts, explain the evidence limit, or refer; do not invent an answer. |

Valid primary/scope pairs are labor/fully_supported, consumer/fully_supported, mixed/fully_supported, mixed/partially_supported, and out_of_scope/unsupported. Other pairs must clarify or otherwise block substantive answering. Passing the two class thresholds is insufficient when the system cannot reliably identify the components of a mixed question. Until a component/topic mapping is supported, clarify rather than guess the allowed part.

Scope-changing facts include the employment category, who owes a refund and for what, the kind of contract, or who made an unexplained charge. Ask only for facts needed to resolve the uncertainty; avoid collecting names, IDs, account numbers or other unnecessary personal details. For the 20 clarification tests, a generic refusal or an irrelevant follow-up is a failure. A relevant question asks for the missing fact recorded in the benchmark, allowing equivalent wording. If relevance is assessed by AI, disclose the evaluator and retain the decision evidence; do not call that human validation.

Readable typos, word order, punctuation and code-switching alone are not reasons to declare a question out of scope. Preserve the original input. Any normalization or translation must be recorded as a derived value, never replace the original question silently, and must not introduce deciding facts.

## Confidence selection

Do not invent a confidence cutoff such as 70% or 80% before measuring the models. A displayed probability is not automatically reliable.

Fit/calibrate each model using training data only, with leakage groups kept together within internal folds. Compare settings and choose primary/scope confidence thresholds using the 102-row validation partition. Record the calibration method, threshold search, selected thresholds and validation results. Jointly assess the unsupported-admission and routing-coverage targets. If no configuration meets both, report that failure and continue development; do not lower a target silently or claim that universal abstention passes.

Explicit missing-context and valid-pair checks apply even when confidence is high. Final thresholds and the complete routing policy must be fixed before opening the synthetic test results. Calibration and threshold fitting must not use test labels.

## Data-use rules

| Data | Allowed use |
|---|---|
| Frozen reviewed seed: 459 training rows | Fit preprocessing, vectorizers, models and training-only grouped calibration. |
| Frozen reviewed seed: 102 validation rows | Compare models, features, thresholds, coverage and calibration choices. |
| Frozen reviewed seed: 100 synthetic test rows | Evaluate the selected fixed pipeline after development choices are recorded. Do not fit or tune on these rows. This test shares synthetic origins with training and is not an independent human gold set. |
| AI-reviewed general set: 100 rows | Development evaluation and error analysis. Excluded from fitting model weights and preprocessing. |
| AI-reviewed typing set: 100 rows | Development stress testing: 80 classifiable rows and 20 clarification cases. Excluded from fitting. Keep the five variants of each scenario together. |
| Fresh independent human-written/labeled holdout | Still outstanding for the project's formal final evaluation requirement. Lock before using it for final performance claims. |

The owner intends revisions during testing, so the new 200 AI-reviewed questions are development benchmarks. Their results may inform error analysis and development changes before the 100-row synthetic test is opened. Record changes and re-evaluate them on the validation partition. Do not later describe the development benchmarks as untouched final tests. Their shared AI origin, limited scenario count and unestablished semantic independence remain disclosed.

Only question text may supply the classifier's main text features. IDs, labels, topics, referrals, original splits, author names, reviewer decisions and review notes must not become input features. Fit vocabularies and preprocessing statistics on training rows only. Use whole leakage groups for any internal cross-validation. Keep excluded seed variants excluded.

## Reporting and acceptance

Report primary and scope confusion matrices; macro and per-class precision, recall and F1; English and Taglish breakdowns; calibration; coverage; unsupported admission; partial-support errors; and clarification behavior. Report the two AI benchmarks separately from seed validation and synthetic test results. For typing, show both row and scenario-family results and the clear/noisy variants; do not treat five siblings as five independent situations.

The initial targets are development acceptance criteria for a classifier candidate. They do not approve the legal assistant for release. Retrieval evidence, citation correctness, legal-source freshness, excluded-topic handling and required legal-professional review remain separate system-level checks.

## Approval record

- Proposed by: Codex, 17 October 2026.
- Project-owner confirmation: recorded 17 October 2026; exploratory training/evaluation authorized, with measured results and test explanations requested.
- Team/adviser approval required by the existing final-evaluation plan: not recorded.
- Numeric production confidence thresholds: not approved. The repaired v1.4.0 candidate selected primary 0.80 / scope 0.85. Development targets pass, but opened-set regression routing coverage is 69% versus 70%; the cutoffs remain experimental.
- Independent human holdout: not yet supplied.
- Deployment: not authorized; a passing classifier score alone does not enable legal answering.

Machine-readable targets and approval status: [evaluation_policy.json](C:/IA/dataset/pipelines/item10/evaluation_policy.json). Exploratory training is an explicitly authorized exception to the older plan's pre-training human-gold gate; it does not claim that gate is satisfied. The frozen seed and AI-reviewed benchmark manifests remain unchanged.

Exploratory results and tests: [accuracy report](C:/IA/outputs/item10-classifier-v1.3.1/ACCURACY_REPORT.md). After development and software checks passed, the 100-row synthetic test was evaluated once on frozen v1.3.1. It scored 95/100 but failed partial-support recall. That original model/result remains frozen. The owner subsequently authorized a new version to repair dropped concerns. Its old-test replay is explicitly development regression, and renewed final claims require a fresh independent holdout.


The improved experiment also uses 42 existing project taxonomy definitions and atomic derivatives from the 459 training parents. This additional derived layer is disclosed, not independently human reviewed. AI-authored scope constraints and logged preprocessing changes informed by development analysis are part of the measured pipeline. The 200 AI development questions and the synthetic test do not fit model weights, vocabulary, calibration, or thresholds. Targets remain unchanged.


## Owner-authorized partial-support repair

The owner explicitly requested implementation of the clause-handling fix after the original synthetic test was inspected. v1.4.0 preserves the parent package and source question data, inherits its classifier configuration, recalibrates on training-only grouped folds and selects thresholds on validation only. Inspected old-test examples informed preprocessing repair, not fitted weights or calibration. The original test is now regression-only, and both final-test entry points reject calling it fresh. Partial-support recall improves from 7/11 to 11/11 with no new classification regressions on that set; its 69% decisive coverage still misses 70%. All numeric targets remain unchanged. [Repair report](C:/IA/outputs/item10-classifier-v1.4.0/PARTIAL_SUPPORT_FIX.md).
