#!/usr/bin/env python3
"""Filter BetterGov metadata/text into an unverified Item 8 discovery queue."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


def norm(value: Any) -> str:
    text = str(value or "").lower().replace("ñ", "n")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compile_rules(raw: dict[str, list[str]]) -> dict[str, list[re.Pattern[str]]]:
    return {
        topic: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for topic, patterns in raw.items()
    }


def matches(rules: dict[str, list[re.Pattern[str]]], text: str) -> list[str]:
    return sorted(topic for topic, patterns in rules.items() if any(p.search(text) for p in patterns))


def canonical_aliases(manifest_path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    aliases: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
            document_id = row["document_id"]
            stem = Path(row["local_path"]).stem
            for alias in (document_id, stem, row["citation"], row["title"]):
                if alias:
                    aliases[norm(alias)] = document_id
            number_match = re.search(r"\b(ra|pd|mo)[ _.-]*(\d+)\b", norm(stem))
            if number_match:
                aliases[f"{number_match.group(1)} {number_match.group(2)}"] = document_id
    return aliases, rows


def citation_key(source: str, basename: str, title: str) -> str:
    joined = norm(f"{source} {basename} {title}")
    patterns = [
        (r"\bra[ _-]?(\d+)\b", "ra"),
        (r"\bpd[ _-]?(\d+)\b", "pd"),
        (r"\bmo[ _-]?(\d+)\b", "mo"),
        (r"\beo[ _-]?(\d+)\b", "eo"),
        (r"\bao[ _-]?(\d+)\b", "ao"),
    ]
    for pattern, prefix in patterns:
        found = re.search(pattern, joined)
        if found:
            return f"{prefix} {found.group(1)}"
    return ""


def local_markdown_path(markdown_root: Path, row: dict[str, Any]) -> Path:
    source = str(row.get("source") or "")
    basename = str(row.get("basename") or "")
    year_value = row.get("year")
    year = str(int(year_value)) if year_value is not None else "unknown"
    return markdown_root / source / year / f"{basename}.md"


def read_limited(path: Path, limit: int) -> tuple[str, bool]:
    if not path.exists():
        return "", False
    with path.open(encoding="utf-8", errors="replace") as handle:
        return handle.read(limit), True


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def existing_candidate_ids(path: Path) -> dict[str, str]:
    """Reuse already-issued IDs so existing review files remain compatible."""
    if not path.exists():
        return {}
    ids: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        ids[str(row["bettergov_id"])] = str(row["candidate_id"])
    return ids


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            cooked = dict(row)
            for field in fields:
                if isinstance(cooked.get(field), list):
                    cooked[field] = "|".join(cooked[field])
            writer.writerow(cooked)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    output = (args.output or dataset_root / "processed" / "item8").resolve()
    output.mkdir(parents=True, exist_ok=True)
    previous_candidate_ids = existing_candidate_ids(output / "candidate_documents.jsonl")
    rules_path = Path(__file__).with_name("filter_rules.json")
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    supported_rules = compile_rules(rules["supported_topics"])
    excluded_rules = compile_rules(rules["excluded_topics"])
    canonical_map, canonical_rows = canonical_aliases(
        dataset_root / "canonical_sources" / "manifests" / "canonical_documents.csv"
    )

    metadata_columns = ["id", "source", "category", "year", "month", "path", "basename", "title"]
    metadata = pq.read_table(dataset_root / "consolidated.parquet", columns=metadata_columns).to_pylist()
    source_counts = Counter(str(r["source"]) for r in metadata)
    category_counts = Counter(str(r["category"]) for r in metadata)

    enriched_columns = [
        "id", "title", "summary", "legislative_agenda_purpose", "key_provisions",
        "affected_laws_amendments", "tags", "keywords"
    ]
    enriched_table = pq.read_table(dataset_root / "repacts_with_summary.parquet", columns=enriched_columns)
    enriched: dict[str, dict[str, str]] = {}
    for row in enriched_table.to_pylist():
        enriched[str(row["id"])] = {
            "title": str(row.get("title") or ""),
            "text": "\n".join(str(row.get(col) or "") for col in enriched_columns[2:])
        }

    allowed = set(rules["allowed_categories"])
    excluded_sources = set(rules["excluded_sources"])
    minimum_year = int(rules["minimum_year"])
    body_limit = int(rules["body_character_limit"])
    title_weight = int(rules["title_weight"])
    body_weight = int(rules["body_weight"])
    core_anchor_weight = int(rules["core_anchor_weight"])
    relationship_weight = int(rules["relationship_weight"])
    markdown_root = dataset_root / "markdown"

    counters = Counter()
    candidates: list[dict[str, Any]] = []
    canonical_matches: list[dict[str, Any]] = []
    missing_markdown: list[dict[str, Any]] = []

    for row in metadata:
        source = str(row.get("source") or "")
        category = str(row.get("category") or "")
        year = int(row["year"]) if row.get("year") is not None else None
        if source in excluded_sources or category not in allowed:
            counters["excluded_category_or_source"] += 1
            continue
        if year is not None and year < minimum_year:
            counters["excluded_before_minimum_year"] += 1
            continue
        counters["eligible_metadata_records"] += 1

        display_title = str(row.get("title") or "")
        if source == "repacts":
            enriched_record = enriched.get(str(row["id"]), {})
            enriched_title = str(enriched_record.get("title") or "")
            if len(norm(enriched_title)) > len(norm(display_title)):
                display_title = enriched_title
            body_text = norm(enriched_record.get("text", ""))
            text_origin = "bettergov_enriched_metadata"
            text_available = bool(body_text)
        else:
            md_path = local_markdown_path(markdown_root, row)
            raw_text, text_available = read_limited(md_path, body_limit)
            body_text = norm(raw_text)
            text_origin = "bettergov_markdown_limited"
            if not text_available:
                missing_markdown.append({
                    "id": row["id"], "source": source, "year": year,
                    "basename": row.get("basename"), "expected_path": str(md_path)
                })

        title_text = norm(f"{display_title} {row.get('basename', '')}")

        title_topics = matches(supported_rules, title_text)
        body_topics = matches(supported_rules, body_text)
        supported_topics = sorted(set(title_topics) | set(body_topics))
        title_excluded = matches(excluded_rules, title_text)
        body_excluded = matches(excluded_rules, body_text)
        excluded_topics = sorted(set(title_excluded) | set(body_excluded))

        core_domains = []
        combined_text = f"{title_text} {body_text}"
        for domain, anchors in rules["core_anchors"].items():
            if any(re.search(pattern, combined_text, re.IGNORECASE) for pattern in anchors):
                core_domains.append(domain)
        relationship_hits = sorted(term for term in rules["relationship_terms"] if term in combined_text)
        score = (
            title_weight * len(title_topics)
            + body_weight * len(set(body_topics) - set(title_topics))
            + core_anchor_weight * len(core_domains)
            + relationship_weight * min(1, len(relationship_hits))
        )
        relationship_candidate = bool(core_domains and relationship_hits)
        qualifies = bool(title_topics or len(body_topics) >= 2 or score >= 6 or relationship_candidate)
        if not qualifies:
            counters["not_relevant_by_rules"] += 1
            continue

        key = citation_key(source, str(row.get("basename") or ""), display_title)
        canonical_id = canonical_map.get(key, "")
        if canonical_id:
            canonical_matches.append({
                "bettergov_id": row["id"], "canonical_document_id": canonical_id,
                "citation_key": key, "source": source, "year": year,
                "title": display_title, "dedup_action": "excluded_from_candidate_queue"
            })
            counters["canonical_duplicates"] += 1
            continue

        labor_topics = [x for x in supported_topics if x.startswith("labor.")]
        consumer_topics = [x for x in supported_topics if x.startswith("consumer.")]
        if labor_topics and consumer_topics:
            predicted_domain = "mixed"
        elif labor_topics or "labor" in core_domains:
            predicted_domain = "labor"
        elif consumer_topics or "consumer" in core_domains:
            predicted_domain = "consumer"
        else:
            predicted_domain = "undetermined"

        if excluded_topics:
            review_priority = "boundary_review"
            scope_prediction = "mixed_or_excluded_review"
        elif score >= 12:
            review_priority = "high"
            scope_prediction = "plausibly_in_scope"
        elif score >= 7:
            review_priority = "medium"
            scope_prediction = "plausibly_in_scope"
        else:
            review_priority = "low"
            scope_prediction = "manual_scope_review"

        bettergov_id = str(row["id"])
        candidate_id = previous_candidate_ids.get(bettergov_id, f"BG8_{len(candidates) + 1:06d}")
        record = {
            "candidate_id": candidate_id,
            "bettergov_id": row["id"],
            "source_provider_id": "BETTERGOV_LEGAL",
            "source": source,
            "category": category,
            "year": year,
            "month": row.get("month"),
            "path": row.get("path"),
            "basename": row.get("basename"),
            "title": display_title,
            "citation_key": key,
            "predicted_domain": predicted_domain,
            "scope_prediction": scope_prediction,
            "review_priority": review_priority,
            "relevance_score": score,
            "supported_topic_matches": supported_topics,
            "excluded_topic_matches": excluded_topics,
            "core_anchor_domains": sorted(core_domains),
            "relationship_term_matches": relationship_hits,
            "discovery_text_origin": text_origin,
            "discovery_text_available": text_available,
            "discovery_status": "unverified_discovery",
            "permitted_use": "discovery_only",
            "answer_eligible": False,
            "needs_official_source_verification": True,
            "canonical_duplicate": False,
            "human_decision": "pending",
            "filter_version": rules["filter_version"],
            "status_as_of": rules["status_as_of"]
        }
        candidates.append(record)

    # Prefer citation identity. Use a title only when it is long and descriptive;
    # BetterGov has many unrelated records titled only "MALACAÑANG" or "Section 1.".
    deduped: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    internal_duplicates: list[dict[str, Any]] = []
    generic_titles = {
        "malaca ang", "malacanang", "section 1", "section 2", "whereas",
        "eighth congress", "executive order", "presidential decree"
    }
    for record in sorted(candidates, key=lambda r: (-r["relevance_score"], str(r["bettergov_id"]))):
        title_key = norm(record["title"])
        citation = str(record.get("citation_key") or "")
        if citation:
            dedupe_key = f"citation:{citation}"
        elif len(title_key) >= 30 and title_key not in generic_titles:
            dedupe_key = f"title:{record['year']}:{title_key}"
        else:
            dedupe_key = f"id:{record['bettergov_id']}"
        if dedupe_key in seen:
            internal_duplicates.append({
                "bettergov_id": record["bettergov_id"],
                "kept_bettergov_id": seen[dedupe_key],
                "year": record["year"], "title": record["title"],
                "dedupe_key": dedupe_key,
                "dedup_action": "excluded_from_candidate_queue"
            })
            continue
        seen[dedupe_key] = str(record["bettergov_id"])
        deduped.append(record)

    candidates = sorted(deduped, key=lambda r: (
        {"high": 0, "medium": 1, "boundary_review": 2, "low": 3}[r["review_priority"]],
        -r["relevance_score"], str(r["title"])
    ))
    write_jsonl(output / "candidate_documents.jsonl", candidates)
    if candidates:
        pq.write_table(pa.Table.from_pylist(candidates), output / "candidate_documents.parquet", compression="zstd")

    queue_fields = [
        "candidate_id", "bettergov_id", "review_priority", "predicted_domain",
        "scope_prediction", "relevance_score", "year", "source", "category", "title",
        "supported_topic_matches", "excluded_topic_matches", "core_anchor_domains",
        "relationship_term_matches", "discovery_status", "permitted_use", "answer_eligible",
        "needs_official_source_verification", "human_decision"
    ]
    write_csv(output / "candidate_review_queue.csv", candidates, queue_fields)
    write_csv(output / "canonical_matches.csv", canonical_matches, [
        "bettergov_id", "canonical_document_id", "citation_key", "source", "year", "title", "dedup_action"
    ])
    write_csv(output / "internal_duplicates.csv", internal_duplicates, [
        "bettergov_id", "kept_bettergov_id", "year", "title", "dedupe_key", "dedup_action"
    ])
    write_csv(output / "missing_markdown.csv", missing_markdown, [
        "id", "source", "year", "basename", "expected_path"
    ])

    priority_counts = Counter(r["review_priority"] for r in candidates)
    domain_counts = Counter(r["predicted_domain"] for r in candidates)
    topic_counts = Counter(topic for r in candidates for topic in r["supported_topic_matches"])
    excluded_topic_counts = Counter(topic for r in candidates for topic in r["excluded_topic_matches"])
    summary = {
        "item": 8,
        "filter_version": rules["filter_version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status_as_of": rules["status_as_of"],
        "input": {
            "consolidated_rows": len(metadata),
            "source_counts": dict(sorted(source_counts.items())),
            "category_counts": dict(sorted(category_counts.items())),
            "canonical_documents": len(canonical_rows),
            "minimum_year": minimum_year
        },
        "results": {
            "eligible_metadata_records": counters["eligible_metadata_records"],
            "candidate_documents": len(candidates),
            "canonical_duplicates_removed": len(canonical_matches),
            "internal_duplicates_removed": len(internal_duplicates),
            "missing_markdown_files": len(missing_markdown),
            "review_priority_counts": dict(sorted(priority_counts.items())),
            "predicted_domain_counts": dict(sorted(domain_counts.items())),
            "supported_topic_counts": dict(topic_counts.most_common()),
            "excluded_topic_counts": dict(excluded_topic_counts.most_common())
        },
        "safety": {
            "all_candidates_discovery_only": True,
            "all_candidates_answer_eligible_false": True,
            "official_source_verification_required": True,
            "jurisprudence_excluded": True,
            "constitutions_excluded": True,
            "candidate_text_not_copied_to_outputs": True
        }
    }
    (output / "filter_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary["results"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
