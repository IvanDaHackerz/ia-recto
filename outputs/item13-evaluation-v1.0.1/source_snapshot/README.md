# Item 13 — offline system evaluation

This stage connects the existing classifier v1.5.5, retrieval v1.2.4 and verifier v1.0.2 to a repeatable development evaluator. It does not call an LLM, retrain the model, refresh current law, connect the UI or authorize deployment.

## Data and protocol

The versioned run contains **291 AI-authored development cases**: the same 100 general questions, 100 typing/clarification questions and 67 retrieval cases, plus 24 new system questions across eight three-variant families. The new cases cover supported/partial mixed concerns, excluded subjects, missing employment context and final-pay/COE evidence gaps. English, Taglish and informal wording variants stay together.

The 24 system cases are development material, not independent human gold. Existing inspected data remain development too. Expected legal provision IDs are checked against the eligible index before any inference; no ineligible authority is silently promoted. General/typing questions have classification/scope annotations but no provision-level relevance judgments, so their retrieval relevance remains unjudged.

`prepare()` writes cases, grouping, source hashes, protocol and code hashes before constructing the runtime. Repair v1.0.1 reuses all 291 parent case bytes and screening targets unchanged; a changed binding or target is rejected before output creation. `run()` refuses modified inputs/code/sources and previously started runs. The runtime receives only question text. Expected domain, labels, concerns and provision IDs are used only after inference for scoring. Diagnostic excerpts select the first retrieved candidate; relevance labels never choose that candidate.

The protocol executes development only. It rejects a request to relabel these cases as a final test. `check_independent_intake.py` validates future independently supplied questions without executing the model or opening a final evaluation. The existing 100-row human intake remains blank. Independent final criteria, completed input and required review/acceptance are still pending.

## What is measured

- Classification: labels on every labeled row, including routing deferrals; confusion matrices, per-class precision/recall/F1 and macro F1. Macro F1 lists the represented true labels in each stratum.
- Confidence: label-probability calibration, 10-bin ECE, multiclass Brier score and negative log likelihood. These are not probabilities that a legal answer is correct.
- Routing: decisive coverage, clarification relevance, supported routing deferrals, unsupported routing admission and expected domain/exclusion coverage.
- Retrieval: known-relevant Hit@1/5, MRR@5 and known-relevant Recall@5 on the 56 judged retrieval cases. Relevance labels are partial; an unlisted hit is unjudged rather than proven irrelevant.
- Mixed concerns: independent explicit concern/anchor/evidence expectations on the 24 new cases. A supported topic with missing evidence is distinct from an excluded topic.
- Citations: exact full-source quotation/provenance checks on first-candidate excerpt round trips. A correct quotation alone does not prove relevance or legal support.
- Current guidance: actual evidence-gate coverage and blocking reasons. Zero permitted current-guidance candidates is reported as a limitation.

Rates include numerator, denominator and family-cluster bootstrap intervals with a fixed seed and 2,000 replicates. They describe correlated AI development material; they do not establish population accuracy or account for generator bias. Constant outcomes produce degenerate bootstrap intervals, which cannot rule out unseen failures. Results are separated by source suite, language, typing variation and topic.

Classifier screens retain the owner-authorized Item 10 targets. Additional retrieval/system screens are AI-proposed development criteria, not formal adviser acceptance. Results are retained even if a screen fails; failures belong in the error log. Inspecting or fixing a case does not turn it into an untouched final holdout.

## Commands

Use the existing `C:/IA/.venv-item10/` Python environment. No new dependency or model download is needed.

```powershell
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item13/build_evaluation.py --output C:/IA/outputs/<new-evaluation-version>
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item13/runner.py --output C:/IA/tmp/<new-development-run> --prepare-only
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item13/runner.py --output C:/IA/tmp/<prepared-development-run> --run-prepared
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item13/test_evaluation.py
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item13/check_independent_intake.py --input C:/IA/outputs/pre-item12-repair-2026-10-17/human_gold_intake.jsonl --output C:/IA/tmp/<new-intake-report>.json
```

The blank intake command intentionally fails validation; it does not supply independent questions. New run directories are required. `build_evaluation.py` adds software tests, parent/source preservation, schemas, report, plots and artifact hashes. `runner.py` alone writes the frozen cases, prediction log, metrics, CSV and error log.

## Future generated-answer scoring

`answer_evaluation.py` can score externally supplied structured drafts against separately supplied operator-managed legal review records. It makes no LLM calls. Reviews must bind the exact answer, original question and protocol hash; every draft claim needs exactly one finding. Missing or partial reviews do not count as supported claims. Normal scoring rejects software fixtures. Reviewer identity/credentials remain an external trust boundary; self-attestation is not machine authentication.

```powershell
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item13/answer_evaluation.py --cases C:/IA/outputs/item13-evaluation-v1.0.1/cases.jsonl --protocol C:/IA/outputs/item13-evaluation-v1.0.1/protocol.json --answers C:/IA/tmp/actual-drafts.jsonl --reviews C:/IA/tmp/operator-legal-reviews.jsonl --output C:/IA/tmp/<new-answer-metrics>.json
```

The schemas in the packet specify provider/model/prompt/timestamp provenance, the Item 12 draft contract and claim-level support, qualification and relevance findings. The score describes raw supplied drafts; it cannot override Item 12 source/display gates or authorize answering. Review files must not be model-controlled. An LLM drafter and resolved source/currentness conditions are still needed for actual generated-answer evaluation.

No actual generated answers or legal reviews are supplied by this build. Legal-answer accuracy, unsupported-claim rate and false declines on verified-current answerable questions remain unavailable, not zero or perfect. Supported routing deferrals are a separate diagnostic. A licensed Philippine legal professional's review of selected answers, fresh independent question/label collection and formal acceptance remain pending.

## Artifacts

[Evaluation report](C:/IA/outputs/item13-evaluation-v1.0.1/EVALUATION_REPORT.md), [metrics](C:/IA/outputs/item13-evaluation-v1.0.1/metrics.json), [per-question table](C:/IA/outputs/item13-evaluation-v1.0.1/results.csv) and [error log](C:/IA/outputs/item13-evaluation-v1.0.1/error_log.jsonl). JSONL preserves original text; CSV neutralizes formula-like text cells for spreadsheet viewing. The original legal sources, frozen reviewed data and evaluated parent packages remain unchanged.
