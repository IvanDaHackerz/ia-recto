"""Opt-in, frozen development diagnostics; never classify a rejected proposal."""
from __future__ import annotations

import argparse
from pathlib import Path

from backend.evaluate_normalization import ROOT, compact, jsonl, read, rows, save, sha, utc, verify_freeze


def prepare(output):
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT / "outputs"):
        raise ValueError("Diagnostics belong under project outputs")
    parent = ROOT / "outputs/normalization-evaluation-v1.1.0"
    for name, expected in read(parent / "artifact_checksums.json").items():
        if sha(parent / name) != expected:
            raise ValueError("Earlier study artifact changed")
    cases = []
    for row in rows(parent / "observations.jsonl"):
        norm = row["normalized"]["packet"]["normalization"]
        if norm["validation_failure"] or row["case"]["case_id"] == "EVAL_100__noisy":
            cases.append({"case_id": row["case"]["case_id"], "question_text": row["case"]["question_text"],
                          "reference_question": row["case"]["reference_question"],
                          "prior_validation_failure": norm["validation_failure"], "origin": "replayed_AI_development_input"})
    cases.append({"case_id": "USER_PAYMENT_EXAMPLE", "question_text":
                  "inde ako nakoha yung bayad ako sa amu ako... anu pwede gawin.,?",
                  "reference_question": None, "origin": "user_supplied_reproduction_no_gold_label"})
    output.mkdir(parents=True, exist_ok=False)
    jsonl(output / "cases.jsonl", cases)
    save(output / "protocol.json", {"role": "development_diagnostic_replay", "prepared_at_utc": utc(),
         "input_count": len(cases), "maximum_llm_requests": len(cases),
         "note": "New provider responses cannot reconstruct discarded historical proposals. References never enter inference.",
         "independent_human_gold": 0, "website_quality_approved": False})
    current = read(ROOT / "CURRENT_ARTIFACTS.json")
    sources = sorted((ROOT / "backend").rglob("*.py")) + [ROOT / "backend/classifier/config.json"]
    save(output / "freeze.json", {"inputs_sha256": {n: sha(output / n) for n in ["cases.jsonl", "protocol.json"]},
         "runtime_source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in sources},
         "runtime_artifact_manifest_sha256": {current[k] + "/artifact_checksums.json": sha(ROOT / current[k] / "artifact_checksums.json")
                                                for k in ["classifier", "retrieval", "verifier"]}})
    snapshot = output / "source_snapshot"
    for source in sources:
        target = snapshot / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def run(output):
    from backend.normalization import from_environment
    from backend.terminal_test import inspect_question, load_runtime
    output = Path(output)
    verify_freeze(output)
    normalizer = from_environment()
    normalizer.capture_diagnostics = True
    if not normalizer.provider:
        raise ValueError("Configure the provider before diagnostic replay")
    verifier = load_runtime()
    # Exclusive creation prevents silently replacing historical observations.
    with (output / "observations.jsonl").open("x", encoding="utf-8") as stream:
        import json
        for case in rows(output / "cases.jsonl"):
            packet = inspect_question(verifier, case["question_text"], normalizer=normalizer)
            stream.write(json.dumps({"case": case, "packet": compact(packet)}, ensure_ascii=False) + "\n")
            stream.flush()
            norm = packet["normalization"]
            print(case["case_id"], norm["status"], norm["validation_failure"],
                  json.dumps(norm.get("development_diagnostic", {}), ensure_ascii=False), flush=True)
    verify_freeze(output)
    save(output / "completed.json", {"completed_at_utc": utc(), "observations_sha256": sha(output / "observations.jsonl")})
    save(output / "artifact_checksums.json", {str(p.relative_to(output)).replace("\\", "/"): sha(p)
         for p in output.rglob("*") if p.is_file() and p.name != "artifact_checksums.json"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    (prepare if args.prepare else run)(args.output)


if __name__ == "__main__":
    main()
