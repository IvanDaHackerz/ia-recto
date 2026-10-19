"""Terminal wrapper boundary checks; model performance is evaluated separately."""
import copy
import unittest
from unittest.mock import Mock

from backend.terminal_test import inspect_question, interactive, format_inspection, numbered_candidates, candidate_text, terminal_text
from backend.classifier.contracts import RequestError
from backend.clarification import payment_follow_up


def result():
    return {"question_text": "  Private employee ako. Hindi bayad ang overtime ko.  ",
            "answer_generation_allowed": False, "display_allowed": False, "deployment_allowed": False,
            "decision": "insufficient_evidence", "excluded_components": [], "referral_ids": [],
            "routing": {"predicted_primary": "labor", "predicted_scope": "fully_supported",
                        "primary_confidence": .91, "scope_confidence": .94,
                        "routing_action": "retrieve_supported_evidence", "reason": "test", "clarification_question": None},
            "components": []}


class TerminalTests(unittest.TestCase):
    def test_payment_follow_up_keeps_actual_predictions_and_permissions(self):
        response = result()
        question = "hindi ako nakuha yung bayad ako sa amo ako... ano pwede gawin.,?"
        response["question_text"] = question
        response["routing"].update(predicted_primary="out_of_scope", predicted_scope="unsupported",
                                   primary_confidence=.312, scope_confidence=.312,
                                   routing_action="clarify", reason="no_reliable_component_evidence",
                                   clarification_question="Generic clarification")
        response["decision"] = "clarify"
        original_response = copy.deepcopy(response)
        verifier = Mock(preflight=Mock(return_value=response))
        packet = inspect_question(verifier, question)
        self.assertEqual(packet["result"], original_response)
        self.assertEqual(response, original_response)
        self.assertEqual(packet["clarification_follow_up"]["reason"], "employer_payment_context_unconfirmed")
        text = format_inspection(packet)
        self.assertIn("Tentative model topic: Out of scope", text)
        self.assertIn("not a final scope decision", text)
        self.assertIn("sahod para sa trabaho, o ibang uri ng bayad?", text)
        self.assertIn("kasambahay", text)
        self.assertEqual(numbered_candidates(packet["result"]), [])

    def test_payment_follow_up_does_not_change_specific_routes_or_repeat_known_category(self):
        route = {"routing_action": "clarify", "reason": "no_identified_concern"}
        text = "Hindi ako nabayaran ng amo ko; kasambahay ako."
        follow_up = payment_follow_up(text, route)
        self.assertIn("ibang uri ng bayad", follow_up["question"])
        self.assertNotIn("private company", follow_up["question"])
        for question, action, reason in [
            (text, "retrieve_supported_evidence", "supported_candidate_requires_evidence"),
            (text, "refer_out_of_scope", "recognized_excluded_concern"),
            (text, "clarify", "mixed_components_not_resolved"),
            ("Hindi pa nagbayad ang buyer sa binili niya.", "clarify", "no_identified_concern"),
            ("Amo ng aso ang kapitbahay ko.", "clarify", "no_identified_concern"),
            ("The cashier charged more than the displayed price.", "clarify", "low_confidence"),
        ]:
            with self.subTest(question=question, action=action, reason=reason):
                self.assertIsNone(payment_follow_up(question, {"routing_action": action, "reason": reason}))

    def test_only_original_question_enters_normal_current_guidance(self):
        response = result()
        verifier = Mock()
        verifier.preflight.return_value = response
        packet = inspect_question(verifier, response["question_text"])
        verifier.preflight.assert_called_once_with(response["question_text"], mode="current_guidance")
        self.assertFalse(packet["labeled_evaluation"])
        self.assertGreaterEqual(packet["total_query_ms"], 0)

    def test_permission_leak_stops_inspection(self):
        for permission in ("answer_generation_allowed", "display_allowed", "deployment_allowed"):
            with self.subTest(permission=permission):
                response = result()
                response[permission] = True
                with self.assertRaisesRegex(ValueError, "permission"):
                    inspect_question(Mock(preflight=Mock(return_value=response)), "test question")

    def test_invalid_input_does_not_reach_inference(self):
        verifier = Mock()
        for question in ("bad\x1b[2J", "x" * 8001, "   "):
            with self.assertRaises(ValueError):
                inspect_question(verifier, question)
        verifier.preflight.assert_not_called()

    def test_report_does_not_invent_accuracy_or_legal_confidence(self):
        response = result()
        response["routing"].update(routing_action="clarify", clarification_question="What employer category?")
        text = format_inspection({"result": response, "total_query_ms": 12.5})
        self.assertIn("label confidence 91.0%", text)
        self.assertIn("unavailable for an unlabeled question", text)
        self.assertIn("not requested", text)
        self.assertIn("What employer category?", text)

    def test_full_provision_matches_global_number_across_components(self):
        hit = {"chunk_id": "chunk1", "citation_display": "Test citation", "document_title": "Test document",
               "provision_id": "p1", "score": 4.2, "legal_status": "recorded", "status_as_of": "2026-10-18",
               "official_source_url": "https://example.org/source", "retrieval_url": "", "display_text": "A short excerpt",
               "parent_text": "Complete stored text: exact wording."}
        component = {"candidates": [hit], "evidence_gates": [{"chunk_id": "chunk1", "reasons": ["scoped_currentness_review_missing"]}]}
        second = copy.deepcopy(component)
        second["candidates"][0]["parent_text"] = "Second complete provision."
        response = result()
        response["components"] = [component, second]
        rows = numbered_candidates(response)
        text = candidate_text(*rows[1], number=2, full=True)
        self.assertIn("Second complete provision.", text)
        self.assertIn("scoped_currentness_review_missing", text)
        self.assertIn("not confidence or a percentage", text)

    def test_loop_handles_commands_eof_and_correctable_input_error(self):
        answers = iter(["/json", "bad\x1b", "/help", "/quit"])
        output = []
        verifier = Mock()
        self.assertEqual(interactive(verifier, read=lambda _: next(answers), write=output.append), 0)
        self.assertTrue(any("Ask a question first" in line for line in output))
        self.assertTrue(any("Input error" in line for line in output))
        verifier.preflight.assert_not_called()
        self.assertEqual(interactive(verifier, read=Mock(side_effect=EOFError), write=output.append), 0)

    def test_source_controls_are_escaped_only_for_terminal_display(self):
        self.assertEqual(terminal_text("legal\x1b[2J\ntext"), "legal\\u001b[2J\ntext")


if __name__ == "__main__":
    unittest.main()
