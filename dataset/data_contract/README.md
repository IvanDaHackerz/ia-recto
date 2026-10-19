# Item 6 Data Contract

Version: `1.0.0`  
Status date: `2026-09-29`

Current project status: Item 7 implemented this contract for all 20 canonical documents, Item 8 created a separately gated BetterGov discovery queue, and Item 9 created a separate classifier seed dataset. The Item 11 search index must continue to use these document, provision, retrieval-chunk, eligibility, and provenance rules.

## Purpose

This contract defines what Recto & Co. Legal means by cleaned and retrieval-ready legal data. It applies first to the 20 canonical documents and later to BetterGov discovery records that pass scope filtering and source verification.

Item 6 did not alter the raw source files. It defined the structures and rules that Item 7 subsequently implemented.

## Project requirements represented by this contract

The contract supports the project described in `paper.md` and `project_legal_scope.md`:

- provision-level legal retrieval;
- labor, consumer, mixed-domain, and out-of-scope handling;
- source and citation verification;
- amendment, repeal, renumbering, and currentness checks;
- evidence thresholds before substantive answers;
- visible last-checked dates;
- partial answers for mixed questions; and
- refusal or referral when verified support is insufficient.

The legal corpus and the classifier dataset are separate products. Legal documents populate retrieval; they are not classifier examples. Item 9 created labeled user-style classifier seeds, all of which remain pending human annotation review.

## Four-layer legal data model

### 1. Document snapshot

One record identifies a frozen source file and its provenance. It carries the official and retrieval URLs, authority level, verification status, document-wide legal-status default, and raw-file location.

Schema: `schemas/legal_document.schema.json`

### 2. Legal provision

One record represents a complete legally meaningful unit, normally an article, section, rule, or annex provision. A provision retains its hierarchy, exact source location, three text representations, topic scope, legal status, and quality information.

Schema: `schemas/legal_provision.schema.json`

### 3. Scope and legal status

The document status created in Items 1-5 is inherited as a default, but it may be narrowed at provision level. This is necessary because an otherwise useful law may contain provisions outside the MVP scope.

Examples:

- Consumer Act credit provisions are outside the initial banking and lending boundary.
- Labor Code collective-bargaining provisions are outside the initial complex labor-relations boundary.
- Internet Transactions Act consumer provisions are supported, while data-privacy and criminal-fraud issues remain outside scope.

An excluded provision remains in the cleaned document for completeness but cannot enter the default answer index.

Controlled values: `controlled_vocabularies.json`  
Topic map: `topic_taxonomy.csv`

### 4. Retrieval chunk

A retrieval chunk is a smaller searchable passage linked to one complete parent provision. Chunks are derived search artifacts and never replace the provision used for display or citation.

Schema: `schemas/retrieval_chunk.schema.json`

## Text representations

Each provision contains three deliberately different text fields:

- `verbatim_text`: Source-faithful legal wording used for display and citation. Layout whitespace may be normalized, but words, numbers, punctuation with legal meaning, enumerations, and qualifications must remain intact. Any manual repair is logged.
- `normalized_text`: The same wording with deterministic Unicode, whitespace, paragraph, list, and line-break normalization. It is suitable for comparison and chunk construction.
- `search_text`: A retrieval-oriented derivative. It may normalize case, punctuation variants, citation forms, and known old/current article aliases. It must not introduce a legal proposition that is absent from the provision.

Generated summaries, BetterGov tags, keywords, and section summaries are discovery aids only. They must not be copied into `verbatim_text` or cited as law.

## Source-specific extraction rules

### HTML

1. Remove navigation, scripts, styles, cookie text, unrelated headers, and site chrome.
2. Preserve document headings, provision labels, paragraph boundaries, enumerations, tables, footnotes, and meaningful links.
3. Treat visual tags such as `<br>`, paragraphs, list items, and table rows as structural boundaries.
4. Do not assume that one HTML line equals one provision. Several sampled BetterGov files place multiple provisions on one physical line.
5. Store an HTML anchor when available. Otherwise store source character offsets or a deterministic provision locator.

