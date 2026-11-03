"""Local evaluation provenance/denominator boundaries; no inference or network."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from backend.evaluate_local_pipeline import prepare, execute, sha, family_interval, ROOT


class LocalEvaluationTests(unittest.TestCase):
    def test_domain_coverage_is_a_set_not_an_ordered_label_list(self):
        from backend.normalization_metrics import assess
        case={'source_case':{'expected_primary':'mixed','expected_scope':'fully_supported','expected_route':'retrieve_supported_components','expected_domains':['labor','consumer'],'relevant_ids':[],'concerns':[],'retrieval_judgment':'unjudged'}}
        packet={'result':{'routing':{'routing_action':'retrieve_supported_components','predicted_primary':'mixed','predicted_scope':'fully_supported'},'components':[{'allowed_domain':d,'candidates':[]} for d in ['consumer','labor']]}}
        self.assertTrue(assess(case,packet)['domain_correct'])
    def test_prepare_freezes_existing_inputs_and_joined_regressions(self):
        with tempfile.TemporaryDirectory(prefix="local-eval-test-", dir=ROOT / "tmp") as folder:
            self.assertTrue(Path(folder).resolve().is_relative_to((ROOT / "tmp").resolve()))
            target = Path(folder) / "cases"
            prepare(target)
            freeze = json.loads((target / "freeze.json").read_text())
            cases = [json.loads(x) for x in (target / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(sha(target / "cases.jsonl"), freeze["cases_sha256"])
            self.assertEqual(len(cases), 436)
            self.assertEqual(freeze["independent_human_questions"], 0)
            english = next(c for c in cases if c["case_id"] == "joined_english")
            self.assertEqual(english["source_case"]["relevant_ids"], [])
            self.assertEqual(english["source_case"]["retrieval_judgment"], "unjudged")
            self.assertTrue(all(not c["is_independent_human_gold"] for c in cases))
            with self.assertRaises(ValueError): prepare(target)

    def test_changed_freeze_is_rejected_before_model_load(self):
        with tempfile.TemporaryDirectory(prefix="local-eval-test-", dir=ROOT / "tmp") as folder:
            self.assertTrue(Path(folder).resolve().is_relative_to((ROOT / "tmp").resolve()))
            target = Path(folder) / "cases"; prepare(target)
            (target / "cases.jsonl").write_text("{}\n")
            with patch("backend.evaluate_local_pipeline.load_runtime") as loader:
                with self.assertRaises(ValueError): execute(target, Path(folder) / "run")
                loader.assert_not_called()

    def test_interval_uses_families_and_excludes_unlabeled_rows(self):
        rows = [{"case": {"family_id": family}, "baseline": {"assessment": {
            "labeled": labeled, "primary_correct": correct}}}
            for family, labeled, correct in [("a", True, True), ("a", True, True), ("b", False, None)]]
        interval = family_interval(rows, "primary_correct")
        self.assertEqual(interval["families"], 1)
        self.assertEqual((interval["low"], interval["high"]), (1, 1))


if __name__ == "__main__": unittest.main()
