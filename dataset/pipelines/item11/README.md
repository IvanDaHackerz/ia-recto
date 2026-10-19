# Item 11 — offline legal retrieval

Current implementation binding: **v1.2.5** for classifier **v1.5.6**. Source membership, vectors, ranking code and benchmark cases are identical to v1.2.4; 42 software checks pass. Performance scoring is deferred. [Binding report](C:/IA/outputs/item11-retrieval-v1.2.5/RETRIEVAL_REPORT.md). The results below describe previously evaluated versions.

Last evaluated status: classifier **v1.5.5**, retrieval **v1.2.4**. The focused Item 13 repair passes 53 classifier and 42 retrieval tests and all 11 system development screens. Existing retrieval positives remain 56/56; the index preserves 362 chunks / 353 provisions / 12 documents and identical cached vectors. Labor-only ranking expansion repairs delayed-wage and overtime misses; original wording and qualifiers remain. [Current repair comparison](C:/IA/outputs/item13-accuracy-repair-v1.0.0/REPAIR_REPORT.md). Older results below are historical; use [CURRENT_ARTIFACTS.json](C:/IA/CURRENT_ARTIFACTS.json) for active versions. Current guidance and deployment remain disabled.


Historical v1.1.2 results, retained for provenance: [item11-retrieval-v1.1.2](C:/IA/outputs/item11-retrieval-v1.1.2/index_manifest.json). Current results: [v1.2.4 report](C:/IA/outputs/item11-retrieval-v1.2.4/RETRIEVAL_REPORT.md).

The filtered index contains **365 chunks, 356 provisions and 12 canonical documents**. The original Item 7 files remain unchanged: 55 of their 420 flagged-eligible chunks are additionally quarantined for specialized scope or extraction anomalies. The full audit is preserved. This is an offline retrieval pipeline; it does not generate legal answers or authorize deployment.

BM25 is the measured development default. Local multilingual semantic search and reciprocal-rank-fusion hybrid search are also available. BM25 retrieved a judged-relevant provision in the top five for **50/56 positive queries (89.3%)**; semantic search scored 42/56 and hybrid 48/56. The queries and partial relevance labels are AI-authored development material across 28 English/Taglish scenario families. Eleven negative controls and 34 software tests passed. This is not independent human or legal-professional validation.

[Full methods, metrics, source gates, limitations and figures](C:/IA/outputs/item11-retrieval-v1.1.2/RETRIEVAL_REPORT.md). [Retrieval card](C:/IA/outputs/item11-retrieval-v1.1.2/RETRIEVAL_CARD.json).

## Entry points

- `build_index.py`: validate source relationships, apply eligibility/quarantine gates, preserve original metadata and build token-bounded semantic windows/vectors in a new directory. Existing builds are not overwritten.
- `retrieval.py`: manual domain-filtered search, or component retrieval through the current pinned classifier. Classifier clarification/referral decisions do not search; excluded portions of partial questions do not enter queries.
- `create_benchmark.py`: author or reuse the disclosed source-grounded AI development queries with expected provision IDs and provenance.
- `benchmark_retrieval.py`: compare the three fixed methods using Hit@k, known-relevant Recall@k, MRR, nDCG, family bootstrap intervals, language strata and negative controls; record seven classifier integration cases.
- `test_retrieval.py`: check provenance, fail-closed filters, exact text/citations/locators, semantic-window completeness, ranking, interface behavior and classifier isolation.
- `write_report.py`: write the report, retrieval card, quarantine/error summaries, inventory addendum and artifact hashes.

## Run

Use the existing Python 3.12 environment at `C:/IA/.venv-item10/`. `requirements.txt` records the direct packages; each build includes an exact `requirements.lock.txt`. The already downloaded, checksum-recorded local model is needed for semantic rebuilding; ordinary operations never download model weights or send project text to an API.

```powershell
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item11/retrieval.py --index C:/IA/outputs/item11-retrieval-v1.2.4 --domain consumer --query "The cashier charged more than the displayed price."
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item11/retrieval.py --index C:/IA/outputs/item11-retrieval-v1.2.4 --classifier C:/IA/outputs/item10-classifier-v1.5.5/classifier.joblib --query "A store refuses my warranty. I have a complaint about my seafarer deployment."
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item11/test_retrieval.py --index C:/IA/outputs/item11-retrieval-v1.2.4
```

For manual search, `--domain` is required; `--topic` may repeat for supported topics within that domain. Invalid/excluded/empty filters do not silently broaden the search. `--method bm25|semantic|hybrid` overrides the recorded default. In classifier mode omit manual `--domain`/`--topic` filters; the classifier supplies separate supported components. Load only the trusted project classifier package.

Build a new version:

```powershell
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item11/build_index.py --output-dir C:/IA/outputs/<new-index-directory> --default-method bm25 --selection-evidence C:/IA/outputs/item11-retrieval-v1.0.2/benchmark_metrics.json
```

`--reuse-vectors-from C:/IA/outputs/item11-retrieval-v1.2.4` reuses only checksum-verified exact-text vectors under the same model. Benchmark reuse must be declared with `--reuse-queries-from`; rescoring these questions remains development work. Output source files are provenance snapshots; executable entry points retain their project-relative layout. Source, raw canonical file, model manifest or runtime changes require a fresh index build. Old evaluated versions remain preserved; use their snapshots to reproduce an old runtime rather than pairing them with current code.

## Boundaries and next step

Each result preserves the exact source chunk, full eligible provision, citation, former locator labels, document ID, official/retrieval URL, page or source-character locator, legal status, quality flags, recorded check date, freshness rule and related-authority relationships. Similarity/ranking scores are not answer confidence. Every response has `answer_generation_allowed=false` and `deployment_allowed=false`.

The recorded legal-status date remains **29 September 2026**; this build did not refresh current law. Final pay/COE has no eligible evidence and returns a gap. Main thirteenth-month entitlement and current DTI procedure have unresolved authority/extraction limitations. Nonzero topic counts do not prove sufficient substantive support.

The next development stage is **Item 12: citation/proposition verification, source freshness, related-authority checks and evidence-sufficiency/decline behavior**. Classifier independent evaluation and its known coverage limitation remain separate open work. The current interface stays a demonstration; no live answering was enabled.
