# Project dataset inventory

Checked 19 October 2026. Current bindings are classifier v1.5.15, retrieval v1.3.1 and verifier v1.0.9. The fitted training membership, learned weights/calibration and source records are unchanged by this repair. The live website is integrated; source/currentness approval and deployment remain closed. Recorded-source explanations require exact citations plus a same-model automated support check and remain legally unreviewed.

The latest local replay reuses the frozen 436 AI inputs (424 earlier inputs plus 12 joined-concern regressions). Topic/coverage matches are 425/425, routes 435/436 and known-relevant Hit@5 is 93/93. The complete application replays reuse these same inputs; do not add them as new questions. The new privacy/history/grounding software fixtures are tests, not training data or independent human gold. Optional encrypted user history is private runtime state, not a dataset for training or evaluation.

The following milestone-specific counts/results are historical unless explicitly identified as current. [Current repair record](../outputs/project-repair-v1.0.0/REPORT.md).

Last evaluated classifier **v1.5.5** uses the same 459 training parents and 222 unique fitted texts. No new training questions were added. Opened-set regression accuracy is 100/100, routing coverage 92%, and partial recall 11/11. All numeric development/regression gates and 53 software tests pass. Original v1.3.1 once-unseen results remain preserved; no fresh independent holdout exists.

Last evaluated retrieval **v1.2.4** has **362 chunks / 353 provisions / 12 canonical documents** and 719 semantic windows. It additionally quarantines 58 originally flagged-eligible chunks. Its 67 AI development queries are unchanged. BM25 and actual classifier-to-retrieval each hit 56/56 positives; all 11 negative controls and 42 retrieval tests pass. These are inspected development results. [Repairs and unresolved prerequisites](C:/IA/outputs/pre-item12-repair-2026-10-17/REPAIR_REPORT.md).

The repair packet adds four AI visual-comparison final-pay proposals, 29 DTI structural candidates from 31 original records, and a 258-record source-review intake. They remain gated and are versions of existing legal material. The 100 blank human-intake records contain **zero authored questions**; they are not another dataset or human gold. Item 12 is now implemented offline; live answering remains disabled.

Item 12 adds 50 AI-authored software-development scenarios, strict draft/review contracts and verifier audit results. Current artifact-binding version v1.0.2 passes 37 software tests. These controls reuse the existing legal sources and model; they add no training examples, legal authorities or independent human questions. Simulated reviews are isolated test fixtures, rejected by normal runtime. The pre-Item-13 integration audit reuses the same 67 Item 11 cases; these are not additional questions. [Item 12 report](C:/IA/outputs/item12-verifier-v1.0.2/VERIFICATION_REPORT.md). [Pre-Item-13 audit](C:/IA/outputs/pre-item13-audit-2026-10-17/PRE_ITEM13_AUDIT.md).

Item 13 adds **24 AI-authored development questions across eight system scenario families** and evaluates them alongside the same 200 general/typing questions and 67 retrieval queries: **291 cases**, not 291 newly created questions. The repaired evaluator passes 34 software tests and all 11 unchanged development screens. The same 291 case bytes are reused; no questions are added by the repair. Formal independent/legal evaluation and actual generated-answer scoring remain pending. No training examples, legal sources or independent human questions were added. [Item 13 report](C:/IA/outputs/item13-evaluation-v1.0.1/EVALUATION_REPORT.md).

