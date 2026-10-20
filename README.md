# Recto & Co. Legal

Sharing with the group: [GitHub upload and clone/run instructions](GITHUB_SHARING.md).

20 October conversational repair: broad labor questions can receive explicitly conditional private-sector general information while asking the employment-type follow-up. Completed analyses always include a readable local response when AI is off, unavailable or fails checks. Original classifier predictions remain inspectable; learned model weights and thresholds were not changed. A narrow search-wording repair recovers some supported Taglish consumer queries. [Implementation and validation](outputs/conversational-guidance-v1.0.0/REPORT.md).

Current local runtime (20 October 2026): **classifier v1.5.16, retrieval v1.3.3 and verifier v1.0.11**. `CURRENT_ARTIFACTS.json` is the binding record. Run `start-website.ps1` from the VS Code terminal and use its printed URL; occupied ports are skipped. [Local setup and API](backend/application/README.md).

The website now runs real classification/retrieval, optional Together wording interpretation and recorded-source explanations with exact citation checks and a separate same-model support check. Development explanations are explicitly unreviewed for legal interpretation/currentness. Source approvals and deployment permissions remain closed. AI can be switched off for local-only use. History is opt-in, encrypted for the Windows user, isolated by browser session, retained for 30 days, and supports opening/export/deletion.

