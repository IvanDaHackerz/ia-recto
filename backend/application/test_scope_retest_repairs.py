"""Contrastive regressions from the fresh scope test; no external AI calls."""
import re
import unittest

from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime


class ScopeRetestRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = load_runtime()
        cls.service = ApplicationService(verifier=cls.verifier, normalizer=ConditionalNormalizer())

    def ask(self, text):
        packet = self.service.chat({'question_text': text, 'use_ai': False})
        self.assertEqual(packet['explanation']['llm_calls'], 0)
        self.assertFalse(packet['response']['ai_generated'])
        for quote in packet['response']['quotes']:
            self.assertIn(quote['quote'], self.verifier.records[quote['chunk_id']]['parent_text'])
        return packet

    def headings(self, packet):
        return [self.verifier.records[q['chunk_id']]['heading'] for q in packet['response']['quotes']]

    def test_local_specialized_job_descriptions_are_referrals(self):
        for text in [
            'Empleyado ako sa munisipyo at may salary deduction na hindi ko maintindihan. Sakop ba ninyo ito?',
            'Nagtatrabaho ako sa barangay at kulang ang sahod.',
            'Stay-out yaya ako ng isang family sa bahay nila. Hindi nila binibigay yung sahod ko nang buo.',
            'Nanny ako ng isang pamilya at hindi nila ako binabayaran.',
        ]:
            with self.subTest(text=text):
                packet = self.ask(text)
                self.assertEqual(packet['response']['kind'], 'referral')
                self.assertFalse(packet['response']['quotes'])
        # A product description is not an assertion of household employment.
        packet = self.ask('A retailer sold me a defective nanny camera for my family.')
        self.assertEqual(packet['result']['routing']['predicted_primary'], 'consumer')

    def test_follow_up_references_do_not_create_a_second_concern(self):
        for text in [
            'The bank has charged an annual credit-card fee after I requested cancellation. Where does that dispute fit?',
            'My securities broker refuses to release the money from an investment sale. Can you handle that complaint?',
        ]:
            with self.subTest(text=text):
                packet = self.ask(text)
                self.assertEqual(packet['response']['kind'], 'referral')
                self.assertEqual(packet['result']['routing']['predicted_scope'], 'unsupported')
        different = self.ask('My bank charged an annual credit-card fee. A retailer also refuses to replace a defective desk lamp.')
        self.assertEqual(different['result']['routing']['predicted_primary'], 'mixed')
        self.assertEqual(different['result']['routing']['predicted_scope'], 'partially_supported')
        self.assertTrue(different['result']['excluded_components'])

    def test_paid_shift_is_working_time_not_an_unknown_payment(self):
        packet = self.ask('Our private restaurant requires us to attend a briefing before the paid shift begins. Do those minutes count as working time?')
        self.assertNotEqual(packet['response']['kind'], 'clarification')
        self.assertEqual(len(packet['result']['components']), 1)
        self.assertEqual(packet['response']['kind'],'recorded_sources')
        self.assertTrue(self.headings(packet))
        self.assertTrue(all(re.search(r'hours|working time', h, re.I) for h in self.headings(packet)))
        self.assertEqual(self.ask('I paid but I have no idea what happened.')['response']['kind'], 'clarification')

    def test_taglish_purchase_and_descriptive_defect_keep_the_product_context(self):
        packet = self.ask('Bumili ako ng bagong desk lamp sa retailer. Basag pala yung switch sa loob at hindi gumagana.')
        self.assertEqual(packet['result']['routing']['predicted_primary'], 'consumer')
        self.assertNotIn('guidance_context', packet)
        self.assertTrue(packet['response']['quotes'])
        self.assertTrue(all(re.search(r'defect|imperfection|warrant', h, re.I) for h in self.headings(packet)))

    def test_extra_hours_do_not_quote_payroll_or_employment_status(self):
        packet = self.ask('I work ten hours packing orders at a private warehouse, but my payslip covers only eight. Is the extra time paid differently?')
        self.assertTrue(self.headings(packet))
        self.assertTrue(all('overtime' in h.lower() for h in self.headings(packet)))

    def test_coe_does_not_use_recruitment_advertisements(self):
        packet = self.ask('HR at my former private employer says they cannot issue a COE until next year. What information is available about release of employment certificates?')
        self.assertFalse(any(re.search(r'recruit|advert', h, re.I) for h in self.headings(packet)))
        # An explicit source limitation is preferable to an unrelated rule.
        self.assertIn(packet['response']['kind'], {'recorded_sources', 'source_limit'})

    def test_named_law_uses_that_source_identity(self):
        packet = self.ask('What is the general purpose of the Consumer Act for people buying ordinary household goods?')
        self.assertTrue(packet['response']['quotes'])
        self.assertTrue(all('Consumer Act' in self.verifier.records[q['chunk_id']]['document_title'] for q in packet['response']['quotes']))

    def test_deceptive_sales_and_price_tags_select_different_topics(self):
        deceptive = self.ask('A salesperson sold me a refurbished tablet as brand new without disclosing that it had been used.')
        prices = self.ask('Nasa shelf tag 85 pesos pero 110 yung singil sa grocery cashier para sa parehong item.')
        self.assertTrue(self.headings(deceptive))
        self.assertTrue(all(re.search(r'deceptive|unfair', h, re.I) for h in self.headings(deceptive)))
        self.assertTrue(self.headings(prices))
        self.assertTrue(all(re.search(r'price tag|price label', h, re.I) for h in self.headings(prices)))
        paraphrase = self.ask('A retailer passed off a secondhand speaker as brand new without disclosing its condition.')
        self.assertEqual(paraphrase['result']['routing']['predicted_primary'], 'consumer')
        self.assertTrue(self.headings(paraphrase))
        self.assertTrue(all(re.search(r'deceptive|unfair', h, re.I) for h in self.headings(paraphrase)))

    def test_restricted_procedures_are_not_general_complaint_steps(self):
        from dataset.pipelines.item11.query_relevance import source_relevance
        records = list(self.verifier.records.values())
        shortchange = next(r for r in records if r['provision_id'] == 'DTI_DAO_16_03__rule_vi_procedures_in_filing_a_complaint__section_1')
        termination = next(r for r in records if r['provision_id'] == 'DOLE_DO_147_15__rule_i_a__section_8')
        agency = next(r for r in records if r['provision_id'] == 'LAB_IRR_1989__rule_v_private_employment_agencies__section_18')
        self.assertEqual(source_relevance('How do I file a DTI complaint about a defective appliance?', 'consumer', shortchange), 0)
        self.assertGreater(source_relevance('How do I file a DTI shortchanging complaint about my sukli?', 'consumer', shortchange), 0)
        self.assertEqual(source_relevance('How do I begin SEnA for unpaid salary?', 'labor', termination), 0)
        self.assertGreater(source_relevance('How do I begin SEnA for my dismissal?', 'labor', termination), 0)
        self.assertEqual(source_relevance('My private employer dismissed me without notice.', 'labor', agency), 0)

    def test_mangled_record_is_held_and_excerpts_keep_qualifications(self):
        from backend.application.source_issues import issue_for
        from dataset.pipelines.item11.query_relevance import relevant_excerpt
        self.assertTrue(issue_for({'provision_id': 'LAB_IRR_1989__article_280'}))
        record = next(r for r in self.verifier.records.values() if r['provision_id'] == 'RA_7394_1992__art_68')
        quote = relevant_excerpt('The retailer repaired it twice but it still malfunctions. What refund or replacement rules concern written warranties?', 'consumer', record)
        self.assertIn(quote, record['parent_text'])
        self.assertIn('Minimum standards for warranties', quote)
        self.assertIn('unreasonable use', quote)

    def test_abroad_introduction_keeps_the_worker_category(self):
        packet = self.ask('I work abroad in Qatar and my employer withheld my wages. Which kind of concern is that?')
        self.assertEqual(packet['response']['kind'], 'referral')
        self.assertFalse(packet['response']['quotes'])
        product = self.ask('A local retailer sold me a defective kettle made in Qatar.')
        self.assertEqual(product['result']['routing']['predicted_primary'], 'consumer')

    def test_hazard_follow_up_is_not_an_extra_excluded_concern(self):
        packet = self.ask('The kettle a retailer sold us has exposed live wires at the handle. What product-safety information can I inspect?')
        self.assertEqual(packet['result']['routing']['predicted_primary'], 'consumer')
        self.assertEqual(packet['result']['routing']['predicted_scope'], 'fully_supported')
        self.assertEqual(len(packet['result']['components']), 1)
        self.assertTrue(packet['response']['quotes'])

    def test_then_introduces_a_second_concern_when_both_predicates_are_real(self):
        packet = self.ask('An online business seller delivered a defective product and then published my home address without consent.')
        self.assertEqual(packet['result']['routing']['predicted_primary'], 'mixed')
        self.assertEqual(packet['result']['routing']['predicted_scope'], 'partially_supported')
        self.assertTrue(packet['result']['excluded_components'])
        self.assertTrue(packet['response']['quotes'])
        self.assertEqual({c['allowed_domain'] for c in packet['result']['components']}, {'consumer'})

    def test_denied_utility_concern_does_not_create_a_new_component(self):
        packet = self.ask('I work for a private water utility company. My employer has not paid my overtime wages. This is about employment, not my water bill.')
        self.assertEqual(packet['result']['routing']['predicted_primary'], 'labor')
        self.assertEqual(packet['result']['routing']['predicted_scope'], 'fully_supported')
        self.assertFalse(packet['result']['excluded_components'])
        self.assertTrue(packet['response']['quotes'])
        different = self.ask('My private employer owes wages. Separately, my water utility sent me a duplicate bill.')
        self.assertEqual(different['result']['routing']['predicted_scope'], 'partially_supported')
        self.assertTrue(different['result']['excluded_components'])


if __name__ == '__main__':
    unittest.main()
