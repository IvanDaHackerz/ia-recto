"""Observed AI-on failures: scope isolation, source conditions and wording."""
import unittest
from unittest.mock import Mock
from backend.application.grounding import source_qualification_failure,numeric_facts,prose_locators
from backend.application.development_explanation import checked_claims
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime


class QualificationTests(unittest.TestCase):
    def test_prose_locator_must_match_actual_selected_citation(self):
        source={'chunk_id':'test_chunk','provision_id':'test_provision','document_id':'test_document',
                'citation_display':'Labor Code, ART. 94','parent_text':'This recorded passage mentions Article 87 as a cross-reference.'}
        components=[{'component_id':'concern_001','sources':[source]}]
        def draft(text):return {'paragraphs':[{'component_id':'concern_001','text':text,'evidence':[{'chunk_id':'test_chunk','quote':source['parent_text']}]}]}
        self.assertEqual(len(checked_claims(draft('Article 94 is the selected recorded provision.'),components)),1)
        with self.assertRaisesRegex(ValueError,'Uncited prose locator'):
            checked_claims(draft('Article 87 is the selected recorded provision.'),components)
        self.assertEqual(prose_locators('Art. 94 and Section 2'),{('article','94'),('section','2')})

    def test_ordinary_overtime_rate_preserves_its_day_condition(self):
        source='On ordinary working days, overtime is paid at the wage plus twenty-five percent.'
        self.assertIsNotNone(source_qualification_failure('Any work beyond eight hours in a day is overtime at 25 percent.',source))
        self.assertIsNone(source_qualification_failure('On an ordinary workday, covered overtime adds 25 percent.',source))
        self.assertIsNotNone(source_qualification_failure('Overtime pay is triggered only when the employee works beyond eight hours on an ordinary working day.',source))

    def test_status_exception_cannot_smuggle_in_a_casual_determination(self):
        source='The specific project and seasonal exceptions apply. Casual employment has a separate one year rule.'
        self.assertIsNotNone(source_qualification_failure('The seasonal exception means the casual employment rule determines the status.',source))
        self.assertIsNotNone(source_qualification_failure('For a project or a seasonal task whose completion date is set at hiring, different status applies.',source))
        self.assertIsNone(source_qualification_failure('The seasonal exception concerns work for the duration of the season.',source))
        self.assertIsNotNone(source_qualification_failure('If those exceptions do not apply, the employment is casual.',source))
        self.assertIsNone(source_qualification_failure('The source separately defines casual employment.',source))

    def test_immediate_product_remedy_is_an_alternative_condition(self):
        source='If the imperfection is not corrected within the period, options follow. The consumer may make immediate use of the alternatives if repair jeopardizes quality.'
        self.assertIsNotNone(source_qualification_failure('Remedies are available when (a) the period has elapsed and (b) repair jeopardizes quality.',source))
        self.assertIsNone(source_qualification_failure('The immediate-use exception can apply if repair jeopardizes quality, without waiting for the correction period.',source))

    def test_retailer_forwarding_does_not_eliminate_subsidiary_costs(self):
        source='The retailer is subsidiarily liable if both the manufacturer and distributor fail.'
        self.assertIsNotNone(source_qualification_failure('The retailer forwards the claim but does not bear the warranty costs.',source))
        self.assertIsNone(source_qualification_failure('The retailer forwards the claim; subsidiary liability can arise if the other parties fail.',source))
        source='The retailer is subsidiarily liable in case of failure of both the manufacturer and distributor.'
        self.assertIsNotNone(source_qualification_failure('If the manufacturer or distributor fails, the retailer is subsidiarily liable.',source))
        self.assertIsNone(source_qualification_failure('If both the manufacturer and distributor fail, the retailer is subsidiarily liable.',source))
    def test_money_claim_process_cannot_drop_its_jurisdiction_conditions(self):
        source='Such complaint does not include a claim for reinstatement. Claims do not exceed five thousand pesos.'
        self.assertIsNotNone(source_qualification_failure('Any unpaid salary can be recovered by filing a complaint with the Regional Director.',source))
        self.assertIsNone(source_qualification_failure('The Regional Director can hear a money complaint within the five thousand peso limit, excluding reinstatement.',source))

    def test_mandatory_conciliation_cannot_erase_recorded_exceptions(self):
        source='All issues are subject to conciliation, as may be excepted by the Secretary.'
        self.assertIsNotNone(source_qualification_failure('All labor disputes must undergo mandatory conciliation.',source))
        self.assertIsNone(source_qualification_failure('All labor disputes generally undergo mandatory conciliation, subject to exceptions.',source))

    def test_agreed_period_variation_can_use_equivalent_words(self):
        source='The parties may agree to reduce or increase the term.'
        self.assertIsNone(source_qualification_failure('The default is thirty days; the parties may adjust the correction period.',source))
        self.assertIsNotNone(source_qualification_failure('The consumer must always wait thirty days.',source))

    def test_temporal_first_is_not_an_invented_quantity(self):
        self.assertEqual(numeric_facts('First wait, then contact the seller. First lodge the complaint.'),set())
        self.assertEqual(numeric_facts('The first day and thirty days are calendar quantities.'),{'1.0','30.0'})
        self.assertEqual(numeric_facts('Without first having to wait for correction.'),set())

    def test_privacy_advice_is_not_authorized_by_retail_civil_liability(self):
        text='The retailer is primarily liable, including a separate privacy complaint for posting the ID.'
        self.assertIsNotNone(source_qualification_failure(text,'The merchant has civil and administrative liability.'))
        self.assertIsNone(source_qualification_failure('The recorded rule does not cover the separate privacy complaint.','Retail remedies.'))

    def test_reported_seal_is_not_a_legal_finding(self):
        self.assertIsNotNone(source_qualification_failure('A damaged seal therefore falls within these definitions and prohibitions.','The law prohibits unsafe products.'))
        self.assertIsNone(source_qualification_failure('Whether a damaged seal meets the safety definition requires the relevant facts.','The law prohibits unsafe products.'))

    def test_authorized_cause_cannot_be_erased_from_invalid_dismissal_test(self):
        source='The employer shall not terminate except for a just cause or when authorized by this Title.'
        self.assertIsNotNone(source_qualification_failure('If dismissal is not for a just cause, it is deemed unjust.',source))
        self.assertIsNone(source_qualification_failure('Termination requires a just or authorized cause.',source))


