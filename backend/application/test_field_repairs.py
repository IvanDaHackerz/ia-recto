"""Contrastive website failure regressions. Local-only, no provider requests."""
import re
import unittest
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime


class FieldRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier=load_runtime()
        cls.service=ApplicationService(verifier=cls.verifier,normalizer=ConditionalNormalizer())

    def ask(self,text):
        p=self.service.chat({'question_text':text,'use_ai':False})
        self.assertFalse(p['response']['ai_generated'])
        self.assertEqual(p['explanation']['llm_calls'],0)
        for q in p['response']['quotes']:
            self.assertIn(q['quote'],self.verifier.records[q['chunk_id']]['parent_text'])
        return p

    def test_stress_role_boundaries_reach_application_without_ai(self):
        for text,domain in [
            ('Cashier ako sa supermarket. May salary deduction kami pag kulang ang kaha.','labor'),
            ('The private company that sold me a refrigerator refuses a refund for a defective unit.','consumer'),
            ('I work for a private telecom company. My question is about unpaid overtime, not my phone bill.','labor'),
            ('On my rest day I bought a faulty kettle from a private shop.','consumer')]:
            with self.subTest(text=text):
                p=self.ask(text)
                self.assertEqual(p['result']['routing']['predicted_primary'],domain)
                self.assertNotEqual(p['response']['kind'],'clarification')

    def test_stress_exclusions_are_preserved_next_to_supported_concerns(self):
        p=self.ask('The store sold me a defective phone; the mobile network also charged an unauthorized data-plan fee.')
        self.assertEqual(p['result']['routing']['predicted_primary'],'mixed')
        self.assertEqual(p['result']['routing']['predicted_scope'],'partially_supported')
        self.assertTrue(p['result']['excluded_components'])
        self.assertEqual({c['allowed_domain'] for c in p['result']['components']},{'consumer'})
        for text in ['Yaya ako ng bata sa bahay ng isang pamilya, walang day off na binibigay.',
                     'What is the exact minimum-wage rate in my city today?']:
            with self.subTest(text=text):self.assertEqual(self.ask(text)['response']['kind'],'referral')

    def test_stress_vague_prompts_do_not_receive_source_passages(self):
        for text in ['I paid but nothing happened.','Hindi ko alam paano ito ayusin.',
                     'Can I ask about something that happened yesterday?']:
            with self.subTest(text=text):
                p=self.ask(text)
                self.assertEqual(p['response']['kind'],'clarification')
                self.assertFalse(p['response']['quotes'])

    def test_stress_search_understands_native_faults_and_safety_words(self):
        for text in ['The shop sold me a supposedly new laptop with a cracked screen inside the sealed box.',
                     'Yung bagong electric fan galing sa appliance shop amoy sunog agad nung sinaksak.',
                     'Bumili ako ng bagong plantsa sa appliance store, pero di umiinit. Anong consumer concern ito?',
                     'The hardware store sold an electric kettle with a loose exposed wire near the handle.',
                     'A toy from a retailer overheats and the casing becomes dangerously hot.']:
            with self.subTest(text=text):
                p=self.ask(text)
                self.assertEqual(p['result']['routing']['predicted_primary'],'consumer')
                self.assertTrue(p['response']['quotes'])

    def test_holiday_pay_anaphora_is_one_concern_without_school_passages(self):
        p=self.ask('Our private office closed for a regular holiday, but payroll marked it unpaid. Should I still have been paid for that day?')
        self.assertEqual(len(p['result']['components']),1)
        self.assertTrue(p['response']['quotes'])
        for q in p['response']['quotes']:
            self.assertRegex(self.verifier.records[q['chunk_id']]['heading'],r'(?i)holiday')
            self.assertNotRegex(q['quote'],r'(?i)tuition|educational institution')
        noisy=self.ask('Our private office closed for a regggular holiday, but payrollll marked it unpaid. Should I stillll have beeeen paid for thattt day?')
        self.assertEqual(len(noisy['result']['components']),1)
        self.assertNotEqual(noisy['result']['routing']['routing_action'],'clarify')
        self.assertTrue(noisy['response']['quotes'])
        for q in noisy['response']['quotes']:
            self.assertRegex(self.verifier.records[q['chunk_id']]['heading'],r'(?i)holiday')

    def test_offline_defects_and_shelf_prices_do_not_quote_online_or_advertising_rules(self):
        p=self.ask('My private company keeps delaying salary. Separately, a retailer delivered a washing machine that leaks immediately.')
        self.assertTrue(p['response']['quotes'])
        for q in p['response']['quotes']:
            self.assertNotRegex(q['quote'],r'(?i)online consumers|online merchant')
        p=self.ask('The grocery charged me 180 even though the shelf price for the same item was 150.')
        self.assertTrue(p['response']['quotes'])
        for q in p['response']['quotes']:
            self.assertRegex(self.verifier.records[q['chunk_id']]['heading'],r'(?i)price tag|price label')
        p=self.ask('The shop hid a nonoptional service fee until checkout.')
        self.assertTrue(p['response']['quotes'])
        for q in p['response']['quotes']:
            self.assertRegex(self.verifier.records[q['chunk_id']]['heading'],r'(?i)deceptive|unfair|unconscionable')

    def test_valid_unseen_words_are_not_rewritten_into_scope_words(self):
        from typing_repair import matching_text
        for word in ['kind','hiring','firing','hiding','liking','dining','lining','caring','bearing','funding','checking']:
            with self.subTest(word=word):self.assertEqual(matching_text(word),word)

    def test_consumer_payment_does_not_create_employment(self):
        p=self.ask('My refrigerator has a written warranty, but the seller says I must pay for every repair. What warranty rules can I read?')
        self.assertEqual(p['result']['routing']['predicted_primary'],'consumer')
        self.assertNotIn('guidance_context',p)
        self.assertEqual({c['allowed_domain'] for c in p['result']['components']},{'consumer'})
        self.assertTrue(p['response']['quotes'])
        self.assertTrue(all('warrant' in self.verifier.records[q['chunk_id']]['heading'].lower() for q in p['response']['quotes']))

    def test_employer_industry_and_actual_service_claim_are_distinct(self):
        wage=self.ask('I am employed by a private insurance firm and HR has not paid my wages. This is about my job, not a policy claim.')
        claim=self.ask('My insurance company denied my policy claim.')
        both=self.ask('My private employer owes wages. Separately, my insurance company denied my policy claim.')
        self.assertEqual(wage['result']['routing']['predicted_primary'],'labor')
        self.assertEqual(claim['response']['kind'],'referral')
        self.assertEqual(both['result']['routing']['predicted_scope'],'partially_supported')
        self.assertTrue(both['result']['excluded_components'])

    def test_natural_specialized_employment_is_excluded_without_product_false_positive(self):
        for text in ['My employer in Kuwait is holding my wages.',
                     'Live-in helper ako sa bahay ng pamilya at hindi na ako binibigyan ng rest day.']:
            with self.subTest(text=text):self.assertEqual(self.ask(text)['response']['kind'],'referral')
        self.assertEqual(self.ask('The shop sold me a defective product made in Japan.')['result']['routing']['predicted_primary'],'consumer')

    def test_disciplinary_charge_is_not_a_missing_payment_context(self):
        p=self.ask('My manager removed me from the staff roster without any written charge or chance to reply. What dismissal process should I understand?')
        self.assertNotEqual(p['result']['routing']['routing_action'],'clarify')
        self.assertEqual(p['result']['routing']['predicted_primary'],'labor')
        self.assertEqual(self.ask('They charged me too much.')['response']['kind'],'clarification')

    def test_follow_up_is_attached_but_new_concern_is_retained(self):
        from clause_classifier import segment_question
        same=segment_question('The firm keeps hiring us on short project contracts although we do the same daily office duties. How is employment status generally explained?')
        different=segment_question('My employer withheld my wages. What divorce rules apply?')
        self.assertEqual(len(same['components']),1)
        self.assertEqual(same['fragments'][-1]['role'],'follow_up')
        self.assertEqual(len(different['components']),2)

    def test_incidental_bank_check_word_does_not_select_payment_by_check(self):
        p=self.ask('The supervisor requires a twenty-minute equipment check before we clock in at the workshop. Is that part of working time?')
        headings=[self.verifier.records[q['chunk_id']]['heading'] for q in p['response']['quotes']]
        self.assertEqual(p['response']['kind'],'recorded_sources')
        self.assertTrue(headings)
        self.assertTrue(all(re.search(r'hours|working time',h,re.I) for h in headings))
        self.assertFalse(any('payment by check' in h.lower() for h in headings))

    def test_defect_and_service_questions_do_not_quote_effectivity_or_advertising_exemptions(self):
        for text,pattern in [('Kakabili lang ng speaker sa tindahan pero basag pala yung charging port. Ano consumer concern ito?',r'defect|imperfection|warrant'),
                             ('A paid laundry service shrank our clothes and refuses to acknowledge the damage. What consumer service rules cover it?',r'service|imperfection')]:
            with self.subTest(text=text):
                p=self.ask(text)
                headings=[self.verifier.records[q['chunk_id']]['heading'] for q in p['response']['quotes']]
                self.assertTrue(headings)
                self.assertTrue(all(re.search(pattern,h,re.I) for h in headings))
                self.assertFalse(any(re.search(r'effectivity|exemption',h,re.I) for h in headings))

    def test_irrelevant_stored_identity_does_not_make_a_passage_quotable(self):
        from retrieval import relevant_excerpt
        hit=next(r for r in self.verifier.records.values() if r['provision_id']=='LAB_CODE_2022__art_83')
        self.assertEqual(relevant_excerpt('A store refuses the written warranty on my refrigerator.','consumer',hit),'')

    def test_dismissal_does_not_quote_employee_resignation(self):
        p=self.ask('My manager removed me from the staff roster without any written charge or chance to reply. What dismissal process should I understand?')
        self.assertTrue(p['response']['quotes'])
        self.assertTrue(all('by employee' not in self.verifier.records[q['chunk_id']]['heading'].lower() for q in p['response']['quotes']))

    def test_work_history_is_not_an_independent_termination_claim(self):
        p=self.ask('Five months lang ako sa company bago nagresign. May explanation ba kayo tungkol sa prorated 13th month?')
        self.assertEqual(len(p['result']['components']),1)
        for q in p['response']['quotes']:
            title=self.verifier.records[q['chunk_id']]['document_title']
            self.assertRegex(title,r'(?i)13th|thirteenth')

    def test_product_hazard_is_not_invented_as_an_excluded_concern(self):
        p=self.ask('My new extension cord has exposed live wiring. What product safety rules concern unsafe goods?')
        self.assertEqual(p['result']['routing']['predicted_primary'],'consumer')
        self.assertEqual(p['result']['routing']['predicted_scope'],'fully_supported')
        self.assertFalse(p['result']['excluded_components'])

    def test_holiday_rule_follow_up_is_not_an_independent_fee_question(self):
        p=self.ask('Our private shop stayed open on a regular holiday. What general pay rules cover the staff who worked?')
        self.assertEqual(len(p['result']['components']),1)
        self.assertTrue(p['response']['quotes'])
        for q in p['response']['quotes']:
            self.assertRegex(self.verifier.records[q['chunk_id']]['heading'],r'(?i)holiday')

    def test_generic_working_time_does_not_use_hospital_only_applicability(self):
        p=self.ask('Our company requires a work briefing before clock-in each morning. Are those hours included as working time?')
        self.assertEqual(len(p['result']['components']),1)
        self.assertEqual(p['response']['kind'],'recorded_sources')
        self.assertTrue(p['response']['quotes'])
        self.assertFalse(any(re.search(r'hospital.and.clinic.personnel',q['quote'],re.I) for q in p['response']['quotes']))
        for q in p['response']['quotes']:
            record=self.verifier.records[q['chunk_id']]
            self.assertFalse(any('All hospitals and clinics' in c for c in record['conditions']))

    def test_paid_repair_service_prefers_service_quality_and_passages_do_not_repeat(self):
        for text in ['A paid repair service damaged my cabinet instead of fixing it. What service quality rules cover this?',
                     'My employer is a private bank and it has not paid my wages. What wage-payment rules are available?']:
            with self.subTest(text=text):
                p=self.ask(text);quotes=p['response']['quotes']
                self.assertTrue(quotes)
                self.assertEqual(len({q['quote'] for q in quotes}),len(quotes))
                if 'service' in text:
                    self.assertTrue(all('service quality' in self.verifier.records[q['chunk_id']]['heading'].lower() for q in quotes))

    def test_same_word_in_a_follow_up_cannot_swallow_a_new_scope_exclusion(self):
        p=self.ask('I am a private factory employee with unpaid wages. Where can I get help, and what is the exact minimum wage in my town today?')
        self.assertEqual(p['result']['routing']['predicted_primary'],'mixed')
        self.assertEqual(p['result']['routing']['predicted_scope'],'partially_supported')
        self.assertTrue(p['result']['excluded_components'])
        self.assertTrue(p['result']['components'])

    def test_actual_excluded_requests_are_not_discarded_as_actor_introductions(self):
        for text in ['Seafarer ako at hindi tugma ang sea-service record na ibinigay ng shipping company. Paano ko ipapa-correct ang maritime record?',
                     'Sfarer ako at hindi tgma ang sea-service record na ibinigay ng shipping cmpny. Pno ko ipapa-crrct ang maritime record?',
                     'Mncipal employee ako at gusto kong malaman kung mnnalo ang administrative appeal ko. Pwde mo bang i-prdct ang rslt?',
                     'Municipal employee ako at gusto kong malaman kung mananalo ang administrative appeal ko.',
                     'An investment adviser got me to put money in a fund, but now I cannot withdraw it. How do I raise a securities complaint?']:
            with self.subTest(text=text):self.assertEqual(self.ask(text)['response']['kind'],'referral')


if __name__=='__main__':unittest.main()