The latest **local-only** frozen development run retains 425/425 topic and coverage matches, 435/436 route matches, 93/93 known-relevant Hit@5 and 73/93 Hit@1. These are reused AI inputs, not independent human accuracy. The complete application replay, software/security results and remaining owner/expert work are recorded in [the repair report](outputs/project-repair-v1.0.0/REPORT.md). [Metrics](http://127.0.0.1:5174/performance) are read from checksum-pinned reports; the launcher's current port may differ.

The [holiday explanation repair](outputs/holiday-explanation-repair-v1.0.0/REPORT.md) connects same-topic rule follow-ups to their scenario, improves unworked-holiday source relevance, fixes written ordinal/date matching, and includes the response schema in both Together prompts. One disputed recorded passage is excluded from AI explanation pending source review. A draft with qualification or citation-support problems may receive one bounded correction and the same full checks again. Each claim is assessed against its own cited sources. The earlier complete AI replay is historical; it does not evaluate this revised explanation path. Provider errors and unsupported drafts still withhold output.

Run `check-project.ps1` for repeatable local checks. [Deployment and recovery](DEPLOYMENT_AND_RECOVERY.md) describes source/runtime snapshots, dependency setup, private-state handling and the public-release prerequisites. No public deployment or independent legal sign-off was performed.

## Historical development notes

The following milestone descriptions retain their original versions and outcomes. Statements about what was unavailable apply to those earlier milestones, not the current runtime above.

# Recto & Co. Legal

## Data foundation and preparation record

This README explains, in plain language, what was completed through Item 13's offline development evaluation, why each item was necessary, how the work was performed, and what remains before the legal AI MVP can provide tested answers.

Status date: **19 October 2026**

Current implementation candidate: **classifier v1.5.13**, retrieval **v1.2.9**, verifier **v1.0.8**. The current local classifier → retrieval → verifier run, **local-pipeline-evaluation-v1.2.0**, covers **436 forms / 171 wording families** with both LLM stages disabled. Topic and coverage labels each match **425/425** expectations, routes match **434/436**, and a known relevant provision appears in the first five for **93/93 judged concern groups**. Two conservative clarification deferrals remain. These inspected AI development results are not independent human accuracy or legal-answer approval. The Performance page defaults to this run and retains the older conditional-LLM comparison separately. [Current repair, explanation mode and limitations](outputs/website-explanations-v1.0.0/REPORT.md).

Previous-stack conditional-wording comparison (classifier v1.5.12 / retrieval v1.2.8 / verifier v1.0.7): on **436 frozen forms / 872 executions**, topic/coverage labels match **425/425** and known-relevant Hit@5 **93/93**; routing improves from **434/436 local** to **436/436 conditional**. Five noisy inputs call Together; all clear inputs bypass. Three accepted rewrites pass a disclosed AI semantic audit. Estimated token cost is $0.0011. These are reused development results, not fresh independent accuracy; a full conditional rerun on the newly packaged stack has not been performed. The website shows its current local-only default and separately labeled historical comparison. [Previous comparison and validation handoff](outputs/current-stack-validation-v1.0.0/REPORT.md).

Joined predicate-led complaints retain supported and excluded concerns separately. [Previous joined-concern repair](outputs/joined-concern-repair-v1.0.0/REPORT.md). Incidental pay/work phrases now stay background when the actual concern is an assault or another recognized exclusion; 29 focused regression cases match their expected routes. The local website now generates **owner-enabled development explanations** from eligible recorded sources using Together, with checked citation IDs and exact quotations, clickable source links and a skippable word reveal. Legal interpretation/current applicability are visibly unreviewed. The separate approved current-guidance path, deployment and independent acceptance remain closed; generated-answer quality evaluation remains pending. Start with `C:\IA\start-website.ps1`. [Integration setup](backend/application/README.md).

Historical wording/partial-support repair: **227 software checks passed** before integration. On the identical frozen **424-input / 848-execution** development comparison, conditional noisy topic accuracy improves **74.6% to 99.2%**, partial-support recall **57.4% to 100%**, and route match **69.3% to 97.7%**. Clear topic accuracy stays 100%. The new local classifier alone scores 99.6% noisy topic accuracy; the conditional layer conservatively defers one more labeled input. Only six inputs call the LLM, and both accepted rewrites exactly reconstruct the reference in the AI audit. Training weights/calibration/thresholds and legal records/vectors are preserved. These inspected development scores now appear on the website, with their provenance; they are not independent human accuracy or legal-answer approval. [Repair findings](outputs/normalization-repair-v2.0.0/REPORT.md).

The historical full offline evaluation used **classifier v1.5.5** and **retrieval v1.2.4**; the historical results below belong to that stack. Classifier routing coverage is now **92%** on the opened regression set (previously 69%); classification is 100/100 and partial-support recall remains 11/11. All development/regression numeric gates pass, with thresholds unchanged. These are inspected development results, not fresh independent accuracy claims. The original v1.3.1 once-unseen 95/100 result is preserved.

BM25 and the actual classifier-to-retrieval path both find a known relevant provision for **56/56 existing development queries**, and pass 11/11 negative controls. The stricter index contains **362 chunks / 353 provisions / 12 documents**. The focused repair passes 53 classifier tests and 42 retrieval tests; prior supporting and frozen-data audit results remain preserved. [Repair report and remaining blockers](C:/IA/outputs/pre-item12-repair-2026-10-17/REPAIR_REPORT.md).

**Item 12 is implemented and audited offline (v1.0.2).** The owner's subsequent request to build it supersedes the earlier offline milestone hold. The verifier checks evidence before drafting and structured claims afterward, preserving source/currentness and scope gates. Independent human evaluation, source review/currentness, contact follow-up and formal approvals remain open. Answer generation, user display and deployment remain disabled. [Item 12 report](C:/IA/outputs/item12-verifier-v1.0.2/VERIFICATION_REPORT.md). [Current artifacts](C:/IA/CURRENT_ARTIFACTS.json).

Item 12 passes **37/37 software tests and 50/50 AI development scenarios**; the existing **53 classifier and 42 retrieval tests** also pass. The pre-Item-13 audit additionally passes all **67 reused retrieval cases through Item 12**, **17 supporting tests**, the **59 frozen-dataset checks**, Item 7/8/9 validation, and frontend build/lint. Parent artifacts and legal sources remain unchanged. These results validate development software behavior, not real-world legal accuracy. [Audit and readiness](C:/IA/outputs/pre-item13-audit-2026-10-17/PRE_ITEM13_AUDIT.md).

**Item 13's focused development repair is complete (v1.0.1).** All 34 evaluator tests and all 11 development screens pass. On the same frozen 291 AI cases, primary/scope classification are each **268/268**, explicit concern/evidence checks are **39/39**, known-relevant retrieval is **56/56**, and quotation integrity is **288/288**. The eight targeted cases are fixed; 11 existing conservative routing deferrals remain. Current guidance is blocked and actual generated-answer accuracy is unmeasured. [Repair comparison](C:/IA/outputs/item13-accuracy-repair-v1.0.0/REPAIR_REPORT.md). These are inspected development results; independent/legal acceptance remains pending.

Additional source/contact follow-up: Codex compared the 11-page DTI procedure scan and saved 29 AI-reviewed sections, retained four AI-reviewed final-pay records, and corroborated 36 contact fields across 15 agencies. These are disclosed AI review artifacts; required human approval and unresolved source/contact checks remain open. [Follow-up report](C:/IA/outputs/source-contact-followup-v1.0.0/FOLLOWUP_REPORT.md).

Current counts and file locations: [Project dataset inventory](C:/IA/dataset/DATASET_INVENTORY.md). The two new 100-question sets have completed owner-authorized AI review and are approved for exploratory evaluation; their origin remains AI-authored and they are separate from training.

## What the project is building

Recto & Co. Legal is a web-based legal-information assistant for selected Philippine labor and consumer concerns. It is intended to:

- answer only within its approved labor and consumer scope;
- retrieve the legal provisions supporting an answer;
- display sources that the user can inspect;
- recognize amendments, repeals, renumbering, and outdated guidance;
- identify mixed or out-of-scope questions;
- avoid making a substantive legal claim when the evidence is insufficient; and
- provide general legal information, not professional legal advice or predictions about a case.

The project deliberately does not attempt to cover every area of Philippine law.

## The data we started with

The `dataset/` directory contains the BetterGov.PH Philippine Legal Documents Library. It is a large discovery corpus of approximately 114,340 documents, including statutes, executive issuances, constitutions, and Supreme Court decisions.

This corpus is useful for finding documents, but it cannot automatically be treated as a database of verified current law. A document may be an old version, may have been amended, or may be outside the project's scope. The BetterGov collection is therefore treated as a **discovery source**, while a smaller verified collection is being prepared for actual answers.

The project now has two data tiers:

1. **Canonical answer sources** — individually selected, downloaded and source-recorded documents with extraction, eligibility and legal/currentness reviews tracked per record under `dataset/canonical_sources/`.
2. **Broader discovery corpus** — the BetterGov Parquet and Markdown collection, which may help locate relevant material but cannot independently support a current-law answer.

This distinction is one of the most important safety decisions made so far.

## Completed work

### Item 1 — Define and freeze the MVP legal scope

File: [`project_legal_scope.md`](project_legal_scope.md)

#### What happened

The first step was deciding exactly what the MVP may and may not answer.

The approved labor scope includes subjects such as wages, working hours, rest days, overtime, holiday pay, thirteenth-month pay, basic employment-contract questions, termination procedure, final pay, certificates of employment, and basic complaint referrals.

The approved consumer scope includes defective products, warranties, repair or replacement, refunds, deceptive sales practices, misleading advertisements, price tags, product safety, basic service complaints, online consumer transactions, and DTI complaint procedures.

Specialized subjects such as banking, insurance, investments, privacy, criminal online fraud, overseas workers, seafarers, government employment, complex collective bargaining, workers' compensation, and exact regional wage rates were excluded from the first MVP.

#### Why it was necessary

Without a fixed scope, almost any document in the 114,340-document corpus could appear relevant. That would make filtering inconsistent and would encourage the system to answer questions for which it was never properly prepared.

The scope is now the rule used to decide:

- which documents are collected;
- which records are retained during filtering;
- which questions the classifier should accept;
- when the assistant should provide only a partial answer; and
- when the assistant should decline and refer the user elsewhere.

### Item 2 — Create an authoritative-source registry

File: [`dataset/authoritative_source_registry.csv`](dataset/authoritative_source_registry.csv)

#### What happened

A registry of **13 recognized source providers** was created. It records each provider's organization, website, legal domains, document types, authority level, permitted use, answer eligibility, verification method, last-check date, and notes.

Examples include the Official Gazette, Supreme Court E-Library, DOLE, DTI, NWPC, NLRC, BetterGov, and Lawphil.

#### Why it was necessary

Finding the same law on two websites does not mean the copies have equal authority. The registry tells the project which source should be preferred and what a copy may be used for.

The working source order is:

1. Official Gazette or official printed publication
2. The government agency that issued the document
3. Supreme Court E-Library
4. An official document preserved through a recognized institutional mirror
5. BetterGov or Lawphil as discovery or comparison sources

Lower-ranked sources are not automatically rejected. They simply cannot be used beyond the permission recorded in the registry.

#### How it was done

Each source was checked individually. The registry records how document identity must be verified—for example, by comparing the document number, title, approval date, effectivity clause, and official publication details.

### Item 3 — Build the initial canonical law collection

Main manifest: [`dataset/canonical_sources/manifests/canonical_documents.csv`](dataset/canonical_sources/manifests/canonical_documents.csv)

#### What happened

The first **10 core legal documents** were selected and preserved:

Labor:

- DOLE's 2022 renumbered Labor Code edition
- Presidential Decree No. 442, the original Labor Code text
- Presidential Decree No. 851 on thirteenth-month pay
- Memorandum Order No. 28
- Republic Act No. 6727, the Wage Rationalization Act
- Republic Act No. 10151 on night work and Labor Code renumbering
- Republic Act No. 10396 on labor conciliation-mediation

Consumer:

- Republic Act No. 7394, the Consumer Act
- Republic Act No. 10909, the No Shortchanging Act
- Republic Act No. 11967, the Internet Transactions Act

#### Why it was necessary

The BetterGov corpus contains many useful texts, but the AI needs a small set of known documents that can safely anchor its answers. Item 3 established that foundation.

#### How it was done

For every document:

- the official or best permitted source was located;
- the source URL and retrieval URL were recorded;
- the raw file was saved without rewriting it;
- the title and citation were checked;
- the official URL, retrieval URL, local path, retrieval date, and verification result were recorded;
- the source and verification status were recorded; and
- an initial decision was made about whether the document could become an answer source.

Raw files are stored under `dataset/canonical_sources/raw/`. They must never be silently overwritten. A changed upstream document must be saved as a new version.

### Item 4 — Add implementing rules and practical agency guidance

#### What happened

Statutes usually state the general rule, while implementing orders explain procedures, deadlines, coverage, and agency handling. Ten more official materials were therefore added.

Labor:

- Omnibus Rules Implementing the Labor Code
- DOLE Department Order No. 147-15 on Book VI and termination
- DOLE Department Order No. 249-25 on the current SEnA procedure
- Labor Advisory No. 06-20 on final pay and certificates of employment
- Labor Advisory No. 16-25 on thirteenth-month pay for 2025
- 2024 Workers' Statutory Monetary Benefits Handbook

Consumer:

- DTI DAO No. 02, Series of 1993, implementing the Consumer Act
- DTI DAO No. 16-03, implementing the No Shortchanging Act
- DTI DAO No. 20-02 on mediation and adjudication
- Joint Administrative Order No. 24-03, implementing the Internet Transactions Act

This increased the canonical collection to **20 documents: 13 labor and 7 consumer documents**.

#### Why it was necessary

An answer based only on a statute can be incomplete. For example, RA 10396 establishes labor conciliation-mediation, but current procedural details come from DOLE Department Order No. 249-25. Likewise, the Internet Transactions Act must be read with its implementing rules.

#### How it was done

Official agency indexes and publication pages were checked. PDFs were downloaded and checked for the expected title, page count, and first-page contents. HTML sources were verified against their displayed citation and title. Every new raw file received a manifest entry containing its identity, source locations, retrieval date, and verification result.

Materials were assigned different roles. A statute or implementing order may support an answer, while an agency handbook may only help explain a rule already supported by controlling authority.

#### Gaps found during Item 4

- The official historical download for DOLE Department Order No. 119-12 was unavailable. An uncontrolled substitute was not added.
- A stable standalone official copy of the older thirteenth-month-pay implementing and revised guidelines was not located.
- The stored full text of Memorandum Order No. 28 comes from Lawphil and still needs comparison with an official full-text copy.

These gaps were recorded instead of being filled with unverified material.

### Item 5 — Audit currentness and legal relationships

Files:

- [`dataset/canonical_sources/manifests/legal_status_review.csv`](dataset/canonical_sources/manifests/legal_status_review.csv)
- [`dataset/canonical_sources/manifests/legal_status_relationships.csv`](dataset/canonical_sources/manifests/legal_status_relationships.csv)
- [`dataset/canonical_sources/scripts/apply_item5_status.ps1`](dataset/canonical_sources/scripts/apply_item5_status.ps1)
- [`dataset/canonical_sources/scripts/validate_item5_status.ps1`](dataset/canonical_sources/scripts/validate_item5_status.ps1)

#### What happened

All 20 canonical documents were reviewed to determine whether each one is:

- current and operative;
- an official consolidation with a cutoff date;
- amended or supplemented;
- historical only;
- applicable only to a particular year;
- explanatory rather than controlling law; or
- legally operative but represented by a source copy that is not yet suitable for answers.

The review also recorded **18 legal relationships**, including amendment, partial repeal, renumbering, implementation, modification, supplementation, and replacement for current use.

#### Important decisions

- The original 1974 text of PD 442 is historical and cannot answer a present-law question by itself.
- The DOLE 2022 Labor Code is the working baseline, but later developments must still be checked.
- PD 851 must be interpreted with MO 28 and applicable DOLE guidance.
- MO 28 is legally important, but its stored copy remains ineligible for direct answers until it is compared with an official full-text copy.
- RA 6727 may explain the wage-setting framework, but it cannot establish a current regional wage amount.
- DO 249-25 is the selected current SEnA procedure; the older 2016 procedure must not be presented as current.
- Labor Advisory No. 16-25 is specific to 2025 and was removed from the default current-law answer set.
- The 2024 DOLE handbook is explanatory material and cannot replace the controlling law.
- DTI DAO No. 02 remains a general Consumer Act IRR but must be checked against later topic-specific rules.
- DTI DAO No. 20-02 is the selected current DTI mediation and adjudication procedure.
- JAO No. 24-03 is the selected current IRR for the Internet Transactions Act.

#### How it was done

The text of the documents was checked for express language such as “amended,” “repealed,” “modified,” “renumbered,” and “implementing rules.” Current official agency indexes and official government publications were then checked for later or replacement issuances.

The status review intentionally separates two questions:

1. **Is the legal authority still operative?**
2. **Is our particular stored copy sufficiently verified to support an answer?**

A law can be in force while the stored copy remains unsuitable for direct citation. Keeping these questions separate prevents source quality from being confused with legal effect.

#### Validation result

- 20 of 20 documents have a completed status review.
- 18 legal relationships passed validation.
- Zero manifest records remain marked `pending_item_5`.
- All 20 manifest entries point to an existing raw file and retain matching source and path information.
- 15 documents remain candidates for the default answer-authority set.
- Five documents are restricted to historical, corroborative, time-bound, audit, or explanatory use.

### Item 6 — Define the cleaned-data schema and cleaning rules

Files:

- [`dataset/data_contract/README.md`](dataset/data_contract/README.md)
- [`dataset/data_contract/schemas/legal_document.schema.json`](dataset/data_contract/schemas/legal_document.schema.json)
- [`dataset/data_contract/schemas/legal_provision.schema.json`](dataset/data_contract/schemas/legal_provision.schema.json)
- [`dataset/data_contract/schemas/retrieval_chunk.schema.json`](dataset/data_contract/schemas/retrieval_chunk.schema.json)
- [`dataset/data_contract/controlled_vocabularies.json`](dataset/data_contract/controlled_vocabularies.json)
- [`dataset/data_contract/topic_taxonomy.csv`](dataset/data_contract/topic_taxonomy.csv)
- [`dataset/data_contract/samples/`](dataset/data_contract/samples/)
- [`dataset/data_contract/scripts/validate_item6_contract.ps1`](dataset/data_contract/scripts/validate_item6_contract.ps1)

#### What happened

A versioned data contract was created before cleaning any source document. It defines four connected data layers: document snapshots, complete legal provisions, provision-level scope and legal status, and smaller retrieval chunks linked to their parent provisions.

The contract also separates three forms of text: source-faithful text for display and citation, deterministically normalized text, and search-oriented text. Generated summaries remain discovery aids and cannot replace legal text.

Scope and answer eligibility are now defined at provision level. This allows the project to retain a complete law while excluding particular provisions outside the MVP, such as specialized consumer-credit or collective-bargaining material.

The topic taxonomy contains 42 supported and excluded labor and consumer topics. Ordinary online consumer transactions were made explicitly in scope, while criminal online fraud and data-privacy issues remain excluded or subject to partial-answer routing.

#### Source-specific rules

The contract was tested against three actual source patterns:

- the text-based DOLE 2022 Labor Code PDF, where extracted glyphs sometimes require visual confirmation;
- the Supreme Court E-Library Consumer Act HTML; and
- the 1993 DTI Consumer Act IRR, which is an image-only, rotated scan containing two printed pages in one PDF image.

Rules now cover HTML cleanup, PDF page tracking, printed-page tracking, OCR, rotation, multi-page scans, footnotes, Unicode errors, provision boundaries, natural-subdivision chunking, traceability, answer gating, and quality flags.

#### Validation result

- Three JSON Schemas passed native schema validation.
- Three sample documents, three sample provisions, and three sample retrieval chunks passed the Item 6 validator.
- All sample document IDs, paths, and source URLs match the canonical manifest, and their raw files exist.
- All sample topics and legal relationships resolve to controlled records.
- The taxonomy contains 42 unique topics.
- No raw legal source was changed.

## What exists now

```text
IA/
├── README.md
├── paper.md
├── project_legal_scope.md
└── dataset/
    ├── authoritative_source_registry.csv
    ├── consolidated.parquet
    ├── juris.parquet
    ├── repacts.parquet
    ├── repacts_with_summary.parquet
    ├── markdown/
    ├── data_contract/
    │   ├── README.md
    │   ├── controlled_vocabularies.json
    │   ├── topic_taxonomy.csv
    │   ├── schemas/
    │   ├── samples/
    │   └── scripts/
    ├── pipelines/
    │   ├── item7/
    │       ├── README.md
    │       ├── prepare_ocr.py
    │       ├── ocr_images.mjs
    │       ├── extract_canonical.py
    │       ├── validate_item7.py
    │       └── jsonl_to_parquet.py
    │   ├── item8/
    │       ├── README.md
    │       ├── filter_rules.json
    │       ├── filter_bettergov.py
    │       ├── validate_item8.py
    │       └── run_item8.ps1
    │   ├── item9/
    │       ├── README.md
    │       ├── build_item9.py
    │       ├── validate_item9.py
    │       └── run_item9.ps1
    │   └── item10/
    │       └── README.md
    ├── processed/
    │   ├── item7/
    │       ├── documents.jsonl / documents.parquet
    │       ├── provisions.jsonl / provisions.parquet
    │       ├── retrieval_chunks.jsonl / retrieval_chunks.parquet
    │       ├── extraction_report.csv
    │       ├── ocr_review_queue.csv
    │       ├── human_review_queue.csv
    │       └── validation_report.json
    │   ├── item8/
    │       ├── candidate_documents.jsonl / candidate_documents.parquet
    │       ├── candidate_review_queue.csv
    │       ├── canonical_matches.csv
    │       ├── internal_duplicates.csv
    │       ├── missing_markdown.csv
    │       ├── filter_summary.json
    │       └── validation_report.json
    │   └── item9/
    │       ├── classifier_questions.csv / .jsonl / .parquet
    │       ├── referral_directory.csv
    │       ├── dataset_summary.json
    │       └── validation_report.json
    └── canonical_sources/
        ├── README.md
        ├── raw/
        ├── manifests/
        │   ├── canonical_documents.csv
        │   ├── legal_status_review.csv
        │   └── legal_status_relationships.csv
        └── scripts/
            ├── apply_item5_status.ps1
            └── validate_item5_status.ps1
```

The BetterGov data has now been filtered into a discovery queue, but it has not been bulk-cleaned or indexed as verified current law. That is intentional. Items 1–9 created the scope, trusted reference set, data contract, canonical processed baseline, safely gated list of possible additional documents, and the first classifier and referral datasets.

## Recent completed work and remaining items

The next work should proceed in this order.

### Item 7 — Completed: extract and normalize the 20 canonical documents

All 20 canonical sources were converted into document, provision, and retrieval-chunk records under the Item 6 contract. HTML was structurally cleaned, text PDFs retained page locations, and the four image-only PDFs were OCRed. The rotated 1993 DTI scan was also split into its two printed pages per PDF page.

OCR-derived provisions are searchable but remain in a human-review queue and are not answer eligible. Text-PDF defects are also quarantined. JSONL is the lossless contract output; matching Parquet files were created for Pandas and analytical work. The Item 7 validator checks source-file existence and manifest provenance, required fields, identifiers, relationships, topics, character offsets, printed-page locators, suspicious extraction patterns, and answer-safety gates.

### Item 8 — Completed: filter the BetterGov corpus to the approved scope

Files:

- [`dataset/pipelines/item8/README.md`](dataset/pipelines/item8/README.md)
- [`dataset/pipelines/item8/filter_rules.json`](dataset/pipelines/item8/filter_rules.json)
- [`dataset/pipelines/item8/filter_bettergov.py`](dataset/pipelines/item8/filter_bettergov.py)
- [`dataset/pipelines/item8/validate_item8.py`](dataset/pipelines/item8/validate_item8.py)
- [`dataset/processed/item8/candidate_review_queue.csv`](dataset/processed/item8/candidate_review_queue.csv)
- [`dataset/processed/item8/filter_summary.json`](dataset/processed/item8/filter_summary.json)
- [`dataset/processed/item8/validation_report.json`](dataset/processed/item8/validation_report.json)

#### What happened

The BetterGov corpus was reduced from 114,340 records to a reviewable set of **182 possible labor or consumer documents**. This was a filtering step, not a legal verification step.

The pipeline first excluded all 68,080 jurisprudence records and all nine constitutions. It then considered only statute and executive records from 1970 onward, leaving 28,385 metadata records for rule-based screening. Republic Acts were screened using BetterGov's enriched title, summary, key-provision, amendment, tag, and keyword fields. Other eligible documents were checked one at a time from the Markdown corpus, with a 120,000-character reading limit per file. Legal text was used only for local relevance scoring and was not copied into the Item 8 outputs.

The filter looked for approved subjects such as wages, hours of work, overtime, rest days, thirteenth-month pay, employment contracts, termination, final pay, consumer warranties, product safety, online transactions, and complaint procedures. It also looked for citations to core laws and words indicating amendment, implementation, repeal, modification, or supplementation.

Excluded subjects were not silently accepted. Records mentioning government employment, OFWs, seafarers, collective bargaining, workers' compensation, banking, insurance, investments, privacy, telecommunications, real estate, and the other Item 1 exclusions were moved into boundary review.

#### Deduplication and safety

Nine BetterGov records matched documents already present in the canonical collection and were removed from the candidate queue. One additional within-corpus duplicate was suppressed. Deduplication uses legal citation numbers where possible; it does not trust generic page headings such as “MALACAÑANG” as document identity.

Every one of the 182 remaining rows is marked:

- `discovery_status=unverified_discovery`;
- `permitted_use=discovery_only`;
- `answer_eligible=false`;
- `needs_official_source_verification=true`; and
- `human_decision=pending`.

The automated prediction divided the queue into 163 labor, seven consumer, and 12 mixed-domain candidates. These are screening predictions, not final legal classifications. The review queue contains four medium-priority candidates, 53 low-priority candidates, and 125 boundary-review candidates. The high number of boundary records is deliberate: an apparent labor or consumer match that also touches an excluded field must be reviewed before it can move forward.

#### Validation result

- 182 JSONL records, 182 Parquet rows, and 182 CSV review rows agree.
- Candidate identifiers and BetterGov identifiers are unique.
- No jurisprudence or constitution entered the queue.
- All candidates remain blocked from answer use.
- All candidates require official-source verification.
- No expected Markdown source file was missing.
- The Item 8 validation report passed with zero errors.

Passing validation means the queue is structurally consistent and safely restricted. It does not mean all 182 documents should be added. Human triage and official-source verification are the next decisions for any candidate that is eventually promoted.

### Item 9 — Completed: build the question-classification and referral seed data

Files:

- [`dataset/pipelines/item9/README.md`](dataset/pipelines/item9/README.md)
- [`dataset/pipelines/item9/build_item9.py`](dataset/pipelines/item9/build_item9.py)
- [`dataset/pipelines/item9/validate_item9.py`](dataset/pipelines/item9/validate_item9.py)
- [`dataset/processed/item9/classifier_questions.csv`](dataset/processed/item9/classifier_questions.csv)
- [`dataset/processed/item9/referral_directory.csv`](dataset/processed/item9/referral_directory.csv)
- [`dataset/processed/item9/dataset_summary.json`](dataset/processed/item9/dataset_summary.json)
- [`dataset/processed/item9/validation_report.json`](dataset/processed/item9/validation_report.json)

#### What happened

Item 9 created **672 realistic seed questions** covering every one of the 42 supported and excluded topics defined in Item 6. This dataset teaches a future classifier to distinguish four routing outcomes:

- `labor` for questions containing only a supported labor topic;
- `consumer` for questions containing only a supported consumer topic;
- `mixed` for questions containing both supported domains, or a supported issue combined with an excluded issue; and
- `out_of_scope` for questions containing no supported topic.

The label alone is not enough to decide what the application should do. Each row therefore also has a scope label and routing action. A fully supported question may be answered after retrieval. A partially supported question must answer only the supported portion and refer the rest. A fully unsupported question must decline the substantive answer and provide an appropriate referral.

The generated set contains 160 labor, 176 consumer, 168 mixed, and 168 out-of-scope questions. It includes 378 English questions and 294 conversational English-Taglish questions. The dataset is divided into 490 training, 91 validation, and 91 test rows.

#### Preventing an artificially easy evaluation

Questions that describe the same situation may have different wording. If one wording appeared in training and a near-identical wording appeared in the test data, the classifier could seem accurate merely because it memorized the scenario.

Item 9 prevents this by assigning related questions a shared `scenario_group_id`. All variants of one situation are kept entirely in one split. Validation confirmed that no scenario group crosses between training, validation, and test.

#### Human-review requirement

The questions are a synthetic seed set, not yet a final gold-standard dataset. Every row is marked:

`annotation_status=machine_generated_needs_human_review`

A human reviewer must confirm the wording, topic classification, scope label, routing action, and referral before the row is approved for final model training or formal evaluation. Real anonymized user questions should later be added with a different provenance label so synthetic and real data can be measured separately.

#### Referral directory

A separate directory of **19 official referral destinations** was created. It includes DOLE/SEnA, DTI CARe, PAO, DMW, MARINA, CSC, ECC, OSHC, SSS, NWPC, BSP, SEC, the Insurance Commission, NPC, NTC, HSAC/DHSUD, LTFRB, ERC, and the PNP Anti-Cybercrime Group.

The directory is separate from classifier training because phone numbers, email addresses, and portals may change. Each row records the proper subject, first step, official URLs, available contact information, verification source, verification status, and last-verified date. When a detailed contact page could not be verified, only the official government website was retained and the missing contact verification was stated explicitly.

Financial referrals are context-specific: bank and e-wallet concerns route to BSP, while lending-company complaints route to the SEC. The system does not send every financial question to both agencies.

#### Validation result

- 672 CSV, JSONL, and Parquet question records agree.
- All question identifiers and normalized question texts are unique.
- All 42 taxonomy topics are represented.
- Every classifier label appears in training, validation, and test.
- No scenario group leaks across dataset splits.
- All synthetic records remain gated for human review.
- All 19 referral records have an official verification source and freshness date.
- The Item 9 validation report passed with zero errors.

Passing validation means the seed data is internally consistent. It does not mean the questions have already been approved by a human annotator or that a classifier has already been trained.

#### Planned runtime flow for English and Taglish questions

The original user question must always be preserved. Taglish is not translated and discarded before classification. The recommended application flow is:

1. Save the original English, Filipino, or Taglish question.
2. Run the classifier on the original wording to obtain the domain, supported topics, excluded topics, scope label, routing action, and confidence.
3. Optionally ask the LLM to produce a normalized English search query. This is a retrieval aid, not a replacement for the original question or the classifier result.
4. Search using the original and normalized queries against answer-eligible legal provisions.
5. Apply legal-status, source-quality, scope, and evidence thresholds.
6. Give the LLM the original question, structured classifier result, retrieved provisions, legal-status warnings, and permitted referrals.
7. Require the LLM to explain only claims supported by the retrieved provisions.
8. Run citation and answer-safety verification before displaying the response.

If classifier confidence is low, the system should ask a clarifying question or use a recorded LLM routing fallback. The LLM must not silently override the classifier. Keeping both the original and normalized query also allows separate measurement of English performance, Taglish performance, normalization errors, retrieval quality, citation accuracy, and unsupported-claim rate.

### Item 10 — Human-review the classifier data and train the classifier

Plan: [`dataset/pipelines/item10/README.md`](dataset/pipelines/item10/README.md)

Annotation instructions: [`dataset/pipelines/item10/ANNOTATION_GUIDE.md`](dataset/pipelines/item10/ANNOTATION_GUIDE.md)

The five human-review workbooks have been consolidated with project-owner-authorized AI cleanup. The [reviewed dataset v1.0.0](dataset/processed/item10/reviewed_v1.0.0/README.md) contains **661 included and 11 excluded questions**. Original Item 9 records and returned workbooks remain unchanged. The reviewed version preserves original reviewer decisions, logs consolidation changes, and groups underlying scenarios together across revised train/validation/test splits. Cleaned workbooks are under `outputs/item10-review-cleaned/`.

The [AI-reviewed development benchmarks](C:/IA/dataset/processed/item10/ai_reviewed_eval_v1.0.0/README.md) add 100 general evaluation questions and 100 typing/clarification questions. Codex reviewed every row, recorded 91 wording revisions and two topic corrections, and approved all 200 for exploratory evaluation. No human review of these new sets is claimed. They remain excluded from training and unlocked for development; they do not fulfill the independent human-written/labeled gold requirement.

The review/consolidation phase is complete. The last evaluated classifier v1.5.5 preserves separated concerns and passes its numeric development/regression gates and 53 software tests. On the opened synthetic regression set, classification is 100/100, partial recall is 11/11 and decisive coverage is 92%. These are inspected development results. Formal final evaluation still requires a fresh independently written, human-labeled holdout and any required team/adviser approval. No deployment was authorized or performed.

The initial baselines should include a dummy classifier, TF-IDF with logistic regression, and TF-IDF with a linear support-vector classifier. A multilingual embedding or transformer model may be tested later, but it should not replace the simpler baselines without evidence that it generalizes better.

Every trained model must be packaged with its preprocessing, label mapping, training-data version and row counts, random seed, dependency versions, confidence threshold, metrics, model card, and structured inference contract. The external LLM API may assist with optional normalization or act as a separately measured fallback, but the independently evaluated classifier promised in the proposal must remain visible.

### Item 11 — Offline retrieval index and development benchmark completed

The last evaluated v1.2.4 index contains 362 chunks from 353 provisions across 12 canonical documents. It applies chunk/provision/document eligibility, source authority, scope, extraction-quality and legal-use gates. Fifty-eight additional flagged-eligible chunks are quarantined in the Item 11 audit; original legal data and review queues remain unchanged.

BM25 keyword, local multilingual semantic and reciprocal-rank-fusion hybrid search are implemented. BM25 is the development-selected default: Hit@5 100% and MRR@10 0.896 on the 56 inspected AI-authored questions across 28 English/Taglish scenario families. Eleven negative controls and 42 software tests passed. These are development relevance judgments, not independent human gold or a measure of legal-answer correctness.

Results preserve citations, exact chunk/parent text, source locators, recorded status and freshness/related-authority conditions. Classifier integration retrieves only supported components and returns no candidates for clarification/referral routes. Final-pay/COE evidence is unavailable; other authority/extraction gaps remain documented. Legal status was not refreshed by this build, and answer generation remains disabled.

[Pipeline and commands](C:/IA/dataset/pipelines/item11/README.md). [Current results, tests and source audit](C:/IA/outputs/pre-item12-repair-2026-10-17/REPAIR_REPORT.md).

### Item 12 — Offline citation and evidence verifier implemented

The implemented preflight and postflight gates check:

- the cited document and provision actually exist;
- full-provision quotations match exact stored text and offsets;
- current-guidance claims, including paraphrases, have separate scoped support/relevance/qualification and concern-coverage reviews;
- the source is eligible for that type of answer;
- a known amendment or time limitation has not been ignored;
- enough evidence was retrieved; and
- unsupported portions of mixed questions are identified rather than guessed.

The strict structured-draft contract rejects fabricated citations, changed quotations, omitted local qualifications, unchecked answer text and draft-supplied approval. Failed claims withhold their concern as a unit; independently passing concerns may remain as partial development candidates. Classifier probabilities and retrieval ranking stay separate from legal-support judgments.

Recorded-excerpt mode permits diagnostic exact-text previews with explicit limitations. It verifies provenance, not relevance, currentness or legal-answer completeness. Current-guidance mode requires an operator-managed scoped review; the real review store remains empty, so that gate currently blocks. Arbitrary paraphrase entailment is a review gate, not an automatic semantic model. Normal runtime rejects simulated software approvals. No LLM API or live answering was enabled.

[Implementation and commands](C:/IA/dataset/pipelines/item12/README.md). [Versioned tests, metrics and limitations](C:/IA/outputs/item12-verifier-v1.0.2/VERIFICATION_REPORT.md).

### Item 13 — Offline system evaluation implemented; findings and formal validation pending

The evaluator freezes the protocol, cases, grouping and source/code hashes before inference. It sends only question text through the actual classifier, retrieval and verifier, then scores expected domains, labels, known relevant provisions, quotation integrity, clarification/referral, corpus gaps and mixed concerns. It reports per-question results, confusion/calibration plots, label-confidence calibration, family-cluster descriptive intervals, source/language/typing/topic strata and an error log. The original model and sources are unchanged.

The repair reruns the exact frozen 291 cases and unchanged screening targets: 200 general/typing questions, 67 retrieval queries and 24 AI-authored system questions across eight families. Classification is 268/268 per head; explicit concern/evidence checks improve from 31/39 to 39/39. All 11 development screens pass. Eleven existing cases retain conservative routing deferrals. Thresholds, model weights, calibration and expected labels are unchanged. All material remains inspected AI development evidence; no independent human questions were added.

No LLM drafter or actual generated answers were used. Legal-answer accuracy, unsupported-claim rate and false declines on verified-current answerable questions remain unavailable. An offline scorer and schemas accept future externally supplied drafts and separately bound operator legal-review judgments, without bypassing Item 12 gates. Fresh independent human evaluation and licensed Philippine legal review of selected generated answers, as required by the proposal, remain pending. This version executes development only and cannot relabel these cases as a final holdout.

[Implementation and commands](C:/IA/dataset/pipelines/item13/README.md). [Results and uncertainty](C:/IA/outputs/item13-evaluation-v1.0.1/EVALUATION_REPORT.md). [Per-question table](C:/IA/outputs/item13-evaluation-v1.0.1/results.csv).

### Item 14 — Connect the data pipeline to the MVP application

Integrate the classifier, retrieval system, citation panel, legal-status warnings, answer thresholds, chat history, and accessibility interface. Add a repeatable refresh process so new issuances can be acquired, source-recorded, reviewed, processed, tested, and deployed without silently replacing older versions.

## Data that should not be added automatically

- The complete jurisprudence corpus should not become an answer authority unless case-law use is separately designed and approved. Jurisprudence requires treatment of doctrine, later rulings, factual differences, and case status.
- Exact regional wage rates should remain excluded until a reliable, frequently refreshed wage-order pipeline is built.
- Secondary summaries must not replace statutes, regulations, or official issuances.
- A document should not enter the current-law answer set merely because it contains a relevant keyword.

## Immediate next step

The focused wording and partial-support repair is implemented and tested. Next, review/test the candidate and discuss the requested website/classifier/explanation-LLM integration order; no integration choice has been executed. The full Item 13 screening run on the current stack, independent human evaluation, source/legal reviews and formal acceptance retain their separate pending status. [Current findings](C:/IA/outputs/normalization-repair-v2.0.0/REPORT.md).

## Current limitations

The canonical collection is a controlled MVP subset, not a complete statement of Philippine labor or consumer law. Some official historical documents remain unavailable, currentness checks must be repeated over time, and no automated legal answer should be treated as a substitute for advice from a qualified lawyer or the appropriate government agency.
