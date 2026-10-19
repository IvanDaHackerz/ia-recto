# Recto & Co. Legal Canonical Sources

This directory contains the frozen source documents selected for the Recto & Co. Legal MVP.

Current project status: Items 1–9 are implemented. This directory remains the controlled source layer for the Item 7 legal records and the future Item 11 retrieval index. BetterGov candidates and Item 9 classifier questions do not become canonical legal authority merely by being selected or labeled.

## Directory policy

- `raw/` contains source files exactly as retrieved. Do not edit, reformat, or overwrite them.
- `manifests/canonical_documents.csv` records provenance, source locations, verification state, answer eligibility, and intended use.
- Cleaned text, section chunks, summaries, embeddings, and other derived data must be written outside `raw/`.
- A changed upstream document must be stored as a new version. Never silently replace an existing raw file.

## Source hierarchy

1. Official Gazette or official printed publication
2. Issuing agency publication
3. Supreme Court E-Library
4. Official document retrieved through an institutional mirror
5. BetterGov or Lawphil discovery copy

Lower-ranked copies may help locate or compare documents, but they must not independently support substantive answers when the manifest marks them as ineligible.

## Verification statuses

- `verified_title_and_citation`: The retrieved official page contains the expected document number and title.
- `verified_pdf`: The file is a readable PDF with expected metadata and page count.
- `title_date_and_text_cross_check_pending`: The document identity is confirmed, but the preserved copy still requires full comparison with an official copy.

## Source-file handling

Every acquired file is tied to a document ID, official source URL, retrieval URL, local path, retrieval date, and verification status in the manifest. Keep the raw files read-only. If a file appears changed, damaged, or inconsistent with its recorded title and citation, quarantine it and reacquire it as a new version instead of silently replacing the stored copy.

## Current collection boundary

The collection now contains the core statutes and the targeted Item 4 implementing layer needed for the approved labor and consumer MVP scope. The implementing layer covers general Labor Code rules, termination, SEnA, final pay and certificates of employment, thirteenth-month-pay guidance, the Consumer Act IRR, the No Shortchanging Act IRR, DTI complaint procedure, and the Internet Transactions Act IRR. Item 5's legal-status audit is recorded in `manifests/legal_status_review.csv`, and amendment, implementation, renumbering, and current-use relationships are recorded in `manifests/legal_status_relationships.csv`.

The 2024 Workers' Statutory Monetary Benefits Handbook is preserved as secondary explanatory material only. It must not replace a controlling statute, rule, order, or advisory in an answer citation.

## Item 4 acquisition notes

- Ten targeted documents were added: six labor documents and four consumer documents.
- Labor Advisory No. 16, Series of 2025 is year-specific. Item 5 removed it from the default current-law answer set; it may be retrieved only for an expressly historical 2025 question unless the applicable current-year advisory is collected.
- Department Order No. 249, Series of 2025 is the selected SEnA procedure source. Older SEnA rules should not be presented as the current procedure.
- DOLE's historical download link for Department Order No. 119-12 currently returns a not-found page. It was not copied from an uncontrolled source. RA 10151 remains in the statutory collection, and the night-work implementing-order gap remains recorded for a future source refresh.
- A standalone official copy of the 1975-1987 thirteenth-month-pay implementing and revised guidelines was not located in a stable official repository. PD 851, Memorandum Order No. 28, the 2025 advisory, and the 2024 handbook are preserved; any historical-guideline proposition must remain unsupported until an official copy is obtained and verified.

## Important limitations

- The DOLE 2022 Labor Code PDF is an official DOLE publication retrieved from the ILO NATLEX mirror because DOLE blocked automated retrieval. Its official landing page remains recorded in the manifest.
- The preserved Memorandum Order No. 28 copy came from Lawphil because the Senate Legislative Reference Bureau blocked automated file retrieval. It is not answer-eligible until an official full-text comparison is completed.
- Exact regional minimum-wage amounts are excluded from MVP answers.
- Jurisprudence is not included in the MVP answer-authority layer.
