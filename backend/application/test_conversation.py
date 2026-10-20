"""Application helpfulness and scope boundaries; no live provider requests."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from backend.application.conversation import prepare_general_information, response_for
from backend.application.identity import identity
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime


class ConversationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = load_runtime()
        cls.service = ApplicationService(verifier=cls.verifier, normalizer=ConditionalNormalizer())

    def ask(self, question):
        return self.service.chat({'question_text': question, 'use_ai': False})

    def test_missing_employment_context_gets_conditional_sources_and_preserves_original(self):
        for question in ['Late ang salary ko.', 'Late ang salry ko.', 'My employer has not paid my wages. What can I do?', 'Hindi binayaran ang overtime ko.']:
            with self.subTest(question=question):
                packet = self.ask(question)
                self.assertEqual(packet['original_question_text'], question)
                context = packet['guidance_context']
                self.assertTrue(context['classification_is_conditional'])
                self.assertEqual(context['original_routing']['routing_action'], 'clarify')
                self.assertIn('not been confirmed', context['note'])
                self.assertTrue(packet['response']['paragraphs'])
                self.assertEqual(len(packet['response']['follow_up_options']), 5)
                self.assertTrue(packet['response']['quotes'])
                self.assertFalse(packet['result']['answer_generation_allowed'])

    def test_explicit_excluded_categories_and_other_concerns_are_not_promoted(self):
        for question in ['Government employee ako. Hindi binayaran ang overtime ko.',
                         'OFW ako. My employer has not paid my wages.',
                         'My bank charged a hidden fee.', 'My landlord kept my rental deposit.']:
            with self.subTest(question=question):
                packet = self.ask(question)
                self.assertNotIn('guidance_context', packet)
                self.assertEqual(packet['result']['routing']['routing_action'], 'refer_out_of_scope')
                self.assertEqual(packet['response']['kind'], 'referral')
                self.assertFalse(packet['response']['ai_generated'])

    def test_mixed_concerns_keep_the_excluded_part(self):
        packet = self.ask('My employer has not paid wages and my landlord kept my deposit.')
        self.assertTrue(packet['guidance_context']['classification_is_conditional'])
        self.assertEqual(packet['result']['routing']['predicted_scope'], 'partially_supported')
        self.assertTrue(packet['result']['excluded_components'])
        self.assertTrue(all(c['allowed_domain'] == 'labor' for c in packet['result']['components']))

    def test_taglish_search_aliases_find_sources_without_changing_the_question(self):
        question = 'Sira yung binili kong phone at ayaw palitan ng shop.'
        packet = self.ask(question)
        self.assertEqual(packet['original_question_text'], question)
        self.assertIn('search_help', packet)
        self.assertFalse(packet['search_help']['changes_user_facts'])
        self.assertTrue(packet['response']['quotes'])
        self.assertEqual(packet['result']['routing']['predicted_primary'], 'consumer')

    def test_quote_fallback_remains_exact_and_never_includes_disputed_text(self):
        packet = self.ask('Private employee ako. What are normal working hours?')
        response = packet['response']
        for quote in response['quotes']:
            self.assertIn(quote['quote'], self.verifier.records[quote['chunk_id']]['parent_text'])
        from backend.application.source_issues import HOLIDAY_PROVISION
        self.assertNotIn(HOLIDAY_PROVISION, [self.verifier.records[q['chunk_id']]['provision_id'] for q in response['quotes']])
        self.assertFalse(response['ai_generated'])

    def test_every_completed_route_including_unclear_and_safety_has_prose(self):
        for question in ['Hello', 'My bank charged a hidden fee.', 'I am being stabbed.',
                         'Private employee ako. What are normal working hours?']:
            with self.subTest(question=question):
                packet = self.ask(question)
                self.assertTrue(packet['response']['paragraphs'])
                self.assertFalse(packet['response']['ai_generated'])

    def test_provider_failure_and_rejected_draft_still_get_a_local_response(self):
        packet = self.ask('Private employee ako. What are normal working hours?')
        for reason in ['provider_unavailable', 'claim_support_failed', 'citation_validation_failed']:
            with self.subTest(reason=reason):
                current = copy.deepcopy(packet)
                current['explanation'] = {'status': 'withheld', 'reason': reason, 'claims': [], 'llm_calls': 1}
                response = response_for(current, self.verifier, current['original_question_text'])
                self.assertTrue(response['paragraphs'])
                self.assertTrue(response['quotes'])
                self.assertFalse(response['ai_generated'])

    def test_uncited_numeric_draft_gets_one_correction_then_all_normal_checks(self):
        provider = Mock()
        provider.name, provider.model, provider.can_revise = 'test', 'mock', True
        def draft(question, preflight):
            return {'paragraphs': [{'component_id': c['component_id'],
                'text': 'The recorded rule applies subject to its stated conditions.',
                'evidence': [{'chunk_id': c['sources'][0]['chunk_id'], 'quote': c['sources'][0]['parent_text'][:120]}]} for c in preflight['components']]}
        def invalid(question, preflight):
            output = draft(question, preflight)
            output['paragraphs'][0]['text'] = 'A fictional unsupported deadline is 99999999 days.'
            return output
        provider.complete.side_effect = invalid
        provider.revise.side_effect = lambda question, preflight, claims, feedback: draft(question, preflight)
        provider.assess.side_effect = lambda question, claims, components: {'assessments': [{
            'claim_id': c['claim_id'], 'verdict': 'supported', 'qualifications_preserved': True,
            'no_case_outcome': True, 'no_excluded_advice': True, 'no_new_facts': True} for c in claims]}
        service = ApplicationService(verifier=self.verifier, normalizer=ConditionalNormalizer(), development_provider=provider)
        packet = service.chat({'question_text': 'My employer has not paid my wages. What wage-payment rules apply?'})
        self.assertEqual(packet['explanation']['status'], 'generated')
        self.assertEqual(packet['explanation']['llm_calls'], 3)
        provider.revise.assert_called_once()
        self.assertIn('has not been confirmed', provider.complete.call_args[0][0])
        self.assertIn('has not been confirmed', provider.assess.call_args[0][0])
        self.assertNotIn('99999999', json.dumps(packet))

    def test_failed_numeric_correction_cannot_pass_or_start_another_retry(self):
        provider = Mock()
        provider.name, provider.model, provider.can_revise = 'test', 'mock', True
        def invalid(question, preflight, *args):
            return {'paragraphs': [{'component_id': c['component_id'], 'text': 'A fictional deadline is 99999999 days.',
                'evidence': [{'chunk_id': c['sources'][0]['chunk_id'], 'quote': c['sources'][0]['parent_text'][:120]}]} for c in preflight['components']]}
        provider.complete.side_effect = provider.revise.side_effect = invalid
        service = ApplicationService(verifier=self.verifier, normalizer=ConditionalNormalizer(), development_provider=provider)
        packet = service.chat({'question_text': 'Private employee ako. What are normal working hours?'})
        self.assertEqual(packet['explanation']['status'], 'withheld')
        self.assertEqual(packet['explanation']['llm_calls'], 2)
        self.assertTrue(packet['response']['paragraphs'])
        provider.revise.assert_called_once()
        provider.assess.assert_not_called()


class ConfigurationIdentityTests(unittest.TestCase):
    def test_saved_credentials_and_feature_flags_change_reuse_identity_without_leaking_them(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]/'tmp') as directory:
            root = Path(directory)
            (root/'backend/application').mkdir(parents=True)
            for name in ['CURRENT_ARTIFACTS.json','backend/normalization.py','backend/normalization_provider.py']:
                (root/name).write_text('test', encoding='utf-8')
            with patch('backend.application.identity.ROOT', root), patch.dict(os.environ, {}, clear=True):
                original = identity()
                local = root/'.local/normalizer'
                local.mkdir(parents=True)
                (local/'together.key.dpapi').write_bytes(b'fictional-encrypted-value')
                changed = identity()
                self.assertNotEqual(original['runtime_signature'], changed['runtime_signature'])
                os.environ['RECTO_ENABLE_EXPLANATIONS'] = '0'
                self.assertNotEqual(changed['runtime_signature'], identity()['runtime_signature'])
                self.assertNotIn('fictional', json.dumps(identity()))
