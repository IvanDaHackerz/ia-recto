"""Validate Item 7 output relationships, source provenance, and safety gates."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{number}: invalid JSON: {exc}") from exc
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root, out = Path(args.project_root), Path(args.output_dir)
    errors: list[str] = []
    docs = read_jsonl(out / "documents.jsonl")
    provisions = read_jsonl(out / "provisions.jsonl")
    chunks = read_jsonl(out / "retrieval_chunks.jsonl")
    schemas = {
        "document": json.loads((root / "dataset/data_contract/schemas/legal_document.schema.json").read_text(encoding="utf-8")),
        "provision": json.loads((root / "dataset/data_contract/schemas/legal_provision.schema.json").read_text(encoding="utf-8")),
        "chunk": json.loads((root / "dataset/data_contract/schemas/retrieval_chunk.schema.json").read_text(encoding="utf-8")),
    }
    vocab = json.loads((root / "dataset/data_contract/controlled_vocabularies.json").read_text(encoding="utf-8"))
    topics = {r["topic_id"] for r in csv.DictReader((root / "dataset/data_contract/topic_taxonomy.csv").open(encoding="utf-8-sig", newline=""))}
    relationships = {r["relationship_id"] for r in csv.DictReader((root / "dataset/canonical_sources/manifests/legal_status_relationships.csv").open(encoding="utf-8-sig", newline=""))}
    manifest = {r["document_id"]: r for r in csv.DictReader((root / "dataset/canonical_sources/manifests/canonical_documents.csv").open(encoding="utf-8-sig", newline=""))}

    def check_shape(rows: list[dict], kind: str) -> None:
        required = set(schemas[kind]["required"])
        known = set(schemas[kind]["properties"])
        for row in rows:
            identity = row.get(f"{kind}_id") or row.get("document_id", "?")
            missing = required - row.keys()
            extra = row.keys() - known
            if missing: errors.append(f"{kind} {identity}: missing fields {sorted(missing)}")
            if extra: errors.append(f"{kind} {identity}: unknown fields {sorted(extra)}")

    check_shape(docs, "document"); check_shape(provisions, "provision"); check_shape(chunks, "chunk")
    if len(docs) != 20: errors.append(f"Expected 20 document records, found {len(docs)}")
    doc_by_id = {d["document_id"]: d for d in docs}
    prov_by_id = {p["provision_id"]: p for p in provisions}
    for label, values in (("document", list(doc_by_id)), ("provision", [p["provision_id"] for p in provisions]), ("chunk", [c["chunk_id"] for c in chunks])):
        if len(values) != len(set(values)): errors.append(f"Duplicate {label} IDs")

    all_flags = set(vocab["blocking_quality_flags"]) | set(vocab["nonblocking_quality_flags"])
    for doc in docs:
        mid = doc["document_id"]
        if mid not in manifest: errors.append(f"Unknown document {mid}"); continue
        row = manifest[mid]
        raw = root / doc["raw_local_path"]
        if not raw.exists(): errors.append(f"Missing raw source for {mid}"); continue
        expected_path = "dataset/canonical_sources/" + row["local_path"].replace("\\", "/")
        if doc["raw_local_path"] != expected_path: errors.append(f"Manifest path mismatch for {mid}")
        if doc["official_source_url"] != row["official_source_url"]: errors.append(f"Official source URL mismatch for {mid}")
        if doc["retrieval_url"] != row["retrieval_url"]: errors.append(f"Retrieval URL mismatch for {mid}")
        if doc["processing_state"] != "validated": errors.append(f"Document {mid} not marked validated")
        if mid == "DOLE_DO_249_25" and doc["effectivity_date"] != "2025-03-03": errors.append("DOLE_DO_249_25 effectivity date is missing or incorrect")

    for p in provisions:
        pid = p["provision_id"]
        if not re.fullmatch(r"[A-Z0-9_]+__[a-z0-9_]+(?:__[a-z0-9_]+)*", pid): errors.append(f"Invalid provision ID {pid}")
        if p["document_id"] not in doc_by_id: errors.append(f"Orphan provision {pid}"); continue
        if "\ufffd" in p["verbatim_text"] + p["normalized_text"] + p["search_text"]: errors.append(f"Unresolved U+FFFD {pid}")
        if p.get("heading") and len(p["heading"]) > 100: errors.append(f"Overlong extracted heading {pid}")
        suspicious_text = bool(re.search(r"(?i)\b(?:re st|em ploy|emplo yment|t he|pro vided|differenti al)\b|\w\s+-\s*\w", p["normalized_text"]))
        suspicious_label = bool(re.search(r"(?i)^(?:ART(?:ICLE)?\.?|SECTION|SEC\.)\s*\d+\s+\d+[.]", p["normalized_text"]))
        if (suspicious_text or suspicious_label) and "provision_boundary_uncertain" not in p["quality_flags"]:
            errors.append(f"Suspicious extraction is not quarantined {pid}")
        if "[UNRESOLVED_GLYPH]" in p["normalized_text"] and "unresolved_replacement_character" not in p["quality_flags"]:
            errors.append(f"Unresolved glyph placeholder is not flagged {pid}")
        unknown_topics = (set(p["supported_topics"]) | set(p["excluded_topics"])) - topics
        if unknown_topics: errors.append(f"Unknown topics {pid}: {sorted(unknown_topics)}")
        if set(p["relationship_ids"]) - relationships: errors.append(f"Unknown relationship {pid}")
        if set(p["quality_flags"]) - all_flags: errors.append(f"Unknown quality flag {pid}")
        blocking = set(p["quality_flags"]) & set(vocab["blocking_quality_flags"])
        if blocking and p["review_status"] != "human_review_required": errors.append(f"Blocking provision is not queued for human review {pid}")
        if p["document_id"] == "LAB_CODE_2022" and p["source_locator"]["pdf_page_start"] and p["source_locator"]["printed_page_start"] is None:
            errors.append(f"Labor Code printed-page locator missing {pid}")
        if p["ocr_used"] and p["provision_answer_eligible"]: errors.append(f"Unverified OCR is answer eligible: {pid}")
        if p["provision_answer_eligible"]:
            if not doc_by_id[p["document_id"]]["document_answer_eligible_candidate"]: errors.append(f"Provision exceeds document gate {pid}")
            if p["scope_status"] != "supported" or p["answer_use_mode"] != "default_answer": errors.append(f"Invalid answer gate {pid}")
            if set(p["quality_flags"]) & set(vocab["blocking_quality_flags"]): errors.append(f"Eligible provision has blocking flag {pid}")
            if p["review_status"] != "machine_validated": errors.append(f"Eligible provision lacks machine validation {pid}")
            if suspicious_text or suspicious_label: errors.append(f"Eligible provision retains suspicious extraction {pid}")

    for c in chunks:
        cid = c["chunk_id"]
        p = prov_by_id.get(c["provision_id"])
        if not p: errors.append(f"Orphan chunk {cid}"); continue
        start, end = c["normalized_char_start"], c["normalized_char_end"]
        if not (0 <= start < end <= len(p["normalized_text"])): errors.append(f"Invalid offsets {cid}"); continue
        if c["display_text"] != p["normalized_text"][start:end]: errors.append(f"Chunk text/offset mismatch {cid}")
        if c["character_count"] != len(c["display_text"]): errors.append(f"Chunk count mismatch {cid}")
        if c["answer_eligible"] and not p["provision_answer_eligible"]: errors.append(f"Chunk exceeds provision gate {cid}")

    if not any(p["document_id"] == "LAB_CODE_2022" and p["footnotes"] for p in provisions):
        errors.append("No Labor Code footnotes were preserved")
    if any("__occ_" in p["provision_id"] for p in provisions if p["document_id"] == "LAB_CODE_2022"):
        errors.append("Labor Code still contains duplicate/colliding article locators")

    report = {
        "item": 7, "validated_at": "2026-09-29", "contract_version": "1.0.0",
        "documents": len(docs), "provisions": len(provisions), "chunks": len(chunks),
        "answer_eligible_provisions": sum(bool(p["provision_answer_eligible"]) for p in provisions),
        "ocr_provisions_pending_human_review": sum(bool(p["ocr_used"] and p["review_status"] == "human_review_required") for p in provisions),
        "provisions_with_footnotes": sum(bool(p["footnotes"]) for p in provisions),
        "provisions_with_printed_page_locators": sum(p["source_locator"]["printed_page_start"] is not None for p in provisions),
        "provisions_quarantined_for_extraction_quality": sum("provision_boundary_uncertain" in p["quality_flags"] or "unresolved_replacement_character" in p["quality_flags"] for p in provisions),
        "errors": errors, "status": "passed" if not errors else "failed",
    }
    (out / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if errors:
        for error in errors[:100]: print("ERROR:", error)
        raise SystemExit(1)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