### Text-based PDF

1. Extract text page by page and preserve the PDF page number.
2. Record the printed page number separately when it differs from the PDF page index.
3. Compare headings, provision boundaries, numeric amounts, percentages, citations, and suspicious glyphs against the rendered page.
4. Remove line-wrap hyphenation only when the rendered word clearly continues on the next line.
5. A replacement character such as `U+FFFD` is a blocking quality error until visually resolved.
6. Footnotes are stored separately and linked to their markers; they are not silently inserted into the operative sentence.

### Image-only or scanned PDF

1. Detect pages with no embedded text and mark `ocr_used=true` when OCR is performed.
2. Detect rotation before OCR. Store the applied rotation.
3. Detect pages containing more than one printed page. OCR and locate each printed page separately while retaining the original PDF page number.
4. Preserve printed-page numbers, bounding regions when available, paragraph order, and table structure.
5. OCR confidence must be recorded when the engine provides it.
6. Manually review provision labels, dates, monetary values, percentages, negations, cross-references, and low-confidence spans.
7. No OCR-derived provision becomes answer eligible while it contains unresolved replacement characters or a blocking quality flag.

The sampled 1993 DTI Consumer Act IRR is image-only, rotated 90 degrees, and contains two printed pages in one PDF image. Item 7 must therefore use rotation and page-region handling for that document.

## Cleaning rules

### Permitted operations

- Unicode normalization to NFC.
- Normalize CRLF and CR line endings to LF.
- Remove repeated spaces caused by layout extraction.
- Remove non-document website navigation and boilerplate.
- Join words split only by source line wrapping.
- Preserve meaningful paragraph and list boundaries.
- Repair a visibly confirmed extraction or OCR error and record the repair.
- Create citation aliases for old and renumbered article numbers without changing the provision text.

### Prohibited operations

- Paraphrasing or simplifying the law inside the legal-text fields.
- Replacing legal wording with a generated summary.
- Silently changing spelling, grammar, numbers, dates, or punctuation that may affect meaning.
- Removing provisos, exceptions, definitions, footnotes, or cross-references merely to shorten a record.
- Combining provisions from different source documents into one authoritative provision.
- Treating a BetterGov summary or Lawphil discovery copy as verified current law.
- Overwriting a raw file after acquisition. Store an upstream change as a new version and review it again.

## Provision boundary rules

1. Prefer the source's legal unit: article, section, rule, regulation, or annex item.
2. Store structural headings such as book, title, chapter, and part as hierarchy metadata.
3. A heading without independent operative text may be represented as hierarchy rather than a standalone answerable provision.
4. Definitions may remain one provision, but individual defined terms may be child provisions when retrieval testing shows that the full definition section is too large.
5. Lettered and numbered clauses remain inside their parent provision unless a long provision requires child records. Child records must link to the complete parent.
6. Never split a sentence or move an exception away from the rule it qualifies.

## Retrieval chunk rules

1. If a complete provision is short enough, create one `whole_provision` chunk.
2. For long provisions, split first on natural subdivisions such as paragraphs or lettered clauses.
3. A token-window fallback may be used only when natural subdivisions remain too large.
4. A fallback window must not cross a provision boundary. The initial target is 350-600 tokens, with a maximum of 800 tokens and up to 80 tokens of overlap.
5. Token limits are provisional until the embedding and generation models are selected. Record the tokenizer name with every measured token count.
6. Every chunk inherits document ID, provision ID, scope, legal status, answer-use mode, topics, and last-checked date.
7. Chunk text must be reconstructable from the parent provision plus the recorded normalization rules.

## Scope and answer eligibility

Document eligibility is necessary but not sufficient. Default answer eligibility for a chunk requires all of the following:

