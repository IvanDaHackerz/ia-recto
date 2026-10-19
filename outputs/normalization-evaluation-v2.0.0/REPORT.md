# Conditional normalization development comparison

167 existing AI development questions, each clear and synthetically noisy: 424 inputs / 848 pipeline executions. Not independent human gold.

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
| noisy | Topic accuracy | 99.6% | 99.2% |
| noisy | Topic macro F1 | 99.4% | 99.4% |
| noisy | Coverage accuracy | 99.6% | 99.2% |
| noisy | Coverage macro F1 | 99.4% | 99.4% |
| noisy | Partial-support recall | 100.0% | 100.0% |
| noisy | Out-of-scope recall | 100.0% | 97.5% |
| noisy | Route match | 97.3% | 97.7% |
| noisy | Known-relevant Hit@5 | 89.8% | 89.8% |
| all | Topic accuracy | 99.8% | 99.5% |
| all | Topic macro F1 | 99.7% | 99.7% |
| all | Coverage accuracy | 99.8% | 99.5% |
| all | Coverage macro F1 | 99.7% | 99.7% |
| all | Partial-support recall | 100.0% | 100.0% |
| all | Out-of-scope recall | 100.0% | 98.8% |
| all | Route match | 98.3% | 98.6% |
| all | Known-relevant Hit@5 | 94.0% | 94.0% |

LLM requests: 6 (clear 0; noisy 6).
Provider usage: 5336 input / 903 output tokens including reasoning. Estimated cost: $0.001342; usage complete: True.

Accepted rewrites audited by Codex AI: 2. Verdicts: {'equivalent': 2}. This is not an independent human meaning-change rate.

## Paired uncertainty

Differences are conditional minus baseline. Intervals resample recorded families, keeping clear/noisy variants paired. These describe this development sample.
- clear topic accuracy difference: +0.0 percentage points; 95% grouped interval +0.0 to +0.0.
- noisy topic accuracy difference: -0.4 percentage points; 95% grouped interval -1.3 to +0.0.
- all topic accuracy difference: -0.2 percentage points; 95% grouped interval -0.8 to +0.0.

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