| Layer | What we have | Purpose and current status |
|---|---|---|
| BetterGov discovery corpus | 114,340 consolidated document records and 114,340 Markdown files | Broad legal-document discovery. Not automatically eligible to support answers. |
| Original / enriched corpus tables | 12,071 Republic Act records; 12,005 Republic Act records with summary/enrichment fields; 68,408 records in the separate jurisprudence table | Stored corpus tables and metadata used during exploration/filtering. These overlap the broader collection. Physical table counts can differ from the consolidated category counts. Summaries are not legal authorities; jurisprudence remains outside automatic MVP answering. |
| Authoritative-source registry | 13 source-provider records | Records authority, permitted use, verification rules, source links and check dates. |
| Canonical legal collection | 20 preserved documents: 13 labor and 7 consumer | Controlled answer-source collection. All 20 manifest files are present. Fifteen have document-level answer-candidate status; five remain restricted/historical. Candidate status alone does not make every provision answer-eligible. |
| Legal-status metadata | 20 document reviews and 18 amendment/repeal/renumbering or related legal-status relationships | Source-use and currentness rules for the canonical collection. Existing check dates remain unchanged; this inventory is not a new current-law certification. |
| Scope taxonomy and data contract | 42 topics: 21 supported and 21 excluded; 3 schemas plus controlled vocabularies and sample records | Shared definitions for documents, provisions, chunks, question labels and scope. |
| Extracted canonical documents | 20 structured document records | Canonical document metadata in JSONL/Parquet. Derived from the same 20 source documents. |
| Legal provisions | 1,928 provision records; 406 marked eligible in Item 7; 353 represented in the current Item 11 index | Structured legal text, citations, page locators, extraction metadata, scope and legal-status gates. |
| Retrieval chunks | 2,001 source chunks; 420 marked eligible in Item 7; 362 indexed by the current Item 11 index | Derived search units. Item 11 applies additional scope/quality quarantine to 58 flagged-eligible chunks. Results remain conditional retrieval candidates; live answer generation is disabled. |
| Extraction review queues | 258 unique pending provision reviews: 255 OCR and 3 text-quality records | OCR review queue is a subset of the combined human-review queue. Do not add 255 and 258. These records remain gated. |
| Filtered discovery candidates | 182 candidate documents: 163 labor, 7 consumer, 12 mixed | Possible future canonical acquisitions. All remain unverified discovery material, not answer evidence or classifier-training questions. |
| Original classifier seed | 672 synthetic questions | Original Item 9 generation, retained unchanged for provenance. CSV, JSONL and Parquet are formats of the same set. |
| Five human reviews | 5 returned workbooks covering all 672 seed questions | Original reviewer evidence preserved. Five cleaned copies and audit records capture the later owner-authorized AI cleanup; they are versions of the same five reviews. |
| Frozen reviewed classifier dataset | 661 included questions; 11 excluded variants retained separately | Current reviewed seed v1.0.0. Splits: 459 train, 102 validation, 100 synthetic test. Human review plus disclosed AI cleanup. This is derived from the original 672, not 661 additional questions. |
| Referral directory | 19 agency/referral destinations | Separate routing/contact metadata. Reviewed Item 10 version contains routing corrections; contact-verification dates were not refreshed by this task. |
| General evaluation questions | 100 AI-authored, AI-reviewed questions; 25 per primary class; 50 English and 50 Taglish | Approved by Codex for exploratory evaluation. Original draft, reviewed workbook, final CSV/JSONL and decision log retained. No human review or independent-human-gold claim. |
| Typing and clarification questions | 100 AI-authored, AI-reviewed questions across 20 scenario families; 50 English and 50 Taglish | 80 labeled examples: 20 labor, 20 consumer, 20 mixed, 20 out_of_scope. Another 20 expect clarification and have null primary/scope labels. Five related variants per family; families must stay together. |
| Derived atomic training material | 571 atomic records from the existing 459 training parents; 180 unique atomic facts, plus 42 existing taxonomy definitions = 222 fitted texts | AI-derived training layer. No extra independent human-written questions. Evaluation questions were not fitted. Scope constraints are AI-written code, not an additional question dataset. |
| Experimental classifier package | Implementation v1.5.6 plus preserved evaluated v1.5.5; 60 software tests; 19 original scope regression cases and additional fragment/component tests | Derived model/metrics artifacts. Partial recall 11/11 on opened-set regression; no fresh independent test. Original v1.3.1 test result unchanged. Regression routing coverage is 92%, passing the 70% target; live answering disabled. |
| Item 11 offline retrieval index | 362 chunks, 353 provisions, 12 existing canonical documents; 719 overlapping semantic windows; BM25, semantic and hybrid search | Derived from the same Item 7/legal sources, not additional legal documents. BM25 is selected on the AI development benchmark. Full citations, locators and conditions are preserved. |
| Item 11 additional quarantine | 58 flagged-eligible chunks covering 53 provisions | Conservative AI-authored scope/quality screens. Logs are separate from the original review queues, which remain unchanged; counts are not automatically additive to those queues. |
| Retrieval relevance benchmark | 67 AI-authored development queries: 56 positive questions / 28 families and 11 excluded-scope or evidence-gap controls | Source-text-based AI relevance judgments; no human gold claim. No classifier training questions added. Copies in index versions are versions of this same benchmark. |
| Item 12 verifier development controls | 50 AI-authored software scenarios: 4 valid-excerpt controls, 2 simulated review positives, 40 adversarial cases, 1 real currentness gate and 3 routing/evidence-gap cases | Reuses existing sources and model. Simulated approvals are test-only; no independent human questions, real legal approvals or new fitted texts. |
| Item 13 system evaluation | 291 AI development cases: the same 200 general/typing questions, the same 67 retrieval cases, plus 24 new mixed/excluded/clarification/evidence-gap questions across eight families | Frozen development protocol and versioned predictions/metrics/error log. Repaired classification 268/268 per head; explicit concern/evidence checks 39/39 pass the unchanged screen. Eleven conservative routing deferrals remain. No final independent or generated-answer accuracy claim. |
| Source repair review packet | 4 AI visual-comparison final-pay proposals; 29 DTI structural candidates replacing 31 original splits; 258 original provisions exported for review | Existing source material, not new legal authorities. All proposals remain gated pending required source review. |
| Independent human intake form | 100 blank records containing zero authored questions | Collection/validation tooling only. No human gold, human review or approval is claimed. |
| AI visual source review follow-up | 29 DTI procedure sections compared against 11 pages, plus the same 4 final-pay sections compared against 2 pages | Corrected versions of existing source material. Images/hashes retained; no new canonical authorities or human approval. Default answer eligibility remains gated. |
| Referral-contact refresh | The same 19 agencies; 36 individual fields corroborated across 15 records | Versioned AI official-source review. Four agencies lack confirmed operational fields; unverified fields withheld. Frozen directory and current classifier unchanged. |
| Audit and validation records | Source/workbook checksums, review findings and resolutions, per-question decisions, overlap screens, dataset manifests and validation reports | Provenance and reproducibility evidence. These are supporting records, not additional training examples. |
| UI demonstration fixtures | 6 scripted answer scenarios, sample conversation history and a source/referral snapshot | Frontend demonstration data only. Not real user conversations, new legal authorities or classifier-training data. |

