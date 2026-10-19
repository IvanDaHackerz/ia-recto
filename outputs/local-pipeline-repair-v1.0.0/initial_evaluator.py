"""Frozen, network-free classifier/retrieval/verifier development evaluation."""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
from unittest.mock import patch
import numpy as np

from backend.normalization_metrics import assess, summarize_path
from backend.terminal_test import ROOT, inspect_question, load_runtime


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def prepare(target):
    if target.exists():
        raise ValueError("Use a new immutable case directory")
    target.mkdir(parents=True)
    source = ROOT / "outputs/normalization-evaluation-v2.0.0/cases.jsonl"
    cases = rows(source)
    original_hash = sha(source)
    additions = []
    labor, excluded = "hindi binayaran ang overtime ko", "ayaw ibalik ng landlord ang rental deposit"
    for conjunction in ("at", "and", "pero", "but"):
        for i, (a, b) in enumerate(((labor, excluded), (excluded, labor))):
            additions.append((f"joined_{conjunction}_{i}", "joined_landlord", "Private employee ako. " + a + " " + conjunction + " " + b + ".", "mixed", "partially_supported", ["labor"], True, "en_tl"))
    additions += [
        ("joined_english", "joined_landlord", "My private employer owes wages and will not return my rental deposit as my landlord.", "mixed", "partially_supported", ["labor"], True, "en"),
        ("joined_both_supported", "joined_supported", "Private employee ako. Hindi binayaran overtime ko at ayaw palitan ng store ang defective blender.", "mixed", "fully_supported", ["consumer", "labor"], False, "en_tl"),
        ("joined_negated_category", "joined_qualification", "Private employee ako at hindi government employee. Hindi binayaran overtime ko.", "labor", "fully_supported", ["labor"], False, "en_tl"),
        ("joined_unknown", "joined_unknown", "A store refuses my blender warranty at hindi pa resolved ang custody dispute ko.", None, None, [], False, "en_tl"),
    ]
    for identifier, family, question, primary, scope, domains, excluded, language in additions:
        route = "clarify" if primary is None else "retrieve_supported_components" if primary == "mixed" else "retrieve_supported_evidence"
        expected = {"case_id": identifier, "expected_primary": primary, "expected_scope": scope,
                    "expected_route": route, "expected_domains": domains, "expected_excluded": excluded,
                    "expected_clarification_reason": None, "language": language,
                    "relevant_ids": ["LAB_CODE_2022__art_87"] if primary else [], "concerns": [],
                    "retrieval_judgment": "known_relevant" if primary else "no_candidates", "origin": "ai_authored"}
        cases.append({"case_id": identifier, "base_case_id": family, "family_id": "joined:" + family,
                      "variation": "clear", "noise_profile": None, "question_text": question,
                      "source_case": expected, "origin": "AI_development_regression", "is_independent_human_gold": False})
    if len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case IDs")
    (target / "cases.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    save(target / "freeze.json", {"prepared_at_utc": datetime.now(timezone.utc).isoformat(),
         "cases_sha256": sha(target / "cases.jsonl"), "historical_cases_sha256": original_hash,
         "historical_inputs": 424, "new_regression_inputs": len(additions), "independent_human_questions": 0,
         "expected_labels_frozen_before_inference": True, "role": "reused_AI_development_plus_joined_regressions"})
    print("Frozen", len(cases), "local development inputs", flush=True)


def compact(packet):
    result = packet["result"]
    return {**{k: packet[k] for k in ("original_question_text", "normalization", "total_query_ms", "inspection_only")},
            "result": {**{k: result[k] for k in ("question_text", "routing", "decision", "excluded_components", "referral_ids", "answer_generation_allowed", "display_allowed", "deployment_allowed")},
                       "components": [{**{k: c[k] for k in ("component_id", "query", "allowed_domain", "retrieval_status", "retrieval_reason")},
                           "candidates": [{**{k: h[k] for k in ("provision_id", "chunk_id", "document_id", "score", "citation_display", "domains")},
                               "parent_text_sha256": hashlib.sha256(h["parent_text"].encode()).hexdigest()} for h in c["candidates"]],
                           "evidence_gate_reasons": sorted({reason for g in c["evidence_gates"] for reason in g["reasons"]})} for c in result["components"]]}}


def family_interval(observations, kind):
    groups = defaultdict(lambda: [0, 0])
    for row in observations:
        a = row["baseline"]["assessment"]
        if kind in {"primary_correct", "scope_correct"} and not a["labeled"]:
            continue
        values = a["retrieval"] if kind == "hit_at_5" else [{kind: a[kind]}]
        for value in values:
            groups[row["case"]["family_id"]][0] += int(value[kind])
            groups[row["case"]["family_id"]][1] += 1
    if not groups:
        return None
    matrix = np.array(list(groups.values()))
    rng = np.random.default_rng(20261019)
    samples = matrix[rng.integers(0, len(matrix), size=(2000, len(matrix)))].sum(axis=1)
    return {"low": float(np.quantile(samples[:, 0] / samples[:, 1], .025)),
            "high": float(np.quantile(samples[:, 0] / samples[:, 1], .975)), "families": len(groups),
            "meaning": "Family-cluster bootstrap on inspected AI development data; not independent population confidence."}


