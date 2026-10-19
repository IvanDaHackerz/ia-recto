"""Evaluation correctness tests. No provider requests or model-quality claims."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.normalization_cases import ROOT, build_cases, load_source
from backend.normalization_metrics import assess, summarize_path, paired_interval
from backend.evaluate_normalization import prepare, verify_freeze, run, finalize, sha


def packet(question, normalized=False):
    return {"inspection_only": True, "labeled_evaluation": False, "original_question_text": question,
            "total_query_ms": 5.0, "normalization": {
                "status": "bypassed", "llm_calls": 0, "usage": {}, "validation_failure": None,
                "effective_question_text": question} if normalized else None,
            "result": {"question_text": question, "question_sha256": "0" * 64,
                       "routing": {"predicted_primary": "labor", "predicted_scope": "fully_supported",
                                   "primary_confidence": .9, "scope_confidence": .95, "routing_action": "retrieve_supported_evidence"},
                       "components": [], "excluded_components": [], "decision": "insufficient_evidence",
                       "mode": "current_guidance", "as_of": "2026-10-19", "answer_generation_allowed": False,
                       "deployment_allowed": False, "display_allowed": False}}


def observation(case, a=None, b=None):
    a, b = a or packet(case["question_text"]), b or packet(case["question_text"], True)
    return {"case": case, "baseline": {"packet": a, "assessment": assess(case, a)},
            "normalized": {"packet": b, "assessment": assess(case, b)}}


class EvaluationTests(unittest.TestCase):
    def test_100_families_200_forms_keep_source_expectations_and_reversible_noise(self):
        sources = {r["case_id"]: r for r in load_source()}
        cases = build_cases()
        self.assertEqual(cases, build_cases())
        self.assertEqual(len(cases), 200)
        self.assertEqual(len({r["family_id"] for r in cases}), 100)
        self.assertEqual(sum(c["source_case"]["expected_primary"] is None for c in cases), 10)
        for case in cases:
            self.assertEqual(case["source_case"], sources[case["base_case_id"]])
            self.assertFalse(case["is_independent_human_gold"])
            recovered = case["question_text"]
            for edit in reversed(case["perturbation_ledger"]):
                recovered = recovered[:edit["noisy_start"]] + edit["source_text"] + recovered[edit["noisy_end"]:]
            self.assertEqual(recovered, case["reference_question"])

    def test_abstentions_remain_in_accuracy_recall_and_f1_denominators(self):
        case = next(c for c in build_cases() if c["source_case"]["expected_primary"] == "labor")
        abstain = packet(case["question_text"], True)
        abstain["normalization"].update(status="clarify", effective_question_text=None)
        abstain["result"] = None
        result = summarize_path([observation(case, b=abstain)], "normalized")
        self.assertEqual(result["primary"]["accuracy"], {"numerator": 0, "denominator": 1, "value": 0})
        self.assertEqual(result["primary"]["per_class"]["labor"]["recall"], 0)
        self.assertEqual(result["primary"]["macro_f1"], 0)
        self.assertEqual(result["primary"]["abstentions"], 1)
        self.assertEqual(result["primary"]["confidence_calibration"]["prediction_count"], 0)

    def test_missing_context_clarification_is_scored_as_route_without_invented_labels(self):
        case = next(c for c in build_cases() if c["source_case"]["expected_primary"] is None)
        abstain = packet(case["question_text"], True)
        abstain["normalization"].update(status="clarify", effective_question_text=None)
        abstain["result"] = None
        result = assess(case, abstain)
        self.assertTrue(result["route_correct"])
        self.assertIsNone(result["primary_correct"])

    def test_retrieval_rank_resets_per_component_and_stops_at_five(self):
        case = next(c for c in build_cases() if c["source_case"]["relevant_ids"])
        p = packet(case["question_text"])
        relevant = case["source_case"]["relevant_ids"][0]
        p["result"]["components"] = [{"allowed_domain": "labor", "candidates": [{"provision_id": "other"}] * 5 + [{"provision_id": relevant}]}]
        self.assertFalse(assess(case, p)["retrieval"][0]["hit_at_5"])
        p["result"]["components"].append({"allowed_domain": "labor", "candidates": [{"provision_id": relevant}]})
        self.assertTrue(assess(case, p)["retrieval"][0]["hit_at_1"])

    def test_paired_bootstrap_keeps_clear_and_noisy_in_one_family(self):
        clear = next(c for c in build_cases() if c["source_case"]["expected_primary"] == "labor")
        noisy = {**copy.deepcopy(clear), "variation": "noisy"}
        wrong = packet(clear["question_text"], True)
        wrong["result"]["routing"]["predicted_primary"] = "consumer"
        rows = [observation(clear, b=wrong), observation(noisy, a=wrong)]
        interval = paired_interval(rows, "primary_correct")
        self.assertEqual(interval["difference"], 0)
        self.assertEqual(interval["family_cluster_bootstrap_95"], [0, 0])
        self.assertEqual(interval["families"], 1)

    def test_frozen_execution_question_only_and_final_report_cannot_be_overwritten(self):
        provider = SimpleNamespace(name="together", model="openai/gpt-oss-120b")
        fake_normalizer = SimpleNamespace(provider=provider)
        current = json.loads((ROOT / "CURRENT_ARTIFACTS.json").read_text())
        fake_verifier = SimpleNamespace(policy=current)
        received = []

        def inspect(verifier, question, normalizer=None):
            self.assertIsInstance(question, str)
            received.append(question)
            return packet(question, normalizer is not None)

        with tempfile.TemporaryDirectory(dir=ROOT / "outputs", prefix="normalization-eval-test-") as directory, \
             patch("backend.normalization.from_environment", return_value=fake_normalizer), \
             patch("backend.terminal_test.load_runtime", return_value=fake_verifier), \
             patch("backend.terminal_test.inspect_question", side_effect=inspect):
            output = prepare(Path(directory) / "study")
            verify_freeze(output)
            run(output)
            self.assertEqual(len(received), 400)
            self.assertEqual(len(set(received)), 200)
            with self.assertRaisesRegex(ValueError, "Preserve earlier predictions"):
                run(output)
            finalize(output)
            checksum = sha(output / "REPORT.md")
            with self.assertRaisesRegex(ValueError, "preserve it"):
                finalize(output)
            self.assertEqual(sha(output / "REPORT.md"), checksum)
            with (output / "cases.jsonl").open("a", encoding="utf-8") as stream:
                stream.write("\n")
            with self.assertRaisesRegex(ValueError, "input changed"):
                verify_freeze(output)


if __name__ == "__main__":
    unittest.main()
