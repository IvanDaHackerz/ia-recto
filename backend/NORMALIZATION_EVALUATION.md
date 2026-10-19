# Baseline versus conditional-normalization evaluation

The runner compares the actual pinned classifier/retriever/verifier with and without the conditional wording layer. This is a disclosed AI development study, not independent human gold or legal-answer acceptance.

## Frozen design

- 100 existing base questions from 100 recorded scenario families, selected before inference by fixed quotas: 24 labor, 24 consumer, 12 fully supported mixed, 15 partially supported mixed, 20 out of scope, and 5 clarification cases.
- Each base question has its existing clear form and one deterministic synthetic noisy form: 200 inputs, 400 pipeline executions.
- Five perturbation styles, 20 noisy forms each: missing vowels, phonetic substitutions, repeated letters, joined words, and mixed typing. A reversible character ledger records each source-to-noisy change. No clauses, amounts or negation are deliberately deleted; joined words can still obscure facts and cause a safe clarification.
- Existing expected labels, routing and provision judgments are copied without consulting new predictions. Only question text enters either inference path. The LLM never receives the clear reference, expected labels or relevant provision IDs.
- Previously inspected source families remain development material. Recorded family IDs support grouped uncertainty estimates; they do not establish semantic independence across suites.
- The existing runtime normalizer makes at most one LLM request per input. Evaluation stops at 200 calls or $0.50 of reported-token estimated cost, or after five consecutive provider-unavailable results. Provider failures are retained as failures/abstentions, not silently retried.

The source case packet is `outputs/item13-evaluation-v1.0.1/cases.jsonl`. Selection prioritizes one question from each retrieval family, one from each system family, four missing-context typing families, then general questions to fill the quotas. The initial composition is 39 retrieval, 8 system, 4 typing and 49 general base questions. It contains 190 labeled inputs and 10 clarification inputs.

## Commands

Use a new output directory for each study. Never overwrite a started run or tune the frozen runtime while it is running.

```powershell
& .\.venv-item10\Scripts\python.exe -m unittest backend.test_normalization_evaluation backend.test_normalization backend.test_terminal_test -v
& .\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --prepare-only --output outputs/normalization-evaluation-v1.0.0
& .\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --run-prepared --output outputs/normalization-evaluation-v1.0.0
```

Preparation freezes case bytes, expected results, generation seed, prices, model identity, input hashes, runtime source hashes and artifact-manifest hashes. `--run-prepared` requires that freeze to match. Baseline-first and normalized-first execution alternate to reduce a fixed ordering effect; no question trains either path. Live execution needs network access to Together.

After inference, inspect `semantic_review_queue.jsonl` before opening the performance results. It shows the reference, typed question and accepted interpretation, excluding outcome labels and classifier results. For each accepted rewrite, write a record in `semantic_reviews.jsonl` containing `case_id`, `verdict` (`equivalent`, `meaning_changed` or `uncertain`) and a concrete `reason`. The initial audit is authored by Codex AI and disclosed as such; it is not independent human validation. Do not count a local validator's rejection as an observed meaning change or treat its acceptance as proof of equivalence.

```powershell
& .\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --finalize --output outputs/normalization-evaluation-v1.0.0
```

Finalization requires every accepted rewrite to have that audit, checks frozen inputs and completed observation hashes, and preserves finalized reports against overwriting.

## Outputs and interpretation

- `REPORT.md`: readable comparison with paired uncertainty and limitations.
- `metrics.json`: per-class precision/recall/F1, accuracy, confusion matrices, label-confidence bins/ECE, partial-support and out-of-scope recall, route/domain match, judged retrieval, latency, usage and estimated cost, including clear/noisy/style breakdowns.
- `results.csv`: every question side by side, expected/actual labels and routes, label confidences, retrieval checks, time, token usage, normalization status, semantic verdict and issues. CSV formula prefixes are escaped.
- `error_log.jsonl`: either-path failures and semantic flags with the recorded packets.
- `observations.jsonl`: immutable completed observations; question hashes, candidate IDs/scores and evidence-gate reasons are retained without duplicating full legal texts.
- Frozen cases, protocol, provenance, execution timestamps and checksum records.

All labeled inputs stay in accuracy/recall denominators, including normalization abstentions. An unresolved wording interpretation is `__abstain__`, not an invented out-of-scope label. Prediction-only confidence calibration reports its smaller denominator explicitly. Clarification cases are evaluated by route rather than forced domain labels. A correct label with an incorrect route is reported separately.

Known-relevant retrieval is scored only on existing judged cases/concerns, per supported component with ranks reset and limited to five. Other returned provisions remain unjudged. Full-text legal correctness and currentness are not inferred from candidate retrieval. Family-cluster bootstrap resamples clear/noisy pairs together; intervals describe this synthetic development sample, not population accuracy. The AI semantic-change fraction is not an independently measured meaning-change rate.

Repeated evaluation on cases used to guide a fix is a regression comparison, not fresh validation. Preserve the first run, freeze the next revision separately, and use fresh cases to assess generalization. No website integration, classifier tuning, legal-answer generation or deployment approval is performed by this runner.

