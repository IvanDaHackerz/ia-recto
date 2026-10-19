# Item 8 — BetterGov scope filtering

This pipeline turns the 114,340-record BetterGov collection into a much smaller **human review queue** for the Recto & Co. Legal MVP.

Current downstream role: these candidates are possible future source acquisitions. They are not classifier training questions, they are not automatically included in the Item 11 search index, and they cannot be passed to the answer-generating LLM until individually verified and promoted through the canonical-source process.

It does not promote BetterGov material into the verified legal knowledge base. Every selected row is marked `unverified_discovery`, `discovery_only`, `answer_eligible=false`, and `needs_official_source_verification=true`.

## What the filter does

1. Reads metadata from `consolidated.parquet` without loading document bodies into the output.
2. Removes jurisprudence and constitutions and keeps only statute/executive records.
3. Applies the approved MVP date, topic, citation, and legal-relationship rules.
4. Uses BetterGov's enriched Republic Act metadata where available. For other allowed sources, it reads at most 120,000 characters from the corresponding Markdown document solely to score relevance.
5. Flags excluded or mixed topics for boundary review instead of silently accepting them.
6. Removes records that match one of the 20 canonical documents.
7. Suppresses same-year, same-title duplicates.
8. Writes candidate metadata and review fields only; source legal text is not copied into Item 8 outputs.

## Run

```powershell
& .\dataset\pipelines\item8\run_item8.ps1
```

## Outputs

- `candidate_documents.jsonl` and `candidate_documents.parquet` — machine-readable candidate metadata
- `candidate_review_queue.csv` — the main human triage queue
- `canonical_matches.csv` — BetterGov records already represented in the canonical collection
- `internal_duplicates.csv` — duplicate candidates suppressed by the filter
- `missing_markdown.csv` — expected discovery files that could not be read
- `filter_summary.json` — counts, topic distribution, and safety assertions
- `validation_report.json` — repeatable validation result

Passing Item 8 validation means the filtering outputs are structurally consistent and safely gated. It does **not** mean the candidate documents are current, official, in scope, or suitable for answering users. Those decisions require human review and official-source verification.

## Current validated run

The 29 September 2026 run screened 114,340 BetterGov records and produced 182 candidates: 163 predicted labor, seven predicted consumer, and 12 predicted mixed-domain records. It removed nine matches to the canonical collection and one internal duplicate. The queue contains four medium-priority, 53 low-priority, and 125 boundary-review records. Validation passed with zero errors, and no expected Markdown file was missing.
