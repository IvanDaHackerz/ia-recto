"""Conditional normalization boundary tests. Synthetic provider replies, no API calls."""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
import urllib.error
from unittest.mock import Mock, patch

from backend.normalization import ConditionalNormalizer, Completion, NormalizationUnavailable, assess_text, from_environment
from backend.normalization_provider import OpenAIProvider, TogetherProvider
from backend import normalizer_credentials
from backend.terminal_test import inspect_question, format_inspection
from backend.normalization_validation import validate_rewrite

NOISY = "d po bnyrn overtime q sa prvt cmpny; municipal employee din si Ana, PHP 500 noong 2026-10-19."
REPORTED = "inde ako nakoha yung bayad ako sa amu ako... anu pwede gawin.,?"


def provider(payload=None):
    p = Mock(name="provider")
    p.name, p.model = "test-provider", "test-model"
    p.complete.return_value = Completion(payload or {
        "status": "normalized", "normalized_question":
        "hindi po binayaran overtime ko sa private company; municipal employee din si Ana, PHP 500 noong 2026-10-19."
    }, {"input_tokens": 20})
    return p


def rewrite(text):
    return {"status": "normalized", "normalized_question": text}


class GateTests(unittest.TestCase):
    def test_failed_payment_rewrite_asks_context_without_classifying_the_proposal(self):
        from backend.test_terminal_test import result as make_result
        baseline = make_result()
        baseline["routing"].update(routing_action="clarify", reason="no_identified_concern")
        p = provider(rewrite("Hindi ako nakakuha ng bayad ko sa ...? Ano pwede gawin?"))
        verifier = Mock(preflight=Mock(return_value=baseline))
        packet = inspect_question(verifier, REPORTED, normalizer=ConditionalNormalizer(p))
        self.assertIsNone(packet["result"])
        self.assertEqual(packet["clarification_follow_up"]["reason"], "payment_wording_unresolved")
        self.assertIn("ibang uri ng bayad", packet["normalization"]["clarification_question"])
        self.assertFalse(packet["clarification_follow_up"]["changes_classifier_prediction"])
        verifier.preflight.assert_called_once_with(REPORTED, mode="current_guidance")

    def test_scope_anchors_cannot_turn_into_plausible_wrong_words(self):
        for original, interpreted in [
            ("Sira ang bnling item sa shop.", "Sira ang billing item sa shop."),
            ("Mas mataas ang sngl sa grocery kaysa price label.", "Mas mataas ang single sa grocery kaysa price label."),
            ("May sharp edgiang householdproduct.", "May sharp edging household product."),
        ]:
            with self.subTest(original=original), self.assertRaisesRegex(ValueError, "scope_anchor_changed"):
                validate_rewrite(original, rewrite(interpreted))

    def test_word_boundaries_and_conjunction_do_not_invent_facts_or_negation(self):
        cases = [
            ("Myprvte employer owes me wagis.", "My private employer owes me wages."),
            ("An onlne store sent it andit won't checkkk theother.", "An online store sent it and it won't check the other."),
            ("Kaya ba gumawa ng technicalOSH assessment?", "Kaya ba gumawa ng technical OSH assessment?"),
            ("The developerchanged the lyut. What doI habe?", "The developer changed the layout. What do I have?"),
            ("May shrp edgiang table at householdproduct.", "May sharp edge ang table at household product."),
            ("Myprvte employer owes me wagis. Do I nd to pay?", "My private employer owes me wages. Do I need to pay?"),
            ("Kung mnnalo ang appeal?", "Kung mananalo ang appeal?"),
        ]
        for original, interpreted in cases:
            with self.subTest(original=original):
                self.assertEqual(validate_rewrite(original, rewrite(interpreted))[0], interpreted)
        for original, interpreted in [
            ("Kaya ba gumawa ng technical assessment?", "Kaya ba gumawa ng technical OSH assessment?"),
            ("My employer owes me wagis.", "My private employer owes me wages."),
            ("Salary delayeddd.", "Salary I delayed."),
            ("An onlne store sent it andit will checkkk.", "An online store sent it and it won't check."),
            ("Gusto kong malaman kung mananalo ang appeal.", "Gusto kong malaman kung manalo ang appeal."),
            ("Gusto kong malaman kung manalo ang appeal.", "Gusto kong malaman kung mananalo ang appeal."),
            ("Kung mnnalo ang appeal?", "Kung manalo ang appeal?"),
            ("nd bayad ang sahod ko.", "Bayad ang sahod ko."),
        ]:
            with self.subTest(original=original), self.assertRaises(ValueError):
                validate_rewrite(original, rewrite(interpreted))

    def test_rejected_diagnostics_require_explicit_opt_in_and_never_enter_inference(self):
        from backend.test_terminal_test import result as make_result
        proposed = "Hindi ko nakuha ang sahod ko sa private company. Ano ang gagawin ko?"
        ordinary = ConditionalNormalizer(provider(rewrite(proposed))).prepare(REPORTED)
        self.assertNotIn("development_diagnostic", ordinary)
        baseline = make_result()
        baseline["routing"].update(routing_action="clarify", reason="no_identified_concern")
        verifier = Mock(preflight=Mock(return_value=baseline))
        packet = inspect_question(verifier, REPORTED,
                                  normalizer=ConditionalNormalizer(provider(rewrite(proposed)), capture_diagnostics=True))
        diagnostic = packet["normalization"]["development_diagnostic"]
        self.assertEqual(diagnostic["proposed_question_text"], proposed)
        self.assertFalse(diagnostic["accepted_for_inference"])
        self.assertIsNone(packet["result"])
        verifier.preflight.assert_called_once_with(REPORTED, mode="current_guidance")

    def test_raw_decisive_result_bypasses_even_suspicious_spelling(self):
        from backend.test_terminal_test import result as make_result
        p = provider()
        verifier = Mock(preflight=Mock(return_value=make_result()))
        packet = inspect_question(verifier, "Privateee employee ako. Hindi bayad ang overtime ko.", normalizer=ConditionalNormalizer(p))
        self.assertEqual(packet["normalization"]["status"], "bypassed")
        self.assertEqual(packet["normalization"]["reason"], "raw_question_understood")
        p.complete.assert_not_called()
        self.assertEqual(verifier.preflight.call_count, 1)

    def test_preservation_repairs_block_observed_semantic_regressions(self):
        cases = [
            ("Prvte emplye ako. May ntce ng rst-day schedule?", "Private employee ako. May notice ng first-day schedule?"),
            ("Ayawww nila i-refund yung binnnayad ko.", "Ayaw nila i-refund yung binabayad ko."),
            ("Sa auuuthorized service center binaliiik ko.", "Sa unauthorized service center binalik ko."),
            ("Ano gagawin ko sa bawwwat isa?", "Ano gagawin ko sa bawas isa?"),
            ("Vouchers imbes na pra bilang shd. Anng rle?", "Vouchers imbes na para bilang sahod. Anong role?"),
        ]
        for original, interpreted in cases:
            with self.subTest(original=original), self.assertRaises(ValueError):
                validate_rewrite(original, rewrite(interpreted))
        original = "Privateee employee ako, unpaid ang overtime."
        self.assertEqual(validate_rewrite(original, rewrite("Private employee ako, unpaid ang overtime."))[0],
                         "Private employee ako, unpaid ang overtime.")

    def test_unlisted_phonetic_forms_and_merged_words_are_accepted(self):
        cases = [
            ("private employee aqoh, hindeh pa nabayarran yung sahod qoh... papanu poh?",
             "Private employee ako, hindi pa nabayaran yung sahod ko... paano po?"),
            ("sa storeh aqoh bumilii, ayw nlah irefund yung sirang itemm... anuh gagawenn?",
             "Sa store ko bumili, ayaw nila irefund yung sirang item... ano gagawin?"),
            ("private company ako work pero hindinabayaran sahodko, papanu?",
             "private company ako work pero hindi nabayaran sahod ko, paano?"),
            ("private employee ako, hind1 pa nabay4ran ang sw3ldo ko",
             "Private employee ako, hindi pa nabayaran ang sweldo ko"),
        ]
        for original, normalized in cases:
            with self.subTest(original=original):
                self.assertEqual(validate_rewrite(original, rewrite(normalized))[0], normalized)

    def test_actor_change_new_agency_and_dropped_second_concern_are_rejected(self):
        original = "hndi po bnyrn sahod ko sa private company; bank loan issue din sa BDO, PHP 500."
        variants = [
            "Hindi po binayaran sahod niya sa private company; bank loan issue din sa BDO, PHP 500.",
            "Hindi po binayaran sahod ko sa private company; bank loan issue din sa BDO, PHP 500. DOLE.",
            "Hindi po binayaran sahod ko sa private company, PHP 500.",
        ]
        for text in variants:
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_rewrite(original, rewrite(text))

    def test_terminal_fallback_runs_once_and_reclassifies_only_validated_text(self):
        from backend.test_terminal_test import result as make_result
        original = "nawitheldan sahod sa kompanyah papanu"
        normalized = "nawitheldan sahod sa kompanya, paano?"
        baseline = make_result()
        baseline["routing"].update(routing_action="clarify", reason="no_reliable_component_evidence")
        final = make_result()
        final["question_text"] = normalized
        p = provider(rewrite(normalized))
        verifier = Mock(preflight=Mock(side_effect=[baseline, final]))
        packet = inspect_question(verifier, original, normalizer=ConditionalNormalizer(p))
        self.assertEqual(packet["normalization"]["gate"]["reason"], "unresolved_unfamiliar_wording")
        self.assertEqual(packet["result"], final)
        self.assertEqual(verifier.preflight.call_count, 2)
        self.assertEqual(verifier.preflight.call_args.args[0], normalized)
        p.complete.assert_called_once()

    def test_failed_fallback_does_not_classify_an_uncertain_rewrite(self):
        from backend.test_terminal_test import result as make_result
        baseline = make_result()
        baseline["routing"].update(routing_action="clarify", reason="no_identified_concern")
        p = provider({"status": "unclear", "normalized_question": ""})
        verifier = Mock(preflight=Mock(return_value=baseline))
        packet = inspect_question(verifier, "nawitheldan sahod sa kompanyah papanu", normalizer=ConditionalNormalizer(p))
        self.assertIsNone(packet["result"])
        self.assertEqual(verifier.preflight.call_count, 1)
        p.complete.assert_called_once()

    def test_long_flagged_question_does_not_pay_for_truncated_rewrite(self):
        p = provider()
        response = ConditionalNormalizer(p).prepare("aqoh " * 401)
        self.assertEqual(response["status"], "clarify")
        self.assertEqual(response["llm_calls"], 0)
        p.complete.assert_not_called()

    def test_whole_sentence_repairs_grammar_and_preserves_original(self):
        p = provider(rewrite("Hindi ko nakuha yung bayad ko sa amo ko. Ano ang puwede kong gawin?"))
        normalized = ConditionalNormalizer(p).prepare(REPORTED)
        self.assertEqual(normalized["status"], "applied")
        self.assertEqual(normalized["original_question_text"], REPORTED)
        self.assertIn("bayad ko sa amo ko", normalized["effective_question_text"])
        self.assertTrue(normalized["edits"])
        p.complete.assert_called_once()
        self.assertFalse(normalized["meaning_preservation_guaranteed"])

    def test_gate_detects_unlisted_typing_shapes(self):
        for text in ["aqoh ndeee nbayarann ng kompanya", "myprvtcmpny didntpayme", "d1aq0 nabay4r4n"]:
            with self.subTest(text=text):
                self.assertTrue(assess_text(text)["needed"])
        for text in ["Si Amu at Anu ay bumili sa tindahan.", "Hindi ko nakuha ang bayad sa amo ko.",
                     "Ano ang gagawin ko?", "anu ang gagawin ko?"]:
            self.assertFalse(assess_text(text)["needed"])

    def test_clear_language_and_isolated_typo_make_zero_provider_calls(self):
        p = provider()
        normalizer = ConditionalNormalizer(p)
        for text in ["The cashier charged more than the displayed price.",
                     "Private employee ako. Hindi bayad ang overtime ko.",
                     "My employer hasn't paid my salary. What can I do?",
                     "hndi po bayad ang overtime ko sa private company.",
                     "DTI, DOLE, SSS, NLRC, RA 7394, PHP 500 on 2026-10-19."]:
            with self.subTest(text=text):
                result = normalizer.prepare(text)
                self.assertEqual(result["status"], "bypassed")
                self.assertEqual(result["effective_question_text"], text)
                self.assertEqual(result["llm_calls"], 0)
        p.complete.assert_not_called()

    def test_shorthand_calls_once_and_preserves_facts(self):
        p = provider()
        result = ConditionalNormalizer(p).prepare(NOISY)
        self.assertEqual(result["status"], "applied", result.get("validation_failure"))
        self.assertEqual(result["original_question_text"], NOISY)
        self.assertIn("municipal employee din si Ana, PHP 500 noong 2026-10-19", result["effective_question_text"])
        self.assertEqual(result["llm_calls"], 1)
        p.complete.assert_called_once()

    def test_absent_credentials_only_affect_flagged_messages(self):
        n = ConditionalNormalizer()
        self.assertEqual(n.prepare("Private employee ako. Hindi bayad ang overtime ko.")["status"], "bypassed")
        result = n.prepare(NOISY)
        self.assertEqual(result["status"], "unconfigured")
        self.assertIsNone(result["effective_question_text"])
        self.assertEqual(result["llm_calls"], 0)

    def test_unclear_or_timeout_never_passes_an_interpretation(self):
        unclear = ConditionalNormalizer(provider({"status": "unclear", "normalized_question": ""})).prepare(NOISY)
        self.assertEqual(unclear["status"], "clarify")
        self.assertIsNone(unclear["effective_question_text"])
        p = provider()
        p.complete.side_effect = NormalizationUnavailable("secret-response-must-not-be-returned")
        result = ConditionalNormalizer(p).prepare(NOISY)
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("secret-response", json.dumps(result))
        p.complete.assert_called_once()

    def test_dti_is_never_blindly_expanded(self):
        text = "prng gn2 kmi mag type dti"
        result = ConditionalNormalizer(provider(rewrite("parang ganito kami mag type dati"))).prepare(text)
        self.assertEqual(result["status"], "clarify")
        self.assertEqual(result["validation_failure"], "agency_changed")

    def test_fact_injection_negation_deletion_and_invalid_schema_are_rejected(self):
        faithful = provider().complete.return_value.payload["normalized_question"]
        malformed = [rewrite(faithful.replace("500", "1000")),
                     rewrite(faithful.replace("municipal", "private")),
                     rewrite(faithful.replace("Ana", "Maria")),
                     rewrite(faithful.replace("hindi po", "oo po")),
                     rewrite(faithful.split(";")[0]),
                     rewrite(faithful.replace("2026-10-19", "2026-10-20")),
                     {**rewrite(faithful), "answer": "fabricated legal advice"},
                     {"status": "unclear", "normalized_question": faithful},
                     {"status": [], "normalized_question": ""},
                     rewrite(faithful + " Contact a lawyer and file in court.")]
        for payload in malformed:
            with self.subTest(payload=payload):
                result = ConditionalNormalizer(provider(payload)).prepare(NOISY)
                self.assertEqual(result["status"], "clarify")
                self.assertIsNone(result["effective_question_text"])

    def test_missing_employment_and_payment_facts_cannot_be_invented(self):
        for text in ["Hindi ko nakuha ang sahod ko sa private company. Ano ang gagawin ko?",
                     "Hindi ko nakuha yung bayad ko sa government employer ko. Ano ang gagawin ko?"]:
            result = ConditionalNormalizer(provider(rewrite(text))).prepare(REPORTED)
            self.assertEqual(result["status"], "clarify")
            self.assertIsNone(result["effective_question_text"])

    def test_dense_unknown_noise_can_ask_for_clarification(self):
        p = provider({"status": "unclear", "normalized_question": ""})
        result = ConditionalNormalizer(p).prepare("xkzpt wrkplzzz")
        self.assertEqual(result["status"], "clarify")
        p.complete.assert_called_once()

    def test_provider_can_decline_unnecessary_rewrite(self):
        result = ConditionalNormalizer(provider({"status": "unchanged", "normalized_question": ""})).prepare(NOISY)
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(result["effective_question_text"], NOISY)

    def test_terminal_does_not_run_inference_when_normalization_is_unresolved(self):
        from backend.test_terminal_test import result as make_result
        baseline = make_result()
        baseline["routing"].update(routing_action="clarify", reason="no_reliable_component_evidence")
        verifier = Mock(preflight=Mock(return_value=baseline))
        packet = inspect_question(verifier, NOISY, normalizer=ConditionalNormalizer())
        verifier.preflight.assert_called_once_with(NOISY, mode="current_guidance")
        self.assertIsNone(packet["result"])
        self.assertIn("Classifier and retrieval were not run", format_inspection(packet))

    def test_unknown_wording_fallback_is_not_low_confidence_alone(self):
        unknown = "nawitheldan sahod sa kompanyah papanu"
        no_evidence = {"routing_action": "clarify", "reason": "no_reliable_component_evidence"}
        self.assertFalse(assess_text(unknown)["needed"])
        self.assertTrue(assess_text(unknown, no_evidence)["needed"])
        for route in [{"routing_action": "clarify", "reason": "employment_category_missing"},
                      {"routing_action": "clarify", "reason": "low_confidence"},
                      {"routing_action": "refer_out_of_scope", "reason": "recognized_excluded_concern"}]:
            self.assertFalse(assess_text(unknown, route)["needed"])
        self.assertFalse(assess_text("My employer has not paid my salary", no_evidence)["needed"])
    def test_clear_specialized_scope_does_not_pay_for_vocabulary_fallback(self):
        route={'routing_action':'clarify','reason':'no_identified_concern'}
        clear='Seafarer ako at hindi tugma ang sea-service record na ibinigay ng shipping company. Paano ko ipapa-correct ang maritime record?'
        self.assertFalse(assess_text(clear,route)['needed'])
        noisy='Seafarer aq hnd tugma record nmn sa cmpny'
        self.assertTrue(assess_text(noisy,route)['needed'])


