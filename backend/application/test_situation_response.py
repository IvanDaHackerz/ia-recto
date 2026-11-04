"""Situation-level responses preserve evidence, scope, privacy and AI provenance."""
import copy
import json
import unittest
from unittest.mock import patch

from backend.application.service import ApplicationService
from backend.application.development_explanation import TogetherDevelopmentExplanation
from backend.application.situation_response import CHECKS, request_guidance
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime

CINEMA = 'A private cinema requires ticket staff to count their cash drawers before clocking in. Does this required preparation count as working time?'


class ScriptedProvider(TogetherDevelopmentExplanation):
    """Actual provider interface with no network or credentials."""
    def __init__(self):
        super().__init__('test', 'fictional')
        self.requests = []
        self.draft = {'situation': 'You described a salary deduction in a government job.', 'paragraphs': ['This project’s private-sector sources cannot establish the rule for that employment; the assistance contacts below are a place to check the appropriate route.']}
        self.check = {key: True for key in CHECKS}

    def fork(self):
        return self

    def complete(self, question, preflight):
        return {'paragraphs': []}

    def _send(self, body):
        self.requests.append(copy.deepcopy(body))
        name = body['response_format']['json_schema']['name']
        return copy.deepcopy(self.check if name == 'situation_response_check' else self.draft)


class SituationResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = load_runtime()

    def service(self, provider=None):
        return ApplicationService(verifier=self.verifier, normalizer=ConditionalNormalizer(), development_provider=provider)

    def test_cinema_scenario_has_one_working_time_component_and_recomputed_gates(self):
        packet = self.service().chat({'question_text': CINEMA, 'use_ai': False})
        components = packet['result']['components']
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0]['query'], CINEMA)
        self.assertEqual(len(packet['situation_context']['original_components']), 2)
        self.assertEqual(packet['original_question_text'], CINEMA)
        self.assertTrue(packet['response']['quotes'])
        self.assertIn('working time', ' '.join(packet['response']['paragraphs']))
        self.assertTrue(all('hours' in (h['heading'] or '').lower() or 'rest periods' in (h['heading'] or '').lower() for h in components[0]['candidates']))
        for gate, hit in zip(components[0]['evidence_gates'], components[0]['candidates']):
            self.assertEqual(gate, self.verifier.source_gate(CINEMA, components[0], hit, packet['result']['mode']))
        self.assertFalse(packet['result']['answer_generation_allowed'])
        self.assertFalse(packet['response']['ai_generated'])

    def test_independent_and_excluded_concerns_are_not_collapsed(self):
        for text in [
            'My private employer has withheld salary. Separately, I was dismissed without notice.',
            'My private employer has withheld salary. Separately, my bank charged a credit-card fee.',
            'My private employer has withheld salary. A retailer also refuses to replace my defective lamp.',
        ]:
            with self.subTest(text=text):
                packet = self.service().chat({'question_text': text, 'use_ai': False})
                self.assertNotIn('situation_context', packet)
                self.assertGreaterEqual(len(packet['result']['components']) + len(packet['result']['excluded_components']), 2)

    def test_excluded_question_gets_real_checked_ai_guidance_without_legal_claims(self):
        provider = ScriptedProvider()
        packet = self.service(provider).chat({'question_text': 'Government employee ako. May salary deduction na gusto kong i-dispute.'})
        self.assertEqual(packet['result']['routing']['predicted_scope'], 'unsupported')
        self.assertEqual(packet['response']['kind'], 'ai_guidance')
        self.assertTrue(packet['response']['ai_generated'])
        self.assertTrue(packet['response']['context_checked'])
        self.assertEqual(packet['response']['generation']['llm_calls'], 2)
        self.assertEqual(len(provider.requests), 2)
        self.assertFalse(packet['explanation']['claims'])
        self.assertFalse(packet['explanation']['automated_support_checked'])
        self.assertFalse(packet['response']['quotes'])

    def test_uncertain_city_office_role_gets_the_relevant_employment_follow_up(self):
        packet = self.service().chat({'question_text': "Regular employee ako ng city treasurer's office. May salary deduction na gusto kong i-dispute. Anong rules ang puwede mong i-apply?", 'use_ai': False})
        self.assertIn('government-employed', packet['response']['follow_up'])
        self.assertIn('private company', packet['response']['follow_up'])
        self.assertFalse(packet['response']['ai_generated'])

    def test_context_rejection_and_malformed_reports_keep_local_response(self):
        for report in [{**{key: True for key in CHECKS}, 'no_new_legal_claims': False}, {}, {key: 'true' for key in CHECKS}]:
            with self.subTest(report=report):
                provider = ScriptedProvider(); provider.check = report
                packet = self.service(provider).chat({'question_text': 'Government employee ako. May salary deduction na gusto kong i-dispute.'})
                self.assertFalse(packet['response']['ai_generated'])
                self.assertTrue(packet['response']['paragraphs'])
                self.assertNotIn(provider.draft['paragraphs'][0], packet['response']['paragraphs'])

    def test_no_extra_legal_deadline_or_outcome_can_bypass_context_review(self):
        for text in ['You will win the case.', 'You must receive payment within 999999 days.', 'Article 999 requires a refund.']:
            provider = ScriptedProvider(); provider.draft = {'situation': 'You described a government salary concern.', 'paragraphs': [text]}
            output, status = request_guidance(provider, 'A government salary concern.', {'paragraphs': ['Outside private-sector coverage.']})
            self.assertIsNone(output)
            self.assertEqual(status['reason'], 'invalid_guidance')
            self.assertEqual(len(provider.requests), 1)

    def test_ai_off_and_immediate_safety_do_not_call_conversation_provider(self):
        for question, use_ai in [('Government employee ako. May salary deduction.', False), ('I am being stabbed.', True)]:
            provider = ScriptedProvider()
            packet = self.service(provider).chat({'question_text': question, 'use_ai': use_ai})
            self.assertFalse(provider.requests)
            self.assertFalse(packet['response']['ai_generated'])

    def test_guidance_uses_redacted_question_and_never_a_rejected_draft(self):
        provider = ScriptedProvider()
        packet = self.service(provider).chat({'question_text': 'Government employee ako. My email is fictional@example.com. May salary deduction.'})
        exported = json.dumps(provider.requests)
        self.assertNotIn('fictional@example.com', exported)
        self.assertNotIn('rejected_prose', exported)
        self.assertTrue(packet['privacy']['redacted'])

    def test_cancellation_during_guidance_is_not_returned_as_a_completed_response(self):
        from backend.classifier.contracts import RequestError
        provider = ScriptedProvider()
        with patch.object(provider, '_send', side_effect=RequestError('request_canceled', 'Request canceled.', 499)):
            with self.assertRaises(RequestError):
                request_guidance(provider, 'A wage question.', {'paragraphs': ['A limitation.']})

    def test_reported_quantities_are_separate_from_cited_legal_quantities(self):
        from backend.application.development_explanation import checked_claims
        record = next(r for r in self.verifier.records.values() if r['provision_id'] == 'LAB_IRR_1989__rule_i_hours_of_work__section_8')
        components = [{'component_id': 'c1', 'query': 'My employer requires two extra hours after my eight-hour shift.', 'sources': [record]}]
        paragraph = {'component_id': 'c1', 'situation': 'You describe two extra hours after your eight-hour shift.',
            'text': 'For a covered employee, the recorded ordinary-day overtime rule applies to work beyond eight hours, subject to its stated conditions.',
            'evidence': [{'chunk_id': record['chunk_id'], 'quote': record['parent_text']}]}
        claims = checked_claims({'paragraphs': [paragraph]}, components)
        self.assertIn('two extra hours', claims[0]['text'])
        paragraph['situation'] = 'You describe nine extra hours after your shift.'
        with self.assertRaisesRegex(ValueError, 'Invented scenario quantity'):
            checked_claims({'paragraphs': [paragraph]}, components)
        paragraph['situation'] = 'You describe two extra hours after your eight-hour shift.'
        paragraph['text'] = 'A covered employee receives an additional two percent.'
        with self.assertRaisesRegex(ValueError, 'Uncited numeric detail'):
            checked_claims({'paragraphs': [paragraph]}, components)