class ScopePromptTests(unittest.TestCase):
    def test_excluded_allegations_are_not_sent_to_supported_explanation(self):
        provider=Mock();provider.name='test';provider.model='mock'
        provider.complete.side_effect=lambda question,pre: {'paragraphs':[{'component_id':c['component_id'],'text':'The recorded source describes the rule; applicability needs the relevant facts.','evidence':[{'chunk_id':c['sources'][0]['chunk_id'],'quote':c['sources'][0]['parent_text'][:120]}]} for c in pre['components']]}
        provider.assess.side_effect=lambda question,claims,components: {'assessments':[{'claim_id':c['claim_id'],'verdict':'supported','qualifications_preserved':True,'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True} for c in claims]}
        service=ApplicationService(verifier=load_runtime(),normalizer=ConditionalNormalizer(),development_provider=provider)
        packet=service.chat({'question_text':'An online retailer sent the wrong model of kettle. The seller also posted my ID publicly; I want to pursue that privacy complaint separately.','use_ai':True,'save_history':False})
        self.assertEqual(packet['explanation']['status'],'generated')
        prompt=provider.complete.call_args.args[0]
        self.assertTrue(prompt.startswith('Explain only these supported concerns:'))
        self.assertNotIn('privacy',prompt)
        self.assertNotIn('posted my id',prompt)
        self.assertTrue(packet['result']['excluded_components'])