## Repaired follow-up

The initial comparison is preserved as v1.0.0. The v2.1.0 normalizer's follow-up selects all 67 recorded families absent from that initial selection, yielding 134 inputs / 268 pipeline executions:

```powershell
& .\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --prepare-only --fresh-after outputs/normalization-evaluation-v1.0.0 --output outputs/normalization-evaluation-v1.1.0
& .\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --run-prepared --output outputs/normalization-evaluation-v1.1.0
```

Those families are not an independent holdout for the classifier: they already existed in the project's AI development material. They are not selected based on their new predictions. The follow-up retains the same grading definitions, counts abstentions in label metrics, and separates AI semantic review from classifier correctness. It has only three partial-support base questions and no judged retrieval provisions; interpret partial-support results cautiously and leave retrieval-relevance metrics unavailable. Do not compare absolute percentages across these different case sets as if they were the same test.

Archived source snapshots in each completed packet preserve its runner and runtime code. Global source files evolve between versions; the original packet's recorded hashes and snapshots describe its historical code. Restoring that frozen code is necessary to rerun its runtime-integrity check. The completed packet checksums and archived sources can be verified without replacing the current code.

## Diagnostic repair and expanded regression suite

The v2.2.1 normalizer adds opt-in development diagnostics for the proposed wording and validation failure. Normal terminal use does not retain rejected proposals. Diagnostic wording is never substituted for an accepted effective question. Batch evaluations explicitly enable this opt-in; provider headers, credentials and response bodies are not logged.

`backend.diagnose_normalization` freezes and replays the eight v1.1.0 rejections, the uncertain future-inflection example and the user-supplied payment reproduction. Replayed provider responses are new observations, not reconstructions of the discarded historical candidates. The ten-question payload and subsequent larger synthetic export received explicit owner approval after automatic approval review requested it.

The repair suite contains all 334 earlier input forms plus 90 newly derived noisy forms across all 18 recorded partial-support families: 424 forms from 167 reused base questions, 848 baseline/conditional pipeline executions. Each partial-support family has all five noise profiles in the additional set. Source expectations and partial relevance judgments remain unchanged. This enriches partial-support testing; it does not create 90 independent scenarios or a representative real-world accuracy sample. Family bootstrap keeps correlated variants together.

```powershell
& .\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --prepare-only --suite repair --output outputs/NEW_REPAIR_RUN
& .\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --run-prepared --output outputs/NEW_REPAIR_RUN
```

Use a new directory, audit all accepted rewrites before generating metrics, then finalize as above. The maximum calls equal the frozen input count; the reported-token cost stop remains $0.50. The prepared v1.2.0 packet was superseded before inference after correcting its base-question count; v1.2.1 has byte-identical question payloads and the final frozen runtime. No started observations were overwritten.

## Local concern-detection repair

The v2.0.0 comparison replays those same 424 question bytes with classifier v1.5.10, retrieval v1.2.7, verifier v1.0.5 and normalizer v3.0.0. Both paths now include the classifier's local spelling features. Historical-versus-current claims therefore use matched earlier observations; they must not be described as an isolated benefit from the LLM. Weights, calibration, thresholds and training membership are preserved. The learned calibration reconstruction and 724-word training-vocabulary preservation checks pass.

Current results: [repair report](../outputs/normalization-repair-v2.0.0/REPORT.md). The final inspection follow-up changed only the question shown after a rejected payment rewrite, plus its software test, after the frozen run. Frozen source bytes are archived; the global source-hash check correctly notices that later change. Classifier decisions, rewrite acceptance, routing, retrieval and scored metrics were unchanged. The final clarification check is a recorded-provider replay, not a new live evaluation.


## Reusing the matched local freeze

The completed current-stack run is `outputs/normalization-evaluation-v3.0.1`. It reuses the exact 436-form local packet, including its disclosed relevance-judgment correction, without modifying questions or labels. Its 171 families include the 12 joined-concern regressions. The older initial-suite quota selection does not apply.

For a future newly authorized replay, use a new output directory:

```powershell
.\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --prepare-only --output outputs/NEW_CURRENT_COMPARISON --frozen-cases outputs/local-pipeline-cases-v1.1.0 --baseline-report outputs/local-pipeline-evaluation-v1.1.0
.\.venv-item10\Scripts\python.exe -m backend.evaluate_normalization --run-prepared --output outputs/NEW_CURRENT_COMPARISON
```

Preparation verifies the prior local packet and current bindings, then freezes the gate's provider-export ceiling. Both inference paths still replay every input with question text only. A bounded provider blocks unplanned question hashes and requests above the declared maximum before export; reaching the call maximum does not prevent later bypassed cases from being scored. The actual completed run made five planned calls, zero clear-input calls and no retries. Complete the semantic queue audit before finalizing as usual.

The unexecuted v3.0.0 preparation is retained as superseded; only v3.0.1 has current-stack inference observations. [Results and limitations](../outputs/current-stack-validation-v1.0.0/REPORT.md) separate measured development performance from fresh human intake and explanation approvals.
