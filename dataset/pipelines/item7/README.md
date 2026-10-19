# Item 7 canonical extraction pipeline

This pipeline converts only the 20 files listed in `canonical_documents.csv` into the Item 6 document, provision, and retrieval-chunk contract. It does not scan the BetterGov corpus.

Current downstream role: Item 11 will index only retrieval chunks permitted by the provision and document safety fields produced here. OCR or extraction-quality records that still require human review must remain searchable only for review and must not support user-facing legal claims.

At runtime, the LLM will not read raw Item 7 files indiscriminately. The search layer retrieves a small set of eligible provisions, and the LLM may explain only the legal propositions supported by those retrieved records.

## Processing rules

- Raw canonical files are read-only inputs. Their document IDs, manifest paths, source URLs, and file existence are checked before output is accepted.
- Structural HTML extraction is used for official E-Library and Lawphil pages.
- Embedded PDF text is used where available.
- The four image-only PDFs are rendered and OCRed. Their provisions are marked `human_review_required` and cannot be answer eligible until compared with the official page image.
- DTI DAO 02 (1993) is rotated and split into its two printed pages per PDF page; both locators are retained.
- Text is split at article/section boundaries, with a documented page-level fallback for explanatory material.
- Topic labels implement the locked MVP scope. Ambiguous or excluded passages are not answer eligible.
- Long provisions are divided into retrieval chunks without changing the parent normalized text; every chunk stores exact character offsets.

## Outputs

The validated outputs are in `dataset/processed/item7/`:

- `documents.jsonl` / `documents.parquet`
- `provisions.jsonl` / `provisions.parquet`
- `retrieval_chunks.jsonl` / `retrieval_chunks.parquet`
- `extraction_report.csv`
- `ocr_review_queue.csv`, the exact OCR passages that still require comparison with the official page images
- `human_review_queue.csv`, covering OCR plus any text-PDF extraction quarantined by quality checks
- `validation_report.json`

JSONL is the lossless contract representation. In the flat Parquet mirrors, nested arrays and objects are stored as JSON strings for convenient Pandas loading.

## Reproduction order

1. Run `prepare_ocr.py` with the project root, Poppler `pdftoppm`, and a temporary work directory.
2. Run `ocr_images.mjs` with the generated OCR manifest, a local `eng.traineddata.gz`, and the bundled Node module directory.
3. Run `extract_canonical.py` with the OCR output and `dataset/processed/item7` as the output directory.
4. Run `validate_item7.py`.
5. Run `jsonl_to_parquet.py` after installing a Pandas Parquet engine such as `pyarrow`.

Pinned Python dependencies are recorded in `requirements.txt`; the OCR dependency is recorded in `package.json`. `ocr_model.json` records the OCR language model URL and checksum. `run_item7.ps1` checks that model checksum and runs the complete pipeline when supplied with Python, Node, Poppler, Node-module, and OCR-model locations.

The OCR images, OCR engine cache, and page-level TSV are temporary processing artifacts. The normalized records retain the PDF page, printed page when available, confidence, extraction method, footnotes, former Labor Code article numbers, and safety flags needed for later review.

The validator also rejects split article numbers, suspicious spacing in answer-eligible text, overlong headings, missing Labor Code printed-page locators, unquarantined glyph problems, and Labor Code locator collisions. Known unresolved PDF-text defects are placed in `human_review_queue.csv` and cannot enter the answer set.