The two new sets have 200 question records in total: 180 with classification labels and 20 clarification tests. All 200 are AI-approved for development testing, with 91 wording revisions and 2 topic-tag corrections. They are excluded from training and remain unlocked because revisions during testing are expected. The typing set has only 20 underlying scenarios, despite containing 100 rows. The AI-review stage itself produced no trained model. Subsequent exploratory experiments now have measured classifier results, listed above; no real-user question dataset or independent human-written gold set is available.

The original corpus, canonical files, Item 9 seed, five returned human workbooks and frozen Item 10 seed were preserved. Frozen-seed validation passed all 59 checks. Pending OCR and discovery-source gates remain in place.

## Locations

| Material | Location |
|---|---|
| Main discovery table | [consolidated.parquet](C:/IA/dataset/consolidated.parquet) |
| Republic Act table | [repacts.parquet](C:/IA/dataset/repacts.parquet) |
| Enriched Republic Act table | [repacts_with_summary.parquet](C:/IA/dataset/repacts_with_summary.parquet) |
| Separate jurisprudence table | [juris.parquet](C:/IA/dataset/juris.parquet) |
| Source registry | [authoritative_source_registry.csv](C:/IA/dataset/authoritative_source_registry.csv) |
| Canonical manifest | [canonical_documents.csv](C:/IA/dataset/canonical_sources/manifests/canonical_documents.csv) |
| Legal status and relationships | [legal_status_review.csv](C:/IA/dataset/canonical_sources/manifests/legal_status_review.csv), [legal_status_relationships.csv](C:/IA/dataset/canonical_sources/manifests/legal_status_relationships.csv) |
| Topic definitions | [topic_taxonomy.csv](C:/IA/dataset/data_contract/topic_taxonomy.csv) |
| Extracted documents | [documents.jsonl](C:/IA/dataset/processed/item7/documents.jsonl) |
| Provisions | [provisions.jsonl](C:/IA/dataset/processed/item7/provisions.jsonl) |
| Retrieval chunks | [retrieval_chunks.jsonl](C:/IA/dataset/processed/item7/retrieval_chunks.jsonl) |
| Combined extraction review queue | [human_review_queue.csv](C:/IA/dataset/processed/item7/human_review_queue.csv) |
| Discovery queue | [candidate_review_queue.csv](C:/IA/dataset/processed/item8/candidate_review_queue.csv) |
| Original seed | [classifier_questions.jsonl](C:/IA/dataset/processed/item9/classifier_questions.jsonl) |
| Five original review assignments | [assignment_manifest.json](C:/IA/outputs/item10-review-workbooks/assignment_manifest.json) |
| Human-review cleanup summary | [cleanup_summary.md](C:/IA/outputs/item10-review-cleaned/cleanup_summary.md) |
| Frozen reviewed seed | [README.md](C:/IA/dataset/processed/item10/reviewed_v1.0.0/README.md) |
| Current referral directory | [referral_directory.csv](C:/IA/dataset/processed/item10/reviewed_v1.0.0/referral_directory.csv) |
| AI-reviewed general questions | [evaluation_questions.jsonl](C:/IA/dataset/processed/item10/ai_reviewed_eval_v1.0.0/evaluation_questions.jsonl) |
| AI-reviewed typing questions | [typing_questions.jsonl](C:/IA/dataset/processed/item10/ai_reviewed_eval_v1.0.0/typing_questions.jsonl) |
| AI review decisions for all 200 IDs | [review_log.json](C:/IA/dataset/processed/item10/ai_reviewed_eval_v1.0.0/review_log.json) |
| AI review validation and provenance | [validation_report.json](C:/IA/dataset/processed/item10/ai_reviewed_eval_v1.0.0/validation_report.json), [dataset_manifest.json](C:/IA/dataset/processed/item10/ai_reviewed_eval_v1.0.0/dataset_manifest.json) |
| Machine-readable inventory snapshot | [dataset_inventory.json](C:/IA/outputs/item10-ai-reviewed-evaluation/dataset_inventory.json) |
| Classifier training-layer inventory addendum | [dataset_inventory_addendum.json](C:/IA/outputs/item10-classifier-v1.4.0/dataset_inventory_addendum.json) |
| Current retrieval index and benchmark metadata | [index_manifest.json](C:/IA/outputs/item11-retrieval-v1.2.4/index_manifest.json), [RETRIEVAL_CARD.json](C:/IA/outputs/item11-retrieval-v1.2.4/RETRIEVAL_CARD.json) |
| Item 11 methods, tests and commands | [README.md](C:/IA/dataset/pipelines/item11/README.md), [RETRIEVAL_REPORT.md](C:/IA/outputs/item11-retrieval-v1.2.4/RETRIEVAL_REPORT.md) |
| Item 12 contracts, development controls and results | [README.md](C:/IA/dataset/pipelines/item12/README.md), [VERIFICATION_REPORT.md](C:/IA/outputs/item12-verifier-v1.0.2/VERIFICATION_REPORT.md), [metrics.json](C:/IA/outputs/item12-verifier-v1.0.2/metrics.json) |
| Item 13 protocol, cases, per-question results and metrics | [README.md](C:/IA/dataset/pipelines/item13/README.md), [EVALUATION_REPORT.md](C:/IA/outputs/item13-evaluation-v1.0.1/EVALUATION_REPORT.md), [results.csv](C:/IA/outputs/item13-evaluation-v1.0.1/results.csv), [dataset_inventory_addendum.json](C:/IA/outputs/item13-evaluation-v1.0.1/dataset_inventory_addendum.json) |

