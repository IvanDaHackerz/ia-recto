#!/usr/bin/env python3
"""Validate Item 8 outputs and enforce discovery-only answer safety."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.dataset_root.resolve()
    output = root / "processed" / "item8"
    errors: list[str] = []
    warnings: list[str] = []

    required = [
        "candidate_documents.jsonl", "candidate_documents.parquet", "candidate_review_queue.csv",
        "canonical_matches.csv", "internal_duplicates.csv", "missing_markdown.csv", "filter_summary.json"
    ]
    for name in required:
        if not (output / name).exists():
            errors.append(f"Missing output: {name}")
    if errors:
        records = []
    else:
        records = load_jsonl(output / "candidate_documents.jsonl")

    ids = [r.get("candidate_id") for r in records]
    bettergov_ids = [r.get("bettergov_id") for r in records]
    if len(ids) != len(set(ids)):
        errors.append("candidate_id values are not unique")
    if len(bettergov_ids) != len(set(bettergov_ids)):
        errors.append("bettergov_id values are not unique")

    allowed_categories = {"statutes", "executive"}
    valid_priorities = {"high", "medium", "boundary_review", "low"}
    for index, record in enumerate(records, 1):
        prefix = f"record {index} ({record.get('bettergov_id')})"
        if record.get("category") not in allowed_categories:
            errors.append(f"{prefix}: disallowed category {record.get('category')}")
        if record.get("source") in {"juris", "consti"}:
            errors.append(f"{prefix}: excluded source entered queue")
        if record.get("discovery_status") != "unverified_discovery":
            errors.append(f"{prefix}: invalid discovery_status")
        if record.get("permitted_use") != "discovery_only":
            errors.append(f"{prefix}: permitted_use is not discovery_only")
        if record.get("answer_eligible") is not False:
            errors.append(f"{prefix}: answer_eligible must be false")
        if record.get("needs_official_source_verification") is not True:
            errors.append(f"{prefix}: official verification flag must be true")
        if record.get("human_decision") != "pending":
            errors.append(f"{prefix}: human_decision must begin as pending")
        if record.get("review_priority") not in valid_priorities:
            errors.append(f"{prefix}: invalid review_priority")
        if not record.get("supported_topic_matches") and not record.get("core_anchor_domains"):
            errors.append(f"{prefix}: no supported topic or core anchor")

    if (output / "candidate_documents.parquet").exists():
        parquet_count = pq.ParquetFile(output / "candidate_documents.parquet").metadata.num_rows
        if parquet_count != len(records):
            errors.append(f"Parquet count {parquet_count} differs from JSONL count {len(records)}")
    else:
        parquet_count = 0

    queue_count = 0
    if (output / "candidate_review_queue.csv").exists():
        with (output / "candidate_review_queue.csv").open(encoding="utf-8-sig", newline="") as handle:
            queue_rows = list(csv.DictReader(handle))
        queue_count = len(queue_rows)
        if queue_count != len(records):
            errors.append(f"Review queue count {queue_count} differs from JSONL count {len(records)}")

    summary = {}
    if (output / "filter_summary.json").exists():
        summary = json.loads((output / "filter_summary.json").read_text(encoding="utf-8"))
        expected = summary.get("results", {}).get("candidate_documents")
        if expected != len(records):
            errors.append(f"Summary candidate count {expected} differs from JSONL count {len(records)}")

    report = {
        "item": 8,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not errors else "failed",
        "counts": {
            "candidate_documents": len(records),
            "parquet_rows": parquet_count,
            "review_queue_rows": queue_count,
            "domains": dict(Counter(r.get("predicted_domain") for r in records)),
            "priorities": dict(Counter(r.get("review_priority") for r in records))
        },
        "checks": {
            "unique_ids": len(ids) == len(set(ids)),
            "discovery_only_gate": all(r.get("permitted_use") == "discovery_only" for r in records),
            "answer_eligible_false_gate": all(r.get("answer_eligible") is False for r in records),
            "official_verification_gate": all(r.get("needs_official_source_verification") is True for r in records),
            "jurisprudence_excluded": all(r.get("source") != "juris" for r in records),
            "constitution_excluded": all(r.get("source") != "consti" for r in records)
        },
        "warnings": warnings,
        "errors": errors
    }
    (output / "validation_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
