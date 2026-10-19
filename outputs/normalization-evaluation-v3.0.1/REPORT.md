# Conditional normalization development comparison

171 AI development wording families: 436 clear/noisy inputs / 872 paired pipeline executions. Includes only the forms declared in the frozen protocol; not independent human gold.

| Group | Measure | Baseline | Conditional LLM |
|---|---|---:|---:|
| clear | Topic accuracy | 100.0% | 100.0% |
| clear | Topic macro F1 | 100.0% | 100.0% |
| clear | Coverage accuracy | 100.0% | 100.0% |
| clear | Coverage macro F1 | 100.0% | 100.0% |
| clear | Partial-support recall | 100.0% | 100.0% |
| clear | Out-of-scope recall | 100.0% | 100.0% |
| clear | Route match | 100.0% | 100.0% |
| clear | Known-relevant Hit@5 | 100.0% | 100.0% |
| noisy | Topic accuracy | 100.0% | 100.0% |
| noisy | Topic macro F1 | 100.0% | 100.0% |
| noisy | Coverage accuracy | 100.0% | 100.0% |
| noisy | Coverage macro F1 | 100.0% | 100.0% |
| noisy | Partial-support recall | 100.0% | 100.0% |
| noisy | Out-of-scope recall | 100.0% | 100.0% |
| noisy | Route match | 99.2% | 100.0% |
| noisy | Known-relevant Hit@5 | 100.0% | 100.0% |
| all | Topic accuracy | 100.0% | 100.0% |
| all | Topic macro F1 | 100.0% | 100.0% |
| all | Coverage accuracy | 100.0% | 100.0% |
| all | Coverage macro F1 | 100.0% | 100.0% |
| all | Partial-support recall | 100.0% | 100.0% |
| all | Out-of-scope recall | 100.0% | 100.0% |
| all | Route match | 99.5% | 100.0% |
| all | Known-relevant Hit@5 | 100.0% | 100.0% |

LLM requests: 5 (clear 0; noisy 5).
Provider usage: 4435 input / 729 output tokens including reasoning. Estimated cost: $0.001103; usage complete: True.

Accepted rewrites audited by Codex AI: 3. Verdicts: {'equivalent': 3}. This is not an independent human meaning-change rate.

## Paired uncertainty

Differences are conditional minus baseline. Intervals resample recorded families, keeping clear/noisy variants paired. These describe this development sample.
- clear topic accuracy difference: +0.0 percentage points; 95% grouped interval +0.0 to +0.0.
- noisy topic accuracy difference: +0.0 percentage points; 95% grouped interval +0.0 to +0.0.
- all topic accuracy difference: +0.0 percentage points; 95% grouped interval +0.0 to +0.0.

## Files and interpretation

`results.csv` contains every question side by side. `error_log.jsonl` includes either-path failures and semantic flags. `metrics.json` provides per-class precision/recall/F1, confusion matrices, label-confidence bins, latency, noise-profile results, denominators and paired intervals.

- Reused AI-authored cases and synthetic perturbations; not independent human gold or real typing prevalence.
- Noisy inputs inherit the intended source meaning. Correct clarification can be a safe deferral while reducing label accuracy.
- Abstentions remain in labeled accuracy/recall denominators and confusion columns.
- Known-relevant judgments are partial development judgments. Candidate availability alone is not relevance.
- Semantic review is AI authored and may miss changes; rejected rewrites are not counted as observed meaning changes.
- Timing includes current-guidance integrity checks and conditional API latency, excluding model startup.
- This does not evaluate generated legal answers or approve current law.

No classifier/normalizer tuning was performed during this frozen run. No website, legal-answer generation or deployment approval is granted by these results.
