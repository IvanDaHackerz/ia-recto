"""Concern regressions and citation-bound development generation; no paid calls."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
from backend.terminal_test import ROOT, load_runtime
from backend.normalization import ConditionalNormalizer
from backend.application.service import ApplicationService
from backend.application.development_explanation import checked_claims, explain_recorded_sources
from backend.application.safety import safety_notice


class ConcernTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = load_runtime()

    def test_all_frozen_random_background_and_supported_concerns(self):
        from backend.classifier.service import ClassifierService
        service = ClassifierService()
        rows = [json.loads(x) for x in (ROOT / 'outputs/website-explanations-v1.0.0/concern_cases.jsonl').read_text(encoding='utf-8').splitlines()]
        for case in rows:
            with self.subTest(case=case['case_id']):
                r = service.classify({'question_text': case['question_text']})
                self.assertEqual(r['routing']['action'], case['expected_route'])
                if case['expected_primary']:
                    self.assertEqual(r['classification']['primary_label'], case['expected_primary'])

    def test_reported_harm_never_reaches_either_provider(self):
        wording, explanation = Mock(), Mock()
        service = ApplicationService(verifier=self.verifier, normalizer=ConditionalNormalizer(wording), development_provider=explanation)
        p = service.chat({'question_text': 'I was about to get my pay, but i got stabbed in the street.'})
        self.assertEqual(p['result']['routing']['predicted_primary'], 'out_of_scope')
        self.assertEqual(p['result']['routing']['routing_action'], 'refer_out_of_scope')
        self.assertEqual(p['result']['components'], [])
        self.assertEqual(p['safety_notice']['emergency_number'], '911')
        self.assertEqual(p['explanation']['llm_calls'], 0)
        wording.complete.assert_not_called(); explanation.complete.assert_not_called()

    def test_safety_notice_does_not_turn_negation_or_a_termination_report_into_harm(self):
        for text in ['I was not stabbed.', 'My private employer fired me after I reported an assault.', 'My private employer did not pay overtime.']:
            self.assertIsNone(safety_notice(text))

    def test_real_supported_sources_generate_without_invented_legal_approval(self):
        provider = Mock(); provider.name, provider.model = 'test', 'mock'
        def complete(question, pre):
            return {'paragraphs': [{'component_id': c['component_id'], 'text': 'The recorded source describes this rule; its application needs the relevant facts.',
                'evidence': [{'chunk_id': c['sources'][0]['chunk_id'], 'quote': c['sources'][0]['parent_text'][:120]}]} for c in pre['components']]}
        provider.complete.side_effect = complete
        provider.assess.side_effect = lambda question,claims,components: {'assessments':[{'claim_id':c['claim_id'],'verdict':'supported','qualifications_preserved':True,'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True} for c in claims]}
        service = ApplicationService(verifier=self.verifier, normalizer=ConditionalNormalizer(), development_provider=provider)
        p = service.chat({'question_text': 'Private employee ako. Ilang oras ang normal na workday bago maging excess hours?'})
        self.assertEqual(p['explanation']['status'], 'generated')
        self.assertTrue(p['explanation']['citations_checked'])
        self.assertFalse(p['explanation']['legal_support_verified'])
        self.assertFalse(p['result']['answer_generation_allowed'])
        self.assertFalse(p['result']['display_allowed'])
        self.assertEqual(p['explanation']['llm_calls'], 2)
        self.assertTrue(p['explanation']['automated_support_checked'])

    def test_outside_and_clarification_do_not_generate(self):
        provider = Mock()
        for q in ['Who gets custody of our child?', 'Late ang salary ko.', 'What is the weather tomorrow?']:
            p = self.verifier.preflight(q)
            self.assertEqual(explain_recorded_sources(self.verifier, p, provider)['llm_calls'], 0)
        provider.complete.assert_not_called()


class CitationTests(unittest.TestCase):
    def revision_fixture(self):
        provider,verifier=Mock(),Mock();provider.name='test';provider.model='mock';provider.last_usage={};provider.can_revise=True
        verifier.check_candidate.return_value=[]
        hit={**self.components[0]['sources'][0],'conditions':[]}
        pre={'question_text':'Fictional question','routing':{'routing_action':'retrieve_supported_evidence'},
             'components':[{'component_id':'c1','query':'Fictional question','allowed_domain':'labor',
                            'candidates':[hit],'evidence_gates':[{'chunk_id':'h1','reasons':[]}]}]}
        provider.complete.return_value=copy.deepcopy(self.draft);provider.revise.return_value=copy.deepcopy(self.draft)
        return provider,verifier,pre

    @staticmethod
    def assessment(qualified,verdict='supported',claim_id='development_1'):
        return {'assessments':[{'claim_id':claim_id,'verdict':verdict,'qualifications_preserved':qualified,
                               'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True}]}

    def test_qualification_revision_requires_a_new_complete_check(self):
        provider,verifier,pre=self.revision_fixture()
        provider.assess.side_effect=[self.assessment(False),self.assessment(True)]
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['llm_calls'],4)
        self.assertTrue(result['revision_attempted']);provider.revise.assert_called_once()
        self.assertEqual(provider.assess.call_count,2)

    def test_revision_is_bounded_and_does_not_override_a_second_failed_check(self):
        provider,verifier,pre=self.revision_fixture()
        provider.assess.return_value=self.assessment(False)
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['reason'],'claim_support_failed');self.assertEqual(result['claims'],[])
        self.assertEqual(result['llm_calls'],4);provider.revise.assert_called_once()

    def test_unsafe_mismatched_or_time_limited_checks_do_not_trigger_revision(self):
        unsafe=self.assessment(False,'unsupported');unsafe['assessments'][0]['no_case_outcome']=False
        for report,allowed in [(unsafe,True),(self.assessment(False,claim_id='wrong'),True),(self.assessment(False),False)]:
            provider,verifier,pre=self.revision_fixture();provider.assess.return_value=report;provider.can_revise=allowed
            result=explain_recorded_sources(verifier,pre,provider)
            self.assertEqual(result['claims'],[]);self.assertEqual(result['llm_calls'],2);provider.revise.assert_not_called()

    def test_citation_support_correction_still_requires_a_passed_new_assessment(self):
        provider,verifier,pre=self.revision_fixture()
        provider.assess.side_effect=[self.assessment(True,'unsupported'),self.assessment(True)]
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['llm_calls'],4)
        provider.revise.assert_called_once()

    def test_revised_invented_quote_is_rejected_before_a_second_assessment(self):
        provider,verifier,pre=self.revision_fixture();provider.assess.return_value=self.assessment(False)
        provider.revise.return_value['paragraphs'][0]['evidence'][0]['quote']='An invented source quotation.'
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['reason'],'citation_validation_failed');self.assertEqual(result['claims'],[])
        self.assertEqual(result['llm_calls'],3);self.assertEqual(provider.assess.call_count,1)

    def setUp(self):
        self.components = [{'component_id': 'c1', 'sources': [{'chunk_id': 'h1', 'provision_id': 'p1', 'document_id': 'd1',
            'citation_display': 'Recorded article', 'parent_text': 'The normal hours of work shall not exceed eight hours per day.'}]}]
        self.draft = {'paragraphs': [{'component_id': 'c1', 'text': 'The recorded text sets a limit on normal daily work hours.',
            'evidence': [{'chunk_id': 'h1', 'quote': 'normal hours of work shall not exceed eight hours per day.'}]}]}

    def test_exact_quote_offsets_are_calculated_from_stored_text(self):
        claims = checked_claims(self.draft, self.components); cite = claims[0]['citations'][0]
        text = self.components[0]['sources'][0]['parent_text']
        self.assertEqual(text[cite['start']:cite['end']], cite['quote'])

    def test_whitespace_only_quote_recovery_preserves_the_exact_stored_span(self):
        components = copy.deepcopy(self.components)
        components[0]['sources'][0]['parent_text'] = components[0]['sources'][0]['parent_text'].replace('not exceed', 'not\nexceed')
        cite = checked_claims(self.draft, components)[0]['citations'][0]
        self.assertIn('not\nexceed', cite['quote'])
        self.assertEqual(components[0]['sources'][0]['parent_text'][cite['start']:cite['end']], cite['quote'])

    def test_fabricated_quote_wrong_source_extra_fields_and_numbers_are_rejected(self):
        bad = []
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['evidence'][0]['quote'] = 'A fabricated quotation'; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['evidence'][0]['chunk_id'] = 'other'; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['text'] += ' Pay 999 pesos.'; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['approved'] = True; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['component_id'] = 'excluded'; bad.append(d)
        for draft in bad:
            with self.subTest(draft=draft), self.assertRaises(ValueError): checked_claims(draft, self.components)

    def test_missing_supported_component_is_not_silently_omitted(self):
        components = copy.deepcopy(self.components); components.append({**components[0], 'component_id': 'c2'})
        with self.assertRaises(ValueError): checked_claims(self.draft, components)

    def test_related_authority_and_fixture_gates_skip_provider(self):
        provider, verifier = Mock(), Mock()
        p = {'routing': {'routing_action': 'retrieve_supported_evidence'}, 'software_fixture_mode': True}
        self.assertEqual(explain_recorded_sources(verifier, p, provider)['llm_calls'], 0)
        p.update(software_fixture_mode=False, components=[{'evidence_gates': [{'chunk_id': 'x','reasons':['related_authority_unavailable:MO_28_1986']}]}])
        self.assertEqual(explain_recorded_sources(verifier, p, provider)['reason'], 'related_authority_missing')
        provider.complete.assert_not_called()

    def test_empty_supported_output_is_a_distinct_safe_withholding_state(self):
        provider,verifier=Mock(),Mock()
        provider.complete.return_value={'paragraphs':[]}
        verifier.check_candidate.return_value=[]
        pre={'question_text':'Fictional question','routing':{'routing_action':'retrieve_supported_evidence'},
             'components':[{'component_id':'c1','query':'Fictional question','allowed_domain':'labor',
                            'candidates':[self.components[0]['sources'][0]],'evidence_gates':[{'chunk_id':'h1','reasons':[]}]}]}
        pre['components'][0]['candidates'][0]['conditions']=[]
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['reason'],'no_supported_explanation')
        self.assertEqual(result['claims'],[])
        self.assertEqual(result['llm_calls'],1)
        provider.assess.assert_not_called()


if __name__ == '__main__': unittest.main()
