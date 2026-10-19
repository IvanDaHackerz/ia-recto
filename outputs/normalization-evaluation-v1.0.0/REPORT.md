# Conditional normalization development comparison

100 existing AI development questions, each clear and synthetically noisy: 200 inputs / 400 pipeline executions. Not independent human gold.

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
| noisy | Topic accuracy | 84.2% | 66.3% |
| noisy | Topic macro F1 | 84.3% | 76.7% |
| noisy | Coverage accuracy | 83.2% | 65.3% |
| noisy | Coverage macro F1 | 78.7% | 70.9% |
| noisy | Partial-support recall | 60.0% | 53.3% |
| noisy | Out-of-scope recall | 100.0% | 55.0% |
| noisy | Route match | 62.0% | 60.0% |
| noisy | Known-relevant Hit@5 | 47.1% | 58.8% |
| all | Topic accuracy | 92.1% | 83.2% |
| all | Topic macro F1 | 92.1% | 89.3% |
| all | Coverage accuracy | 91.6% | 82.6% |
| all | Coverage macro F1 | 89.4% | 86.7% |
| all | Partial-support recall | 80.0% | 76.7% |
| all | Out-of-scope recall | 100.0% | 77.5% |
| all | Route match | 81.0% | 80.0% |
| all | Known-relevant Hit@5 | 73.5% | 79.4% |

LLM requests: 66 (clear 4; noisy 62).
Provider usage: 46127 input / 8576 output tokens including reasoning. Estimated cost: $0.012065; usage complete: True.

Accepted rewrites audited by Codex AI: 34. Verdicts: {'equivalent': 28, 'meaning_changed': 5, 'uncertain': 1}. This is not an independent human meaning-change rate.

## Paired uncertainty

Differences are conditional minus baseline. Intervals resample recorded families, keeping clear/noisy variants paired. These describe this development sample.
- clear topic accuracy difference: +0.0 percentage points; 95% grouped interval +0.0 to +0.0.
- noisy topic accuracy difference: -17.9 percentage points; 95% grouped interval -29.5 to -6.3.
- all topic accuracy difference: -8.9 percentage points; 95% grouped interval -14.7 to -3.2.

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