1. The document is an answer-eligible candidate.
2. The provision has `scope_status=supported`.
3. The provision's `answer_use_mode=default_answer`.
4. The source copy is sufficiently verified.
5. The provision is not historical, expired, or limited to a different year.
6. No blocking quality flag is present.
7. The retrieval and citation-verification stages find sufficient supporting evidence.

Historical or time-bound material may be retrieved only when the user's question expressly asks about the applicable historical period.

## Topic taxonomy rules

- Topic IDs are stable machine identifiers and must not be silently renamed.
- A provision may have multiple topic IDs.
- `consumer.online_transactions` is supported for ordinary covered transactions.
- `consumer.criminal_online_fraud` and `consumer.data_privacy` remain excluded and should trigger referral or partial-answer handling.
- Exact current regional wage amounts remain excluded even though the general wage-setting framework is supported.
- Topic labels used for provision tagging must come from `topic_taxonomy.csv`.

## Identifiers and versioning

- Document IDs continue the canonical manifest IDs, such as `LAB_CODE_2022`.
- Provision IDs use `<document_id>__<normalized_locator>`, for example `LAB_CODE_2022__art_87`.
- Child provision IDs append the child locator, for example `RA_7394_1992__art_4__par_a`.
- Chunk IDs append a stable four-digit sequence, for example `LAB_CODE_2022__art_87__chunk_0001`.
- Text offsets are zero-based and end-exclusive. A complete 458-character provision therefore uses start `0` and end `458`.
- Cleaning rules use semantic versions. The initial value is `1.0.0`.
- Reprocessing with changed rules creates a new derived version. It does not overwrite raw evidence.

## Quality flags

Blocking flags prevent default answer eligibility:

- `unresolved_replacement_character`
- `ocr_low_confidence_critical_text`
- `provision_boundary_uncertain`
- `source_locator_missing`
- `official_text_comparison_pending`
- `legal_status_review_required`

Non-blocking flags communicate limitations:

- `pdf_text_glyph_repair_visual_verified`
- `image_only_pdf`
- `rotated_page`
- `multiple_printed_pages_per_pdf_page`
- `manual_transcription_sample`
- `footnotes_present`
- `table_structure_present`

## Required validation before Item 7 output is accepted

- IDs are unique and follow the naming rules.
- Every provision references an existing document.
- Every chunk references an existing provision and the same document.
- Every parent provision exists.
- Every topic ID exists in the taxonomy.
- Every document ID, raw-file path, official source URL, and retrieval URL matches the canonical manifest, and every recorded raw file exists.
- All answer-eligible provisions are supported, verified, current for the requested use, and free of blocking flags.
- Page ranges and source offsets are ordered and non-negative.
- `verbatim_text`, `normalized_text`, and `search_text` are nonempty for completed provisions.
- No completed text contains `U+FFFD`.
- A chunk cannot be more permissive than its parent provision.
- Historical, explanatory, corroboration-only, and time-bound records cannot enter the default current-law index.

## Storage formats

- CSV remains suitable for small manifests, controlled vocabularies, and human review tables.
- JSONL is used for sample records and pipeline inspection because it handles arrays and nested source locators clearly.
- Parquet is the preferred bulk output for processed documents, provisions, and chunks.
- The application database may later import these records, but it is not the canonical raw evidence store.
- Embeddings are rebuildable derivatives and should be stored separately from the legal text and source manifests.

## Contract samples

The `samples/` directory contains three document records, three provision records, and corresponding example retrieval chunks:

1. A text-based Labor Code PDF provision with visual glyph verification.
2. A Supreme Court E-Library Consumer Act HTML provision.
3. A manually verified contract sample from the rotated, image-only DTI Consumer Act IRR.

These samples test the contract. They are not the completed Item 7 corpus.

## Validation

Run:

```powershell
& .\dataset\data_contract\scripts\validate_item6_contract.ps1
```

The validator checks JSON syntax, required fields, identifiers, controlled values, topic references, parent-child references, eligibility constraints, quality flags, manifest provenance, and raw-file existence.
