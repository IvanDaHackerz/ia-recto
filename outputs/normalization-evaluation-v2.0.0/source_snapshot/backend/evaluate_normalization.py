"""Freeze and run a paired baseline/conditional-normalization development study."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from backend.classifier.contracts import strict_json
from backend.normalization_cases import ROOT, SOURCE, SEED, QUOTAS, build_cases, build_fresh_cases, build_repair_cases
from backend.normalization_metrics import assess, summarize

VERSION = "normalization-evaluation-v2.0.0"
PATHS = ("baseline", "normalized")


def read(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def rows(path):
    return [strict_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def jsonl(path, values):
    with Path(path).open("x", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


def prepare(output, fresh_after=None, suite="initial"):
    from backend.normalization import VERSION as normalizer_version, from_environment
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT / "outputs"):
        raise ValueError("Save this development study under the project outputs directory")
    current = read(ROOT / "CURRENT_ARTIFACTS.json")
    normalizer = from_environment()
    if not normalizer.provider or normalizer.provider.name != "together" or normalizer.provider.model != "openai/gpt-oss-120b":
        raise ValueError("This protocol requires the configured Together GPT-OSS 120B interpreter")
    parent = None
    if suite not in {"initial", "repair"} or (fresh_after and suite != "initial"):
        raise ValueError("Select either a repair replay or remaining-family selection")
    if fresh_after:
        parent = Path(fresh_after).resolve()
        for name, expected in read(parent / "artifact_checksums.json").items():
            source = (parent / name).resolve()
            if not source.is_relative_to(parent) or sha(source) != expected:
                raise ValueError("Earlier comparison artifact changed: " + name)
        excluded = {c["family_id"] for c in rows(parent / "cases.jsonl")}
        cases = build_fresh_cases(excluded)
    else:
        cases = build_repair_cases() if suite == "repair" else build_cases()
    base_count, input_count = len({c["base_case_id"] for c in cases}), len(cases)
    source_ids = {r["provision_id"] for r in rows(ROOT / current["retrieval"] / "records.jsonl")}
    for case in cases:
        expected = case["source_case"]
        judged = expected["relevant_ids"] + [pid for c in expected["concerns"] for pid in c["relevant_ids"]]
        if set(judged) - source_ids:
            raise ValueError("Frozen relevance judgment points outside the current retrieval index")
    output.mkdir(parents=True, exist_ok=False)
    protocol = {"version": VERSION, "role": "development", "prepared_at_utc": utc(),
                "classifier": current["classifier"], "retrieval": current["retrieval"], "verifier": current["verifier"],
                "normalizer_version": normalizer_version, "provider": normalizer.provider.name, "model": normalizer.provider.model,
                "base_questions": base_count, "input_forms": input_count, "pipeline_executions": 2 * input_count,
                "baseline_note": "Both paths use the pinned current classifier, including its local spelling features. Historical classifier/pipeline comparisons require matched earlier observations.",
                "maximum_llm_requests": input_count, "cost_stop_usd": .50,
                "pricing_usd_per_million_tokens": {"input": .15, "output": .60},
                "pricing_source": "https://docs.together.ai/docs/serverless/models",
                "pricing_verified_date": "2026-10-19", "generation_seed": SEED,
                "selection_quotas": None if parent or suite == "repair" else {str(k): v for k, v in QUOTAS.items()},
                "suite": suite,
                "suite_note": "Replay all 334 historical forms plus 90 new noisy partial-scope variants across 18 reused families; enriched AI development set, not an independent holdout" if suite == "repair" else None,
                "fresh_after": str(parent.relative_to(ROOT)).replace("\\", "/") if parent else None,
                "fresh_selection": "all recorded source families not selected in the earlier comparison; still previously inspected AI development material" if parent else None,
                "execution_order": "alternate baseline-first and normalized-first by input index",
                "semantic_review_protocol": "Codex AI audit of accepted rewrites using a queue without labels, predictions or metrics; not independent human review",
                "capture_development_diagnostics": True,
                "formal_acceptance_allowed": False, "answer_generation_allowed": False, "deployment_allowed": False}
    save(output / "protocol.json", protocol)
    save(output / "current_artifacts_snapshot.json", current)
    jsonl(output / "cases.jsonl", cases)
    save(output / "case_manifest.json", {
        "input_forms": input_count, "base_questions": base_count, "recorded_families": base_count,
        "suite_counts_base": dict(Counter(c["source_case"]["suite"] for c in cases if c["variation"] == "clear")),
        "noise_profile_counts": dict(Counter(c["noise_profile"] for c in cases if c["variation"] == "noisy")),
        "classified_inputs": sum(c["source_case"]["expected_primary"] is not None for c in cases),
        "clarification_inputs": sum(c["source_case"]["expected_primary"] is None for c in cases),
        "source_path": SOURCE, "source_sha256": sha(ROOT / SOURCE),
        "source_case_ids": [c["base_case_id"] for c in cases if c["variation"] == "clear"],
        "origin": "existing_AI_development_cases_and_new_reversible_synthetic_perturbations",
        "independent_human_questions": 0, "new_training_questions": 0,
        "note": "Recorded scenario families are clustering units, not a claim of semantic independence across source suites."})
    source_files = sorted((ROOT / "backend").rglob("*.py")) + [ROOT / "backend/classifier/config.json", ROOT / SOURCE]
    save(output / "freeze.json", {"frozen_at_utc": utc(), "status": "prepared_before_inference",
        "inputs_sha256": {name: sha(output / name) for name in ["cases.jsonl", "protocol.json", "case_manifest.json", "current_artifacts_snapshot.json"]},
        "runtime_source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in source_files},
        "runtime_artifact_manifest_sha256": {current[name] + "/artifact_checksums.json": sha(ROOT / current[name] / "artifact_checksums.json")
                                             for name in ["classifier", "retrieval", "verifier"]},
        "no_predictions_observed_by_this_run": True})
    return output


def verify_freeze(output):
    frozen = read(Path(output) / "freeze.json")
    for name, expected in frozen["inputs_sha256"].items():
        if sha(Path(output) / name) != expected:
            raise ValueError("Frozen study input changed: " + name)
    for field in ["runtime_source_sha256", "runtime_artifact_manifest_sha256"]:
        for name, expected in frozen[field].items():
            if sha(ROOT / name) != expected:
                raise ValueError("Frozen runtime/source changed: " + name)


def compact(packet):
    """Keep predictions, question hashes and candidate IDs; no duplicate law text."""
    result = packet["result"]
    if result is not None:
        kept = {k: result[k] for k in ["question_text", "question_sha256", "routing", "decision", "mode", "as_of",
                                      "answer_generation_allowed", "deployment_allowed", "display_allowed"]}
        kept["components"] = [{"query": c["query"], "allowed_domain": c["allowed_domain"],
                               "retrieval_status": c["retrieval_status"],
                               "candidates": [{k: h[k] for k in ["provision_id", "chunk_id", "score", "citation_display"]} for h in c["candidates"]],
                               "evidence_gate_reasons": sorted({reason for g in c["evidence_gates"] for reason in g["reasons"]})}
                              for c in result["components"]]
        kept["excluded_components"] = result["excluded_components"]
        packet = {**packet, "result": kept}
    return packet


def run(output):
    from backend.normalization import from_environment
    from backend.terminal_test import inspect_question, load_runtime
    output = Path(output)
    verify_freeze(output)
    if (output / "execution_started.json").exists():
        raise ValueError("Preserve earlier predictions; prepare a new run directory")
    protocol, cases = read(output / "protocol.json"), rows(output / "cases.jsonl")
    normalizer = from_environment()
    if (normalizer.provider.name, normalizer.provider.model) != (protocol["provider"], protocol["model"]):
        raise ValueError("Configured model differs from frozen protocol")
    normalizer.capture_diagnostics = True
    verifier = load_runtime()
    if any(verifier.policy[k] != protocol[k] for k in ["classifier", "retrieval"]):
        raise ValueError("Loaded stack differs from frozen study")
    verify_freeze(output)
    save(output / "execution_started.json", {"started_at_utc": utc(), "freeze_sha256": sha(output / "freeze.json")})
    observations, requests, cost, consecutive_unavailable = [], 0, 0.0, 0
    with (output / "observations.jsonl").open("x", encoding="utf-8") as stream:
        for index, case in enumerate(cases):
            if requests >= protocol["maximum_llm_requests"] or cost >= protocol["cost_stop_usd"]:
                raise ValueError("Study request/cost stop reached; partial observations preserved")
            observation = {"case": case}
            order = PATHS if index % 2 == 0 else tuple(reversed(PATHS))
            for path in order:
                # Labels, canonical/reference wording and relevance IDs never enter inference.
                packet = inspect_question(verifier, case["question_text"], normalizer=normalizer if path == "normalized" else None)
                observation[path] = {"packet": compact(packet), "assessment": assess(case, packet)}
            normalization = observation["normalized"]["packet"]["normalization"]
            requests += normalization["llm_calls"]
            usage = normalization["usage"]
            prices = protocol["pricing_usd_per_million_tokens"]
            cost += (usage.get("input_tokens", 0) * prices["input"] + usage.get("output_tokens", 0) * prices["output"]) / 1_000_000
            if normalization["llm_calls"] > 1:
                raise ValueError("More than one runtime normalization request")
            for path in PATHS:
                result = observation[path]["packet"]["result"]
                if result and any(result[k] for k in ["answer_generation_allowed", "display_allowed", "deployment_allowed"]):
                    raise ValueError("Live permission leak")
            observations.append(observation)
            stream.write(json.dumps(observation, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            consecutive_unavailable = consecutive_unavailable + 1 if normalization["status"] == "unavailable" else 0
            if consecutive_unavailable >= 5:
                raise ValueError("Five provider failures in a row; partial observations preserved")
            if (index + 1) % 10 == 0:
                print(f"Completed {index + 1}/{len(cases)} inputs / {2 * (index + 1)} pipeline executions; LLM requests {requests}; estimated cost ${cost:.4f}", flush=True)
    verify_freeze(output)
    # This queue deliberately excludes outcome metrics/labels for the AI audit.
    jsonl(output / "semantic_review_queue.jsonl", [
        {"case_id": r["case"]["case_id"], "reference_question": r["case"]["reference_question"],
         "typed_question": r["case"]["question_text"],
         "interpreted_question": r["normalized"]["packet"]["normalization"]["effective_question_text"]}
        for r in observations if r["normalized"]["packet"]["normalization"]["status"] == "applied"])
    save(output / "execution_completed.json", {"completed_at_utc": utc(), "input_forms": len(observations),
         "llm_requests": requests, "observations_sha256": sha(output / "observations.jsonl"),
         "semantic_review_queue_sha256": sha(output / "semantic_review_queue.jsonl")})
    print("Inference complete. Review semantic_review_queue.jsonl before opening performance metrics.", flush=True)


def percent(value):
    return "unavailable" if value is None else f"{100 * value:.1f}%"


def finalize(output):
    import csv
    output = Path(output)
    if any((output / filename).exists() for filename in ["metrics.json", "REPORT.md", "error_log.jsonl", "results.csv"]):
        raise ValueError("A finalized report already exists; preserve it")
    verify_freeze(output)
    completed = read(output / "execution_completed.json")
    for filename, key in [("observations.jsonl", "observations_sha256"), ("semantic_review_queue.jsonl", "semantic_review_queue_sha256")]:
        if sha(output / filename) != completed[key]:
            raise ValueError("Completed observation/audit queue changed")
    observations = rows(output / "observations.jsonl")
    if len(observations) != read(output / "protocol.json")["input_forms"]:
        raise ValueError("A partial run cannot be finalized as the full comparison")
    reviews = rows(output / "semantic_reviews.jsonl") if (output / "semantic_reviews.jsonl").exists() else []
    for review in reviews:
        if review["verdict"] not in {"equivalent", "meaning_changed", "uncertain"} or not review.get("reason"):
            raise ValueError("Invalid semantic verdict")
    metrics = summarize(observations, read(output / "protocol.json"), reviews)
    if metrics["semantic_review"]["pending"]:
        raise ValueError("Accepted rewrites still need their disclosed AI semantic audit")
    save(output / "metrics.json", metrics)
    review_map = {r["case_id"]: r for r in reviews}
    errors = []
    with (output / "results.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["case_id", "family_id", "variation", "noise_profile", "reference_question", "typed_question", "interpreted_question",
                  "expected_primary", "baseline_primary", "normalized_primary", "expected_scope", "baseline_scope", "normalized_scope",
                  "expected_route", "baseline_route", "normalized_route", "baseline_primary_correct", "normalized_primary_correct",
                  "baseline_primary_confidence", "normalized_primary_confidence", "baseline_scope_confidence", "normalized_scope_confidence",
                  "baseline_known_hit_at_5", "normalized_known_hit_at_5",
                  "baseline_scope_correct", "normalized_scope_correct", "baseline_ms", "normalized_ms", "normalizer_status",
                  "validation_failure", "llm_calls", "input_tokens", "output_tokens", "semantic_verdict", "semantic_reason", "issues"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for observation in observations:
            case = observation["case"]
            baseline, normalized = (observation[path]["assessment"] for path in PATHS)
            norm = observation["normalized"]["packet"]["normalization"]
            review = review_map.get(case["case_id"], {})
            issues = [path + ":" + issue for path in PATHS for issue in observation[path]["assessment"]["issues"]]
            if review.get("verdict") in {"meaning_changed", "uncertain"}:
                issues += ["semantic:" + review["verdict"]]
            row = {"case_id": case["case_id"], "family_id": case["family_id"], "variation": case["variation"], "noise_profile": case["noise_profile"],
                   "reference_question": case["reference_question"], "typed_question": case["question_text"],
                   "interpreted_question": norm["effective_question_text"], "expected_primary": case["source_case"]["expected_primary"],
                   "baseline_primary": baseline["predicted_primary"], "normalized_primary": normalized["predicted_primary"],
                   "expected_scope": case["source_case"]["expected_scope"], "baseline_scope": baseline["predicted_scope"], "normalized_scope": normalized["predicted_scope"],
                   "expected_route": case["source_case"]["expected_route"], "baseline_route": baseline["route"], "normalized_route": normalized["route"],
                   **{path + "_" + head + "_confidence": observation[path]["packet"]["result"]["routing"][head + "_confidence"]
                      if observation[path]["packet"]["result"] else None for path in PATHS for head in ["primary", "scope"]},
                   **{path + "_known_hit_at_5": all(item["hit_at_5"] for item in observation[path]["assessment"]["retrieval"])
                      if observation[path]["assessment"]["retrieval"] else None for path in PATHS},
                   "baseline_primary_correct": baseline["primary_correct"], "normalized_primary_correct": normalized["primary_correct"],
                   "baseline_scope_correct": baseline["scope_correct"], "normalized_scope_correct": normalized["scope_correct"],
                   "baseline_ms": observation["baseline"]["packet"]["total_query_ms"], "normalized_ms": observation["normalized"]["packet"]["total_query_ms"],
                   "normalizer_status": norm["status"], "validation_failure": norm.get("validation_failure"), "llm_calls": norm["llm_calls"],
                   "input_tokens": norm["usage"].get("input_tokens"), "output_tokens": norm["usage"].get("output_tokens"),
                   "semantic_verdict": review.get("verdict"), "semantic_reason": review.get("reason"), "issues": "|".join(issues)}
            writer.writerow({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v for k, v in row.items()})
            if issues:
                errors.append({"comparison": row, "baseline": observation["baseline"], "normalized": observation["normalized"]})
    if (output / "error_log.jsonl").exists():
        raise ValueError("A finalized report already exists; preserve it")
    jsonl(output / "error_log.jsonl", errors)
    lines = ["# Conditional normalization development comparison", "",
             f"{metrics['counts']['base_questions']} existing AI development questions, each clear and synthetically noisy: {metrics['counts']['input_forms']} inputs / {metrics['counts']['pipeline_executions']} pipeline executions. Not independent human gold.", "",
             "| Group | Measure | Baseline | Conditional LLM |", "|---|---|---:|---:|"]
    for group in ["clear", "noisy", "all"]:
        a, b = (metrics["strata"][group][p] for p in PATHS)
        for title, va, vb in [("Topic accuracy", a["primary"]["accuracy"]["value"], b["primary"]["accuracy"]["value"]),
                              ("Topic macro F1", a["primary"]["macro_f1"], b["primary"]["macro_f1"]),
                              ("Coverage accuracy", a["scope"]["accuracy"]["value"], b["scope"]["accuracy"]["value"]),
                              ("Coverage macro F1", a["scope"]["macro_f1"], b["scope"]["macro_f1"]),
                              ("Partial-support recall", a["partial_support_recall"], b["partial_support_recall"]),
                              ("Out-of-scope recall", a["out_of_scope_recall"], b["out_of_scope_recall"]),
                              ("Route match", a["route_match"]["value"], b["route_match"]["value"]),
                              ("Known-relevant Hit@5", a["known_relevant_hit_at_5"]["value"], b["known_relevant_hit_at_5"]["value"])]:
            lines.append(f"| {group} | {title} | {percent(va)} | {percent(vb)} |")
    cost, semantic = metrics["normalization"], metrics["semantic_review"]
    lines += ["", f"LLM requests: {cost['llm_requests']} (clear {cost['clear_llm_requests']}; noisy {cost['noisy_llm_requests']}).",
              f"Provider usage: {cost['input_tokens']} input / {cost['output_tokens_including_reasoning']} output tokens including reasoning. Estimated cost: ${cost['estimated_provider_cost_usd']:.6f}; usage complete: {cost['usage_complete']}.",
              "", f"Accepted rewrites audited by Codex AI: {semantic['reviewed']}. Verdicts: {semantic['verdict_counts']}. This is not an independent human meaning-change rate.",
              "", "## Paired uncertainty", "",
              "Differences are conditional minus baseline. Intervals resample recorded families, keeping clear/noisy variants paired. These describe this development sample."]
    for group in ["clear", "noisy", "all"]:
        delta = metrics["paired_differences"][group]["primary_correct"]
        interval = delta["family_cluster_bootstrap_95"]
        lines += [f"- {group} topic accuracy difference: {delta['difference'] * 100:+.1f} percentage points; 95% grouped interval {interval[0] * 100:+.1f} to {interval[1] * 100:+.1f}."]
    lines += ["", "## Files and interpretation", "", "`results.csv` contains every question side by side. `error_log.jsonl` includes either-path failures and semantic flags. `metrics.json` provides per-class precision/recall/F1, confusion matrices, label-confidence bins, latency, noise-profile results, denominators and paired intervals.", ""]
    lines += ["- " + text for text in metrics["limitations"]]
    lines += ["", "No classifier/normalizer tuning was performed during this frozen run. No website, legal-answer generation or deployment approval is granted by these results."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    save(output / "artifact_checksums.json", {p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name != "artifact_checksums.json"})
    print("Finalized development comparison: " + str(output / "REPORT.md"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fresh-after", type=Path, help="Prepare remaining recorded families after a completed comparison")
    parser.add_argument("--suite", choices=["initial", "repair"], default="initial")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare-only", action="store_true")
    modes.add_argument("--run-prepared", action="store_true")
    modes.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    if args.fresh_after and not args.prepare_only:
        parser.error("--fresh-after applies only to --prepare-only")
    if args.prepare_only: prepare(args.output, fresh_after=args.fresh_after, suite=args.suite)
    elif args.run_prepared: run(args.output)
    else: finalize(args.output)


if __name__ == "__main__":
    main()
