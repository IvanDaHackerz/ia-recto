#!/usr/bin/env python3
"""Validate Item 9 labels, group-safe splits, referrals, and review gates."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> int:
    dataset_root = Path(__file__).resolve().parents[2]
    output = dataset_root / "processed" / "item9"
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        "classifier_questions.csv", "classifier_questions.jsonl", "classifier_questions.parquet",
        "referral_directory.csv", "dataset_summary.json"
    ]
    for name in required:
        if not (output / name).exists():
            errors.append(f"Missing output: {name}")
    if errors:
        questions: list[dict] = []
        referrals: list[dict] = []
        taxonomy: list[dict] = []
    else:
        questions = load_jsonl(output / "classifier_questions.jsonl")
        with (output / "referral_directory.csv").open(encoding="utf-8-sig", newline="") as handle:
            referrals = list(csv.DictReader(handle))
        with (dataset_root / "data_contract" / "topic_taxonomy.csv").open(encoding="utf-8-sig", newline="") as handle:
            taxonomy = list(csv.DictReader(handle))

    topic_rows = {r["topic_id"]: r for r in taxonomy}
    topic_ids = set(topic_rows)
    referral_ids = {r["referral_id"] for r in referrals}
    if len(referral_ids) != len(referrals):
        errors.append("Referral IDs are not unique")
    question_ids = [q.get("question_id") for q in questions]
    if len(question_ids) != len(set(question_ids)):
        errors.append("Question IDs are not unique")
    normalized_texts = [" ".join(str(q.get("question_text", "")).lower().split()) for q in questions]
    if len(normalized_texts) != len(set(normalized_texts)):
        errors.append("Question text contains exact normalized duplicates")

    valid_primary = {"labor", "consumer", "mixed", "out_of_scope"}
    valid_scope = {"fully_supported", "partially_supported", "unsupported"}
    valid_split = {"train", "validation", "test"}
    group_splits: dict[str, set[str]] = defaultdict(set)
    for q in questions:
        qid = q.get("question_id", "unknown")
        group_splits[str(q.get("scenario_group_id"))].add(str(q.get("split")))
        if q.get("primary_label") not in valid_primary:
            errors.append(f"{qid}: invalid primary_label")
        if q.get("scope_label") not in valid_scope:
            errors.append(f"{qid}: invalid scope_label")
        if q.get("split") not in valid_split:
            errors.append(f"{qid}: invalid split")
        supported = q.get("supported_topic_ids", [])
        excluded = q.get("excluded_topic_ids", [])
        if set(supported + excluded) - topic_ids:
            errors.append(f"{qid}: unknown topic ID")
        if any(topic_rows[t]["scope_status"] != "supported" for t in supported):
            errors.append(f"{qid}: supported_topic_ids contains a non-supported topic")
        if any(topic_rows[t]["scope_status"] != "excluded" for t in excluded):
            errors.append(f"{qid}: excluded_topic_ids contains a non-excluded topic")
        if set(q.get("referral_ids", [])) - referral_ids:
            errors.append(f"{qid}: unknown referral ID")
        if q.get("annotation_status") != "machine_generated_needs_human_review":
            errors.append(f"{qid}: synthetic review gate is missing")
        if q.get("primary_label") == "labor" and (not supported or not all(t.startswith("labor.") for t in supported) or excluded):
            errors.append(f"{qid}: labor label/topic inconsistency")
        if q.get("primary_label") == "consumer" and (not supported or not all(t.startswith("consumer.") for t in supported) or excluded):
            errors.append(f"{qid}: consumer label/topic inconsistency")
        if q.get("primary_label") == "out_of_scope" and (supported or not excluded or q.get("scope_label") != "unsupported"):
            errors.append(f"{qid}: out-of-scope label/topic inconsistency")
        if q.get("primary_label") == "mixed":
            two_supported_domains = {t.split(".", 1)[0] for t in supported} == {"labor", "consumer"}
            partial = bool(supported and excluded)
            if not (two_supported_domains or partial):
                errors.append(f"{qid}: mixed record lacks two supported domains or a supported/excluded combination")
    leaking_groups = [group for group, splits in group_splits.items() if len(splits) != 1]
    if leaking_groups:
        errors.append(f"Scenario-group leakage across splits: {len(leaking_groups)} groups")

    for label in valid_primary:
        for split in valid_split:
            if not any(q["primary_label"] == label and q["split"] == split for q in questions):
                errors.append(f"No {label} records in {split} split")
    represented_topics = {topic for q in questions for topic in q["supported_topic_ids"] + q["excluded_topic_ids"]}
    missing_topics = sorted(topic_ids - represented_topics)
    if missing_topics:
        errors.append(f"Taxonomy topics missing from questions: {missing_topics}")

    for referral in referrals:
        rid = referral["referral_id"]
        mapped = set(filter(None, referral["topic_ids"].split("|")))
        if mapped - topic_ids:
            errors.append(f"{rid}: unknown mapped topic")
        if not referral["verification_source_url"].startswith("https://"):
            errors.append(f"{rid}: missing HTTPS verification source")
        if not referral["last_verified"]:
            errors.append(f"{rid}: missing last_verified")
        if "official_domain_only" in referral["verification_status"] and (referral["email"] or referral["phone"]):
            errors.append(f"{rid}: unverified contact details should be blank")

    parquet_rows = 0
    csv_rows = 0
    if (output / "classifier_questions.parquet").exists():
        parquet_rows = pq.ParquetFile(output / "classifier_questions.parquet").metadata.num_rows
        if parquet_rows != len(questions):
            errors.append("Parquet and JSONL question counts differ")
    if (output / "classifier_questions.csv").exists():
        with (output / "classifier_questions.csv").open(encoding="utf-8-sig", newline="") as handle:
            csv_rows = sum(1 for _ in csv.DictReader(handle))
        if csv_rows != len(questions):
            errors.append("CSV and JSONL question counts differ")

    report = {
        "item": 9,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not errors else "failed",
        "counts": {
            "questions": len(questions), "csv_rows": csv_rows, "parquet_rows": parquet_rows,
            "scenario_groups": len(group_splits), "referrals": len(referrals),
            "labels": dict(sorted(Counter(q.get("primary_label") for q in questions).items())),
            "splits": dict(sorted(Counter(q.get("split") for q in questions).items())),
            "topics_represented": len(represented_topics)
        },
        "checks": {
            "unique_question_ids": len(question_ids) == len(set(question_ids)),
            "unique_question_text": len(normalized_texts) == len(set(normalized_texts)),
            "group_safe_splits": not leaking_groups,
            "all_taxonomy_topics_represented": not missing_topics,
            "all_synthetic_rows_human_review_gated": all(q.get("annotation_status") == "machine_generated_needs_human_review" for q in questions),
            "referral_sources_have_freshness_dates": all(r.get("last_verified") for r in referrals)
        },
        "warnings": warnings,
        "errors": errors
    }
    (output / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