## What changed in the latest review

Shortened formal wording, removed repeated questions about the assistant's coverage, retained readable conversational English/Taglish and intentional typing mistakes, added private-sector context to three labor examples, and clarified several synthetic scenarios. Aligned six Taglish prompts by adding ordinary English code-switching terms while preserving missing context. Corrected EVAL_042's wrong-model topic and EVAL_050's unexplained-charge topic. Primary and scope labels did not change. All 20 incomplete typing examples were approved only as clarification tests.

The new questions are AI-authored and AI-reviewed development benchmarks. If test results drive revisions or model choices, retain that development role and use a fresh independent holdout for final performance claims. They do not satisfy the project's recorded independent human-written/labeled gold requirement.

Focused Item 13 repair: the classifier, retrieval, verifier and evaluation packages are new versions of existing artifacts. The repair adds software regression controls, not training questions or independent human gold. [Repair comparison and preservation](C:/IA/outputs/item13-accuracy-repair-v1.0.0/REPAIR_REPORT.md).


## Conditional-normalization development comparison (19 October 2026)

Two preserved studies reused 167 existing AI development questions and added 167 deterministic, reversible noisy variants (334 input forms / 668 paired pipeline executions). They add zero training questions and zero independent human gold. Accepted LLM interpretations are prediction artifacts, not newly approved gold. The first 100-family study exposed regressions; the repaired follow-up uses 67 different recorded families, still previously inspected development material. See the [comparison and repair report](C:/IA/outputs/normalization-evaluation-summary-v1.0.0/REPORT.md) and [inventory addendum](C:/IA/outputs/normalization-evaluation-summary-v1.0.0/dataset_inventory_addendum.json). Neither normalizer is quality-approved for website integration.

The v2.2.1 repair study replays those 334 forms and adds **90 unique synthetic noisy variants across 18 existing partial-support families**, producing 424 forms / 848 executions. The cumulative normalization development collection has 167 original clear questions and 257 synthetic noisy variants; the earlier 334 forms are reused, not counted as newly collected questions. Separate ten-question diagnostic replays include one user payment reproduction, which is excluded from scored performance and is not gold. No training questions or independent human gold were added. [Latest findings](C:/IA/outputs/normalization-repair-summary-v1.0.0/REPORT.md). [Inventory addendum](C:/IA/outputs/normalization-repair-summary-v1.0.0/dataset_inventory_addendum.json).

The subsequent v3.0.0/local-feature repair replays the **same 424 forms**, adding no questions, training examples or independent human gold. The 724-word preservation vocabulary is derived from existing training parents/atoms and taxonomy; separate declared scope/grammar matching terms are development preprocessing rules. Model weights, calibration and membership are unchanged, and retrieval records/vectors remain byte-identical. [Current report](C:/IA/outputs/normalization-repair-v2.0.0/REPORT.md). [Inventory addendum](C:/IA/outputs/normalization-repair-v2.0.0/dataset_inventory_addendum.json).
