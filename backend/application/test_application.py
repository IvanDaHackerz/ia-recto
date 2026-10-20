"""Integration boundaries, real local inference, and fail-closed answer gates. No live LLM calls."""
import copy
import io
import json
import threading
import unittest
from http.client import HTTPConnection
from unittest.mock import Mock, patch

from backend.classifier.contracts import RequestError
from backend.normalization import ConditionalNormalizer, Completion, NormalizationUnavailable
from backend.application.explanation import explain, TogetherExplanation, ExplanationUnavailable
from backend.application.performance import performance_report, checked, ROOT
from backend.application.service import ApplicationService
from backend.application.server import ApplicationServer


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = Mock(name="normalizer")
        cls.provider.name, cls.provider.model = "test", "mock"
        cls.service = ApplicationService(normalizer=ConditionalNormalizer(cls.provider), explanation_provider=Mock())

    def test_supported_question_uses_real_classifier_and_complete_sources(self):
        p = self.service.chat({"question_text": "Private employee ako. Ilang oras ang normal na workday bago maging excess hours?", "request_id": "local-1"})
        self.assertEqual(p["request_id"], "local-1")
        self.assertEqual(p["result"]["routing"]["predicted_primary"], "labor")
        self.assertEqual(p["normalization"]["llm_calls"], 0)
        self.assertEqual(p["explanation"]["reason"], "source_review_required")
        self.assertFalse(p["result"]["answer_generation_allowed"])
        hit = p["result"]["components"][0]["candidates"][0]
        self.assertEqual(hit["provision_id"], "LAB_CODE_2022__art_83")
        self.assertIn("parent_text", hit)
        self.assertEqual(hit["parent_text"][hit["normalized_char_start"]:hit["normalized_char_end"]], hit["display_text"])
        self.service.explanation_provider.complete.assert_not_called()

    def test_real_routing_paths_and_local_noisy_features(self):
        queries = [
            ("The defective phone I bought from a shop has a warranty but the store refuses repair.", "consumer", "retrieve_supported_evidence"),
            ("Private employee ako. Hindi binayaran ang overtime ko. Ayaw ibalik ng landlord ang rental deposit.", "mixed", "retrieve_supported_components"),
            ("Private employee ako. Hindi binayaran ang overtime ko at ayaw ibalik ng landlord ang rental deposit.", "mixed", "retrieve_supported_components"),
            ("Government employee ako. Hindi binayaran overtime ko.", "out_of_scope", "refer_out_of_scope"),
            ("Late ang salary ko.", "labor", "retrieve_supported_evidence"),
        ]
        for question, label, route in queries:
            with self.subTest(question=question):
                p = self.service.chat({"question_text": question})
                self.assertEqual(p["result"]["routing"]["routing_action"], route)
                if label:
                    self.assertEqual(p["result"]["routing"]["predicted_primary"], label)
                if question == "Late ang salary ko.":
                    self.assertEqual(p['guidance_context']['original_routing']['routing_action'], 'retrieve_supported_evidence')
                    self.assertFalse(p['guidance_context']['classification_is_conditional'])
                self.assertEqual(p["normalization"]["llm_calls"], 0)
                self.assertEqual(p["explanation"]["claims"], [])
                if route in {"clarify", "refer_out_of_scope"}:
                    self.assertEqual(p["result"]["components"], [])

    def test_uncertain_provider_output_is_withheld(self):
        self.provider.complete.return_value = Completion({"status": "unclear", "normalized_question": ""}, {})
        p = self.service.chat({"question_text": "inde ako nakoha yung bayad ako sa amu ako... anu pwede gawin.,?"})
        self.assertIsNone(p["result"])
        self.assertEqual(p["normalization"]["llm_calls"], 1)
        self.assertEqual(p["explanation"]["llm_calls"], 0)
        self.assertIn("ibang uri ng bayad", p["normalization"]["clarification_question"])
        self.assertNotIn("development_diagnostic", p["normalization"])

    def test_input_and_busy_boundaries(self):
        for payload in ({"question_text": " "}, {"question_text": "x", "review_store": {}}, {"question_text": "x" * 8001}):
            with self.assertRaises(RequestError):
                self.service.chat(payload)
        self.service._lock.acquire()
        try:
            with self.assertRaises(RequestError) as error:
                self.service.chat({"question_text": "A concern"})
            self.assertEqual(error.exception.status, 503)
        finally:
            self.service._lock.release()