class ProviderTests(unittest.TestCase):
    def envelope(self, status="completed"):
        return {"status": status, "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps({"status": "unclear", "normalized_question": ""})}]}],
                "usage": {"input_tokens": 12, "output_tokens": 8, "arbitrary": "ignored"}}

    def test_actual_http_contract_is_bounded_stateless_and_structured(self):
        response = io.BytesIO(json.dumps(self.envelope()).encode())
        opener = Mock()
        opener.open.return_value = response
        with patch("backend.normalization_provider.urllib.request.build_opener", return_value=opener):
            result = OpenAIProvider(model="configured-model", api_key="test-secret").complete(NOISY, assess_text(NOISY))
        request = opener.open.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertFalse(body["store"])
        self.assertTrue(body["text"]["format"]["strict"])
        self.assertNotIn("tools", body)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 12)
        self.assertEqual(opener.open.call_count, 1)
        self.assertEqual(result.usage, {"input_tokens": 12, "output_tokens": 8})

    def test_incomplete_refused_and_bad_json_responses_fail_closed(self):
        envelopes = [self.envelope("incomplete"),
                     {"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal"}]}]},
                     {"status": "completed", "output": []}]
        for envelope in envelopes:
            opener = Mock()
            opener.open.return_value = io.BytesIO(json.dumps(envelope).encode())
            with patch("backend.normalization_provider.urllib.request.build_opener", return_value=opener):
                with self.assertRaises(NormalizationUnavailable):
                    OpenAIProvider(model="configured-model", api_key="test-secret").complete(NOISY, [])

    def test_http_error_never_leaks_response_or_key_and_does_not_retry(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError("https://api.openai.com/v1/responses", 401, "test-secret", {}, None)
        with patch("backend.normalization_provider.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(NormalizationUnavailable) as raised:
                OpenAIProvider(model="configured-model", api_key="test-secret").complete(NOISY, [])
        self.assertNotIn("test-secret", str(raised.exception))
        opener.open.assert_called_once()


class TogetherTests(unittest.TestCase):
    def test_stronger_model_uses_bounded_low_reasoning_and_sentence_schema(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(json.dumps(self.envelope()).encode())
        with patch("backend.normalization_provider.urllib.request.build_opener", return_value=opener):
            TogetherProvider(model="openai/gpt-oss-120b", api_key="test-secret").complete(NOISY, assess_text(NOISY))
        body = json.loads(opener.open.call_args.args[0].data)
        self.assertEqual(body["reasoning_effort"], "low")
        self.assertEqual(body["max_tokens"], 1536)
        schema = body["response_format"]["json_schema"]["schema"]
        self.assertEqual(set(schema["required"]), {"status", "normalized_question"})
        self.assertNotIn("editable_spans", json.loads(body["messages"][1]["content"]))
        self.assertTrue(all("candidates" not in s for s in assess_text(NOISY)["trigger_spans"]))

    def envelope(self):
        return {"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"status": "unclear", "normalized_question": ""})}}],
                "usage": {"prompt_tokens": 15, "completion_tokens": 9, "total_tokens": 24}}

    def test_together_request_schema_usage_and_identification(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(json.dumps(self.envelope()).encode())
        with patch("backend.normalization_provider.urllib.request.build_opener", return_value=opener):
            completion = TogetherProvider(model="Qwen/Qwen3.5-9B", api_key="test-secret").complete(NOISY, [])
        request = opener.open.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.together.ai/v1/chat/completions")
        self.assertEqual(request.get_header("User-agent"), "RectoNormalizer/1.0")
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertFalse(body["reasoning"]["enabled"])
        self.assertEqual(body["max_tokens"], 768)
        self.assertNotIn("tools", body)
        self.assertEqual(completion.usage, {"input_tokens": 15, "output_tokens": 9, "total_tokens": 24})
        opener.open.assert_called_once()

    def test_together_incomplete_refusal_tool_calls_and_bad_json_are_rejected(self):
        cases = []
        incomplete = self.envelope()
        incomplete["choices"][0]["finish_reason"] = "length"
        cases.append(incomplete)
        refusal = self.envelope()
        refusal["choices"][0]["message"]["refusal"] = "refused"
        cases.append(refusal)
        tools = self.envelope()
        tools["choices"][0]["message"]["tool_calls"] = [{}]
        cases.append(tools)
        malformed = self.envelope()
        malformed["choices"][0]["message"]["content"] = "not JSON"
        cases.append(malformed)
        for envelope in cases:
            opener = Mock()
            opener.open.return_value = io.BytesIO(json.dumps(envelope).encode())
            with patch("backend.normalization_provider.urllib.request.build_opener", return_value=opener):
                with self.assertRaises(NormalizationUnavailable):
                    TogetherProvider(model="configured-model", api_key="test-secret").complete(NOISY, [])

    def test_together_http_error_is_redacted_and_not_retried(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError("https://api.together.ai/v1/chat/completions", 401, "test-secret", {}, None)
        with patch("backend.normalization_provider.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(NormalizationUnavailable) as raised:
                TogetherProvider(model="configured-model", api_key="test-secret").complete(NOISY, [])
        self.assertIn("401", str(raised.exception))
        self.assertNotIn("test-secret", str(raised.exception))
        opener.open.assert_called_once()


class ConfigurationTests(unittest.TestCase):
    def test_together_environment_overrides_local_configuration(self):
        with patch.dict(os.environ, {"RECTO_NORMALIZER_PROVIDER": "together", "RECTO_NORMALIZER_MODEL": "env-model", "TOGETHER_API_KEY": "test-secret"}, clear=True), \
             patch.object(normalizer_credentials, "read_local_config", return_value={"provider": "openai", "model": "old-model"}), \
             patch.object(normalizer_credentials, "read_key") as read_key:
            normalizer = from_environment()
            self.assertEqual(normalizer.provider.name, "together")
            self.assertEqual(normalizer.provider.model, "env-model")
            read_key.assert_not_called()

    def test_local_encrypted_config_can_supply_together_without_env(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(normalizer_credentials, "read_local_config", return_value={"provider": "together", "model": "local-model"}), \
             patch.object(normalizer_credentials, "read_key", return_value="test-secret") as read_key:
            normalizer = from_environment()
            self.assertEqual(normalizer.provider.model, "local-model")
            read_key.assert_called_once_with("together")

    @unittest.skipUnless(os.name == "nt", "Windows-user encryption only")
    def test_real_dpapi_roundtrip_never_writes_plaintext_key(self):
        workspace = Path(__file__).resolve().parents[1]
        temporary_root = (workspace / ".local").resolve()
        self.assertTrue(temporary_root.is_relative_to(workspace))
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root, prefix="normalizer-test-") as directory, patch.object(normalizer_credentials, "LOCAL", Path(directory)):
            normalizer_credentials.save_together("synthetic-secret-for-encryption-test")
            blob = (Path(directory) / "together.key.dpapi").read_bytes()
            self.assertNotIn(b"synthetic-secret", blob)
            self.assertEqual(normalizer_credentials.read_key("together"), "synthetic-secret-for-encryption-test")
            self.assertNotIn("secret", (Path(directory) / "provider.json").read_text())


if __name__ == "__main__":
    unittest.main()
