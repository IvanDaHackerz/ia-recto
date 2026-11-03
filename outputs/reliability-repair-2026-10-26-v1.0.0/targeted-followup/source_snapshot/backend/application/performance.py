"""Read measured, checksum-pinned development results. No inference or API calls."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVALUATION = ROOT / "outputs/normalization-evaluation-v2.0.0"
# Pins the existing frozen package rather than accepting client-supplied data.
METRICS_SHA = "94f48722c8a55f5de6e625e7e5fdefc07020b9284538019ac16cc1d4a4769d5f"
OBSERVATIONS_SHA = "7d181155abd9967f367eb1efbe4af8a4afb1377e0c1f2eb4430c86b05ae9d068"
PROTOCOL_SHA = "1343b2f008b30e71f0352fce2a667720d542d0e0f40e4078321dad0151582526"


def checked(name, expected, directory=EVALUATION):
    data = (directory / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Saved evaluation integrity check failed")
    return data.decode("utf-8")


def read_report(directory, hashes):
    metrics = json.loads(checked("metrics.json", hashes["metrics.json"], directory))
    protocol = json.loads(checked("protocol.json", hashes["protocol.json"], directory))
    current = json.loads((ROOT / "CURRENT_ARTIFACTS.json").read_text(encoding="utf-8"))
    rows = []
    for line in checked("observations.jsonl", hashes["observations.jsonl"], directory).splitlines():
        observation = json.loads(line)
        case = observation["case"]
        source = case["source_case"]
        paths = {}
        for path in protocol.get("available_paths", ["baseline", "normalized"]):
            execution = observation[path]
            packet = execution["packet"]
            result = packet["result"]
            routing = result["routing"] if result else {}
            assessment = execution["assessment"]
            normalization = packet.get("normalization") or {}
            paths[path] = {
                "domain": assessment["predicted_primary"], "scope": assessment["predicted_scope"],
                "domainConfidence": routing.get("primary_confidence"), "scopeConfidence": routing.get("scope_confidence"),
                "route": assessment["route"], "routeCorrect": assessment["route_correct"],
                "domainCorrect": assessment["primary_correct"], "scopeCorrect": assessment["scope_correct"],
                "latencyMs": packet["total_query_ms"], "retrieval": assessment["retrieval"],
                "issues": assessment["issues"], "llmCalls": normalization.get("llm_calls", 0),
                "wordingStatus": normalization.get("status", "disabled"),
                "evidence": execution.get("evidence"),
            }
        rows.append({"id": case["case_id"], "family": case["family_id"], "language": source["language"],
                     "variation": case["variation"], "question": case["question_text"],
                     "expectedDomain": source.get("expected_primary"), "expectedScope": source.get("expected_scope"),
                     "expectedRoute": source["expected_route"], "labeled": observation["baseline"]["assessment"]["labeled"],
                     "paths": paths})
    return {"schema_version": "1.0", "sample_data": False, "development_only": True,
            "independent_human_questions": 0, "run_id": protocol["version"], "recorded_at": protocol["prepared_at_utc"],
            "stack": {k: protocol[k] for k in ("classifier", "retrieval", "verifier", "normalizer_version", "model")},
            "stack_matches_current": all(protocol[k] == current[k] for k in ("classifier", "retrieval", "verifier")),
            "provenance": "AI-authored development cases used during repair; repeated wording families, not an independent holdout or legal-answer evaluation.",
            "available_paths": protocol.get("available_paths", ["baseline", "normalized"]),
            "evaluation_mode": protocol.get("evaluation_mode", "historical_conditional_comparison"),
            "evidence_checks": metrics.get("evidence_checks"),
            "development_intervals": metrics.get("development_intervals"),
            "metrics": metrics, "cases": rows}


def performance_report():
    historical = read_report(EVALUATION, {"metrics.json": METRICS_SHA, "protocol.json": PROTOCOL_SHA,
                                         "observations.jsonl": OBSERVATIONS_SHA})
    pin_file = ROOT / "backend/application/performance_current.json"
    if not pin_file.exists():
        return historical
    pin = json.loads(pin_file.read_text(encoding="utf-8"))
    directory = (ROOT / pin["path"]).resolve()
    if directory.parent != (ROOT / "outputs").resolve() or not directory.name.startswith("local-pipeline-evaluation-"):
        raise ValueError("Invalid operator evaluation binding")
    current = read_report(directory, pin["files"])
    current["provenance"] = "AI-authored development inputs and joined-concern regressions used during repair. Local classifier, retrieval and verifier only; no wording or explanation LLM. Not an independent holdout or legal-answer evaluation."
    current["historical_report"] = historical
    application_pin=ROOT/'backend/application/performance_application.json'
    if application_pin.exists():
        binding=json.loads(application_pin.read_text(encoding='utf-8'))
        directory=(ROOT/binding['path']).resolve()
        if directory.parent!=(ROOT/'outputs').resolve() or not directory.name.startswith('application-evaluation-'):raise ValueError('Invalid application evaluation binding')
        metrics=json.loads(checked('metrics.json',binding['metrics_sha256'],directory))
        metrics['run_id']=directory.name
        metrics['inference_files_match']=all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in binding['inference_source_sha256'].items())
        current['application_replay']=metrics
    return current