def execute(cases_dir, output):
    frozen = json.loads((cases_dir / "freeze.json").read_text(encoding="utf-8"))
    if sha(cases_dir / "cases.jsonl") != frozen["cases_sha256"] or output.exists():
        raise ValueError("Frozen cases changed or output already exists")
    cases = rows(cases_dir / "cases.jsonl")
    verifier = load_runtime()
    current = json.loads((ROOT / "CURRENT_ARTIFACTS.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True)
    shutil.copyfile(cases_dir / "cases.jsonl", output / "cases.jsonl")
    shutil.copyfile(cases_dir / "freeze.json", output / "freeze.json")
    protocol = {"version": output.name, "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        **{k: current[k] for k in ("classifier", "retrieval", "verifier")},
        "normalizer_version": "disabled_for_local_evaluation", "model": "none (no LLM)", "available_paths": ["baseline"],
        "evaluation_mode": "local_classifier_retrieval_verifier", "pipeline_executions": len(cases),
        "cases_sha256": frozen["cases_sha256"], "evaluator_sha256": sha(__file__), "llm_calls": 0,
        "independent_human_questions": 0, "answer_generation_allowed": False, "deployment_allowed": False,
        "timing_note": "Classification, retrieval and current-guidance preflight; diagnostic excerpt postflight is timed separately."}
    save(output / "protocol.json", protocol)
    observations = []
    # Fail rather than silently making any network call, even if future code changes.
    with patch("urllib.request.OpenerDirector.open", side_effect=RuntimeError("Network forbidden in local evaluation")):
        with (output / "observations.jsonl").open("x", encoding="utf-8") as stream:
            for number, case in enumerate(cases, 1):
                question = case["question_text"]
                packet = inspect_question(verifier, question, normalizer=None)
                result = packet["result"]
                assessment = assess(case, packet)
                cross_domain = sum(c["allowed_domain"] not in hit["domains"] for c in result["components"] for hit in c["candidates"])
                start = time.perf_counter()
                pre = verifier.preflight(question, mode="recorded_excerpt")
                draft = verifier.excerpt_draft(question, pre)
                checked = verifier.verify(question, draft, mode="recorded_excerpt") if draft["claims"] else None
                claims = checked["claim_results"] if checked else []
                evidence = {"cross_domain_candidate_leaks": cross_domain,
                    "live_permissions_closed": not any(result[k] for k in ("answer_generation_allowed", "display_allowed", "deployment_allowed")),
                    "recorded_excerpt_claims": len(claims), "recorded_excerpt_claims_passed": sum(c["passed"] for c in claims),
                    "recorded_excerpt_legal_support_claimed": bool(checked and checked["legal_support_verified"]),
                    "postflight_ms": (time.perf_counter() - start) * 1000,
                    "unreviewed_explanation_withheld": result["decision"] in {"clarify", "refer_out_of_scope", "insufficient_evidence"}}
                if cross_domain or not evidence["live_permissions_closed"] or evidence["recorded_excerpt_legal_support_claimed"]:
                    assessment["issues"].append("evidence_gate_violation")
                if any(not c["passed"] for c in claims):
                    assessment["issues"].append("recorded_excerpt_postflight_failed")
                observation = {"case": case, "baseline": {"packet": compact(packet), "assessment": assessment, "evidence": evidence}}
                stream.write(json.dumps(observation, ensure_ascii=False, allow_nan=False) + "\n"); stream.flush()
                observations.append(observation)
                if number % 50 == 0:
                    print(f"Checked {number}/{len(cases)} inputs; network/LLM calls 0", flush=True)
    verifier._begin_request()
    strata = {name: {"baseline": summarize_path(group, "baseline")} for name, group in {
        "all": observations, "clear": [r for r in observations if r["case"]["variation"] == "clear"],
        "noisy": [r for r in observations if r["case"]["variation"] == "noisy"],
        "original_424": observations[:424], "joined_regressions": observations[424:]}.items()}
    evidence = [r["baseline"]["evidence"] for r in observations]
    metrics = {"version": output.name, "role": "local_AI_development_pipeline_evaluation", "strata": strata,
        "counts": {"input_forms": len(observations), "families": len({r['case']['family_id'] for r in observations}), "independent_human_questions": 0},
        "evidence_checks": {"inputs": len(evidence), "live_permissions_closed": sum(e["live_permissions_closed"] for e in evidence),
            "unreviewed_explanation_withheld": sum(e["unreviewed_explanation_withheld"] for e in evidence),
            "cross_domain_candidate_leaks": sum(e["cross_domain_candidate_leaks"] for e in evidence),
            "recorded_excerpt_claims": sum(e["recorded_excerpt_claims"] for e in evidence),
            "recorded_excerpt_claims_passed": sum(e["recorded_excerpt_claims_passed"] for e in evidence),
            "recorded_excerpt_legal_support_claimed": sum(e["recorded_excerpt_legal_support_claimed"] for e in evidence)},
        "development_intervals": {key: family_interval(observations, key) for key in ("primary_correct", "scope_correct", "route_correct", "hit_at_5")},
        "llm_calls": 0, "generated_answers_evaluated": 0, "formal_acceptance_completed": False}
    save(output / "metrics.json", metrics)
    save(output / "errors.json", [{"case_id": r["case"]["case_id"], "question_text": r["case"]["question_text"],
        "expected": r["case"]["source_case"], **r["baseline"]} for r in observations if r["baseline"]["assessment"]["issues"]])
    save(output / "artifact_checksums.json", {p.name: sha(p) for p in output.iterdir() if p.is_file()})
    print(json.dumps({"scores": strata["all"]["baseline"], "evidence_checks": metrics["evidence_checks"]}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare"); prep.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("run"); run.add_argument("--cases", type=Path, required=True); run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare": prepare(args.output)
    else: execute(args.cases, args.output)
