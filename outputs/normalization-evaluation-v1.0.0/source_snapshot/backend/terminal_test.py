"""Classifier/retrieval inspector with optional conditional LLM wording repair."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from backend.classifier.contracts import validate_request
from backend.clarification import payment_follow_up

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "labor": "Labor", "consumer": "Consumer", "mixed": "Mixed",
    "out_of_scope": "Out of scope", "fully_supported": "Fully supported",
    "partially_supported": "Partially supported", "unsupported": "Unsupported",
}
ROUTES = {
    "retrieve_supported_evidence": "Retrieve supporting provisions",
    "retrieve_supported_components": "Retrieve only the supported concerns",
    "clarify": "Ask for clarification", "refer_out_of_scope": "Refer out of scope",
}


def load_runtime():
    """Reuse the pinned verifier's classifier/retriever and normal review gates."""
    current = json.loads((ROOT / "CURRENT_ARTIFACTS.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(ROOT / "dataset/pipelines/item13"))
    from evaluation_common import verify_packet
    verify_packet(ROOT / current["verifier"], runtime=True)
    sys.path.insert(0, str(ROOT / "dataset/pipelines/item12"))
    from verification import EvidenceVerifier
    verifier = EvidenceVerifier()
    for field in ("classifier", "retrieval"):
        if verifier.policy[field] != current[field]:
            raise ValueError(f"Current {field} differs from verifier binding")
    if verifier.policy["version"] != Path(current["verifier"]).name:
        raise ValueError("Current verifier version differs from policy")
    return verifier


def inspect_question(verifier, question, normalizer=None):
    original, _ = validate_request({"question_text": question})
    if not original.strip():
        raise ValueError("Type a non-empty question")
    start = time.perf_counter()
    normalization = normalizer.prepare(original) if normalizer is not None else None
    effective = normalization["effective_question_text"] if normalization else original
    if effective is None:
        return {"inspection_only": True, "labeled_evaluation": False,
                "original_question_text": original, "normalization": normalization,
                "total_query_ms": (time.perf_counter() - start) * 1000, "result": None}
    result = verifier.preflight(effective, mode="current_guidance")
    if any(result[key] for key in ("answer_generation_allowed", "display_allowed", "deployment_allowed")):
        raise ValueError("Unexpected answer/display permission; inspection stopped")
    if normalizer is not None and normalization["status"] == "bypassed":
        fallback = normalizer.prepare(original, routing=result["routing"])
        if fallback["gate"]["needed"]:
            fallback["baseline_routing"] = dict(result["routing"])
            normalization = fallback
            effective = normalization["effective_question_text"]
            if effective is None:
                result = None
            elif effective != original:
                result = verifier.preflight(effective, mode="current_guidance")
                if any(result[key] for key in ("answer_generation_allowed", "display_allowed", "deployment_allowed")):
                    raise ValueError("Unexpected answer/display permission; inspection stopped")
    return {"inspection_only": True, "labeled_evaluation": False,
            "original_question_text": original, "normalization": normalization,
            "clarification_follow_up": payment_follow_up(effective, result["routing"]) if result else None,
            "total_query_ms": (time.perf_counter() - start) * 1000, "result": result}


def numbered_candidates(result):
    return [(component, hit) for component in result["components"] for hit in component["candidates"]] if result else []


def terminal_text(value):
    # Keep source data intact; escape control characters only in terminal output.
    return "".join(c if c in "\n\t" or (ord(c) >= 32 and not 127 <= ord(c) <= 159)
                   else f"\\u{ord(c):04x}" for c in str(value))


def candidate_text(component, hit, number, full=False):
    gate = next((g for g in component["evidence_gates"] if g["chunk_id"] == hit["chunk_id"]), None)
    text = hit["parent_text"] if full else hit["display_text"]
    shown = text if full or len(text) <= 240 else text[:240] + "\n[Preview shortened; use /full " + str(number) + "]"
    reasons = ", ".join("Current-source review missing (scoped_currentness_review_missing)" if r == "scoped_currentness_review_missing" else r
                        for r in gate["reasons"]) if gate and gate["reasons"] else "No recorded preflight blockers"
    return "\n".join([
        f"  [{number}] {hit['citation_display']} - {hit['document_title']}",
        f"      Provision: {hit['provision_id']}",
        f"      Ranking score: {hit['score']:.4f} (not confidence or a percentage)",
        f"      Recorded status: {hit['legal_status']} | checked {hit['status_as_of']}",
        f"      Source: {hit['official_source_url'] or hit['retrieval_url']}",
        f"      Current-guidance check: {reasons}",
        "      Complete stored provision:" if full else "      Stored excerpt:", shown,
    ])


def format_inspection(packet):
    result = packet["result"]
    normalization = packet.get("normalization")
    prefix = []
    if normalization:
        prefix = ["\nORIGINAL QUESTION", packet["original_question_text"], "\nWORDING CHECK",
                  f"  Normalization: {normalization['status']} | LLM requests: {normalization['llm_calls']}",
                  f"  Reason: {normalization['reason']}"]
        if normalization["gate"]["needed"]:
            prefix += ["  Wording trigger: " + normalization["gate"]["reason"]]
        if normalization.get("baseline_routing"):
            prefix += ["  The original was checked locally first; unfamiliar unresolved wording triggered interpretation."]
        if normalization.get("validation_failure"):
            prefix += ["  Rewrite check: " + normalization["validation_failure"]]
        if normalization["normalized_question_text"]:
            prefix += ["  Interpreted wording: " + normalization["normalized_question_text"],
                       "  Confidence below is for this interpreted wording; this pipeline has not been performance-evaluated."]
        if normalization["llm_calls"]:
            prefix += [f"  Provider/model: {normalization['provider']} / {normalization['model']}",
                       f"  Normalizer time: {normalization['elapsed_ms']:.1f} ms"]
            if normalization["usage"]:
                prefix += ["  Token usage: " + json.dumps(normalization["usage"], sort_keys=True)]
        if result is None:
            prefix += ["  " + normalization["clarification_question"],
                       "  Classifier and retrieval were not run on an uncertain interpretation.",
                       "  No legal answer generated."]
            if normalization["status"] == "unconfigured":
                prefix += ["  Configure the optional provider/model/key, or retype in fuller words."]
            return terminal_text("\n".join(prefix))
    route = result["routing"]
    tentative = route["routing_action"] == "clarify"
    label_prefix = "Tentative model topic" if tentative else "Topic"
    scope_prefix = "Tentative model coverage" if tentative else "Coverage"
    lines = [
        "\nANALYZED QUESTION" if normalization else "\nQUESTION", result["question_text"], "\nCLASSIFICATION",
        f"  {label_prefix}: {LABELS[route['predicted_primary']]} | label confidence {route['primary_confidence']:.1%}",
        f"  {scope_prefix}: {LABELS[route['predicted_scope']]} | label confidence {route['scope_confidence']:.1%}",
        f"  Next action: {ROUTES[route['routing_action']]}",
        f"  Reason: {route['reason']}",
    ]
    if tentative:
        lines += ["  Topic and coverage are unresolved; these tentative labels are not a final scope decision."]
    if route["clarification_question"]:
        follow_up = packet.get("clarification_follow_up")
        lines += [f"  Clarification: {follow_up['question'] if follow_up else route['clarification_question']}"]
        if follow_up:
            lines += ["  Follow-up selected from payment/employer wording; model predictions are unchanged."]
    for excluded in result["excluded_components"]:
        lines += [f"  Excluded concern (not searched): {excluded['text']}"]
    if result["referral_ids"]:
        lines += ["  Referral candidate IDs: " + ", ".join(result["referral_ids"]),
                  "  Contact details need their separate recorded checks."]
    lines += ["\nRETRIEVED PROVISIONS (candidates for inspection)"]
    number = 0
    for component in result["components"]:
        lines += [f"  {component['allowed_domain']}: {component['query']}",
                  f"  Retrieval: {component['retrieval_status']}"]
        if not component["candidates"]:
            lines += [f"  No provisions returned: {component['retrieval_reason']}"]
        for hit in component["candidates"]:
            number += 1
            lines += [candidate_text(component, hit, number)]
    if not result["components"]:
        lines += ["  Retrieval was not requested for this clarification/referral route."]
    lines += ["\nOBSERVATIONS", f"  Retrieved provisions: {number}",
              f"  Total query time: {packet['total_query_ms']:.1f} ms (classification + retrieval + preflight checks)",
              f"  Current-guidance decision: {result['decision']}",
              "  Accuracy / F1: unavailable for an unlabeled question; use the labeled evaluation.",
              "  Confidence describes labels; a retrieval hit does not prove legal correctness.",
              "  No LLM answer generated. Current-guidance and display gates remain unchanged."]
    if normalization and normalization["llm_calls"]:
        lines += ["  Total query time also includes the conditional LLM request."]
    return terminal_text("\n".join(prefix + lines))


HELP = """Type a question and press Enter.
/full N  Read the complete stored provision for result N from the last question.
/json    Inspect the last result as JSON (including source metadata and checks).
/help    Show these commands.
/quit    Exit. Ctrl+C or Ctrl+Z then Enter also exits.
Questions are not saved by this tool and never train the local model.
Only flagged messages can call the configured LLM; that request includes the full question for context.
Accuracy and F1 require expected labels in a separate evaluation run.
"""


def interactive(verifier, read=input, write=print, normalizer=None):
    write(HELP)
    last = None
    while True:
        try:
            question = read("\nQuestion> ")
        except (EOFError, KeyboardInterrupt):
            write("\nTester closed.")
            return 0
        command = question.strip()
        if not command:
            continue
        if command == "/quit":
            return 0
        if command == "/help":
            write(HELP)
            continue
        if command == "/json" or command.startswith("/full"):
            if last is None:
                write("Ask a question first.")
                continue
            if command == "/json":
                write(json.dumps(last, ensure_ascii=False, indent=2, allow_nan=False))
                continue
            pieces = command.split()
            hits = numbered_candidates(last["result"])
            if len(pieces) != 2 or pieces[0] != "/full" or not pieces[1].isdigit() or not 1 <= int(pieces[1]) <= len(hits):
                write("Use /full N with a result number from the last question.")
                continue
            number = int(pieces[1])
            component, hit = hits[number - 1]
            write(terminal_text(candidate_text(component, hit, number, full=True)))
            continue
        if command.startswith("/"):
            write("Unknown command. Use /help.")
            continue
        try:
            last = inspect_question(verifier, question, normalizer=normalizer)
            write(format_inspection(last))
        except ValueError as error:
            # Invalid input can be corrected; runtime/integrity failures stop this session.
            from backend.classifier.contracts import RequestError
            if isinstance(error, RequestError):
                write(terminal_text("Input error: " + str(error)))
                continue
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Inspect one question and exit instead of prompting")
    parser.add_argument("--json", action="store_true", help="Print one-question output as JSON")
    parser.add_argument("--normalization", choices=["auto", "off"], default="auto",
                        help="Auto: local gate plus optional configured LLM; off: original baseline")
    args = parser.parse_args()
    if args.json and args.query is None:
        parser.error("--json requires --query; use /json inside an interactive session")
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        print("Loading the pinned local classifier, retrieval index and verifier...", file=sys.stderr, flush=True)
        verifier = load_runtime()
        from backend.normalization import from_environment
        normalizer = from_environment() if args.normalization == "auto" else None
        if args.query is not None:
            packet = inspect_question(verifier, args.query, normalizer=normalizer)
            print(json.dumps(packet, ensure_ascii=False, indent=2, allow_nan=False) if args.json else format_inspection(packet))
            return 0
        print(f"Ready: {Path(verifier.policy['classifier']).name} | {Path(verifier.policy['retrieval']).name} | {verifier.policy['version']}")
        if normalizer is not None:
            provider = normalizer.provider
            print(f"Conditional wording layer: {provider.name + ' / ' + provider.model if provider else 'not configured'}; clear messages bypass.")
        return interactive(verifier, normalizer=normalizer)
    except KeyboardInterrupt:
        print("\nTester closed.", file=sys.stderr)
        return 0
    except (ValueError, OSError, KeyError, ImportError) as error:
        print(terminal_text("Tester stopped: " + str(error)), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
