# Remaining independent review

No human authorship, annotation, legal review or adviser approval has been filled in by Codex.

## Independent classifier evaluation

The 100 blank records in human_gold_intake.jsonl are an intake form, not a dataset. A human author writes new English and Taglish questions without copying or lightly rewriting our inspected examples. A human annotator fills the primary and scope labels and records actual IDs/dates. Use all four primary labels, all three scope labels, short/incomplete questions and typing variation. Keep related variants under one scenario family. Do not tune on these records. At least 100 completed rows are required by the current project plan.

Run dataset/pipelines/item10/validate_independent_gold.py with --input and --report. The validator rejects missing provenance, AI writing, direct overlap, duplicate rows and inconsistent labels. Passing checks does not prove authorship or annotation quality. Human near-duplicate and label review, a recorded checksum lock, and formal target approval still precede a one-time independent evaluation.

## Legal source review

source-repairs/final_pay_text_repairs.jsonl has four AI visual-comparison proposals, retaining old text, proposed text and page-image hashes. The official PDF was inspected on both pages. These proposals are not human approval and remain excluded from the default index.

source-repairs/dti_structure_repairs.jsonl reconstructs 29 sections from the 31 incorrectly split original records. It keeps cross-references inside their actual sections and maps OCR Rule Ill to Rule III by its MEDIATION heading. Full text comparison is still needed; these candidates remain excluded. The original 258-row review queue and 20 canonical files are unchanged. source_review_intake.jsonl gives the complete provision text and page locators for that review.

The stored MO 28 text still needs an official full-text copy: its phrase all employees are hereby required to pay appears suspect and must not be silently corrected by assumption. Its Lawphil watermark also entered the extracted text. The Senate official metadata page alone does not verify the operative text. Current-year thirteenth-month guidance still needs confirmation.

## Currentness and contact verification

public_source_audit_network.json records all 39 attempted official-source/contact URLs. Access checks and literal matches are diagnostics, not legal-currentness certification. Confirm substantive content and replacements using official sources. Keep unsuccessful/ambiguous fields unverified. Existing contact and legal-status verification dates have not been silently renewed.

## Formal acceptance

The team/adviser records target approval. The project proposal requires a licensed Philippine legal professional to review selected answers when an answer pipeline exists. Codex cannot supply either person's approval. Item 12, answer generation and deployment have not been started.