class ExplanationTests(unittest.TestCase):
    def setUp(self):
        self.pre = {"question_text": "Fictional test", "routing": {"routing_action": "retrieve_supported_evidence"},
                    "all_supported_components_evidence_ready": True, "answer_generation_allowed": True, "software_fixture_mode": False}
        self.provider = Mock()
        self.verifier = Mock()
        self.verifier.verify.return_value = {"display_allowed": True, "legal_support_verified": True,
            "software_fixture_mode": False, "decision": "reviewed_answer_candidate", "components": [{"passed": True}],
            "preview": [{"text": "Only this verified claim", "citations": []}]}

    def test_all_preflight_gates_skip_provider(self):
        variants = [None, {**self.pre, "all_supported_components_evidence_ready": False},
                    {**self.pre, "answer_generation_allowed": False}, {**self.pre, "software_fixture_mode": True}]
        variants += [{**self.pre, "routing": {"routing_action": route}} for route in ("clarify", "refer_out_of_scope")]
        for pre in variants:
            with self.subTest(pre=pre):
                self.assertEqual(explain(self.verifier, pre, self.provider)["llm_calls"], 0)
                self.assertEqual(explain(self.verifier, pre, self.provider)["claims"], [])
        self.provider.complete.assert_not_called()

    def test_only_postflight_claims_returned_when_every_permission_passes(self):
        self.provider.complete.return_value = {"unchecked": "must never be returned"}
        result = explain(self.verifier, self.pre, self.provider)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["claims"], self.verifier.verify.return_value["preview"])
        self.verifier.verify.assert_called_once_with("Fictional test", self.provider.complete.return_value, mode="current_guidance")

    def test_failed_postflight_never_leaks_raw_draft(self):
        original = copy.deepcopy(self.verifier.verify.return_value)
        for field, value in [("display_allowed", False), ("legal_support_verified", False), ("software_fixture_mode", True),
                             ("decision", "draft_rejected"), ("components", [{"passed": False}])]:
            with self.subTest(field=field):
                self.verifier.verify.return_value = copy.deepcopy(original)
                self.verifier.verify.return_value[field] = value
                result = explain(self.verifier, self.pre, self.provider)
                self.assertEqual(result["claims"], [])
                self.assertEqual(result["reason"], "postflight_withheld")

    def test_provider_failure_is_withheld(self):
        self.provider.complete.side_effect = ExplanationUnavailable("secret provider error")
        result = explain(self.verifier, self.pre, self.provider)
        self.assertEqual(result["llm_calls"], 1)
        self.assertEqual(result["reason"], "provider_unavailable")
        self.assertNotIn("secret", json.dumps(result))

    def test_transport_sends_only_eligible_sources_and_has_no_retries(self):
        # Real source schema becomes available when the runtime is loaded above.
        from backend.terminal_test import load_runtime
        load_runtime()
        pre = {"components": [{"component_id": "c1", "query": "test", "evidence_gates": [
            {"chunk_id": "yes", "passed": True}, {"chunk_id": "no", "passed": False}], "candidates": [
                {"chunk_id": c, "provision_id": "p", "document_id": "d", "parent_text": "text", "conditions": []} for c in ("yes", "no")]}]}
        payload = {"choices": [{"finish_reason": "stop", "message": {"content": '{"draft":"test"}'}}]}
        opener = Mock()
        opener.open.return_value.__enter__ = Mock(return_value=io.BytesIO(json.dumps(payload).encode()))
        opener.open.return_value.__exit__ = Mock(return_value=False)
        with patch("backend.application.explanation.urllib.request.build_opener", return_value=opener):
            self.assertEqual(TogetherExplanation("openai/gpt-oss-120b", "test-key").complete("test", pre), {"draft": "test"})
        opener.open.assert_called_once()
        request = opener.open.call_args.args[0]
        sent = json.loads(request.data)
        evidence = json.loads(sent["messages"][1]["content"])
        self.assertEqual([s["chunk_id"] for s in evidence["components"][0]["sources"]], ["yes"])
        self.assertEqual(request.full_url, "https://api.together.ai/v1/chat/completions")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 20)

    def test_transport_refuses_redirects_and_incomplete_provider_output(self):
        from backend.terminal_test import load_runtime
        load_runtime()
        adapter = TogetherExplanation("openai/gpt-oss-120b", "test-key")
        opener = Mock()
        opener.open.side_effect = NormalizationUnavailable("Redirect rejected")
        with patch("backend.application.explanation.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(ExplanationUnavailable):
                adapter.complete("test", {"components": []})
        opener.open.assert_called_once()

    def test_transport_caps_input_before_any_provider_request(self):
        from backend.terminal_test import load_runtime
        load_runtime()
        with patch("backend.application.explanation.urllib.request.build_opener") as opener:
            with self.assertRaises(ExplanationUnavailable):
                TogetherExplanation("model", "test-key").complete("x" * 150000, {"components": []})
            opener.assert_not_called()


class PerformanceTests(unittest.TestCase):
    def test_complete_application_replay_never_claims_independent_answer_accuracy(self):
        report=performance_report()['application_replay']
        self.assertEqual(report['input_forms'],436)
        self.assertEqual(sum(report['explanation_status'].values()),report['successful_packets'])
        self.assertIsNone(report['independent_legal_accuracy'])
        self.assertEqual(report['generated_without_automated_support'],0)
        self.assertEqual(report['independent_human_questions'],0)
        binding=json.loads((ROOT/'backend/application/performance_application.json').read_text(encoding='utf-8'))
        expected=all(__import__('hashlib').sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in binding['inference_source_sha256'].items())
        self.assertEqual(report['inference_files_match'],expected)
    def test_actual_frozen_denominators_and_deferrals(self):
        data = performance_report()
        self.assertFalse(data["sample_data"])
        self.assertTrue(data["stack_matches_current"])
        self.assertEqual(data["available_paths"], ["baseline"])
        self.assertEqual(len(data["cases"]), 436)
        self.assertEqual(data["independent_human_questions"], 0)
        labeled = [r for r in data["cases"] if r["labeled"]]
        self.assertEqual(len(labeled), 425)
        self.assertEqual(sum(r["paths"]["baseline"]["llmCalls"] for r in data["cases"]), 0)
        self.assertTrue(all("normalized" not in r["paths"] for r in data["cases"]))
        self.assertEqual(sum(r["paths"]["baseline"]["domainCorrect"] for r in labeled), data["metrics"]["strata"]["all"]["baseline"]["primary"]["accuracy"]["numerator"])

    def test_historical_llm_comparison_remains_separate_and_unchanged(self):
        data = performance_report()["historical_report"]
        self.assertFalse(data["stack_matches_current"])
        self.assertEqual(len(data["cases"]), 424)
        self.assertEqual(sum(r["paths"]["normalized"]["llmCalls"] for r in data["cases"]), 6)
        self.assertEqual(sum(r["paths"]["normalized"]["domain"] == "__abstain__" for r in data["cases"] if r["labeled"]), 2)

    def test_evidence_metrics_do_not_claim_legal_approval(self):
        data = performance_report()
        checks = data["evidence_checks"]
        self.assertEqual(checks["live_permissions_closed"], 436)
        self.assertEqual(checks["candidate_integrity_failures"], 0)
        self.assertEqual(checks["cross_domain_candidate_leaks"], 0)
        self.assertEqual(checks["recorded_excerpt_claims_passed"], checks["recorded_excerpt_claims"])
        self.assertEqual(checks["recorded_excerpt_legal_support_claimed"], 0)

    def test_checksum_failure_is_not_silently_replaced_with_fixtures(self):
        with self.assertRaises(ValueError):
            checked("metrics.json", "0" * 64)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = Mock()
        cls.service.health.return_value = {"schema_version": "1.0", "status": "ready"}
        cls.service.performance.return_value = {"schema_version": "1.0", "sample_data": False}
        def chat(payload, **kwargs):
            from backend.classifier.contracts import validate_request
            validate_request(payload)
            return {"schema_version": "1.0", "request_id": "test"}
        cls.service.chat.side_effect = chat
        cls.server = ApplicationServer(("127.0.0.1", 0), cls.service, allowed_origins=["http://127.0.0.1:5173"])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        client = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        client.request(method, path, body=body, headers=headers or {})
        response = client.getresponse()
        status, headers, payload = response.status, dict(response.getheaders()), json.loads(response.read())
        client.close()
        return status, headers, payload

    def test_get_routes_and_no_store(self):
        for path in ("/api/health", "/api/performance"):
            status, headers, payload = self.request("GET", path)
            self.assertEqual(status, 200); self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(payload["schema_version"], "1.0")

    def test_real_json_post_and_exact_origin(self):
        status, headers, _ = self.request("POST", "/api/chat", '{"question_text":"test"}',
            {"Content-Type": "application/json", "Origin": "http://127.0.0.1:5173"})
        self.assertEqual(status, 200)
        self.assertEqual(headers["Access-Control-Allow-Origin"], "http://127.0.0.1:5173")

    def test_invalid_json_content_and_unknown_client_review_fields(self):
        for body in ('{"question_text":"a","question_text":"b"}', '{"question_text":NaN}', '{"question_text":"a","display_allowed":true}'):
            self.assertEqual(self.request("POST", "/api/chat", body, {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.request("POST", "/api/chat", "x", {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/chat", "x", {"Content-Type": "application/json", "Content-Length": "65537"})[0], 413)

    def test_host_origin_paths_and_methods(self):
        checks = [("GET", "/api/health", {"Host": "evil.example"}, 403),
                  ("GET", "/api/health", {"Origin": "https://evil.example"}, 403),
                  ("GET", "/api/health?x=1", {}, 400), ("GET", "/unknown", {}, 404),
                  ("GET", "/api/chat", {}, 405), ("POST", "/api/performance", {}, 405)]
        for method, path, headers, expected in checks:
            with self.subTest(path=path, headers=headers):
                self.assertEqual(self.request(method, path, headers=headers)[0], expected)

    def test_errors_do_not_echo_payloads_or_credentials(self):
        original = self.service.chat.side_effect
        self.service.chat.side_effect = RuntimeError("secret-key and personal-question")
        try:
            status, _, payload = self.request("POST", "/api/chat", '{"question_text":"test"}', {"Content-Type": "application/json"})
            self.assertEqual(status, 503)
            self.assertNotIn("secret", json.dumps(payload))
        finally:
            self.service.chat.side_effect = original


if __name__ == "__main__":
    unittest.main()
