"""Reproduced website routing/fragment failures; no provider requests."""
import unittest
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime


class RoutingFragmentRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service=ApplicationService(verifier=load_runtime(),normalizer=ConditionalNormalizer())

    def ask(self,text):
        p=self.service.chat({'question_text':text,'use_ai':False})
        self.assertEqual(p['original_question_text'],text)
        self.assertEqual(p['explanation']['llm_calls'],0)
        self.assertFalse(p['response']['ai_generated'])
        self.assertFalse(p['result']['answer_generation_allowed'])
        return p

    def test_three_valid_questions_reach_one_correct_domain_component(self):
        for text,domain in [
            ('Probationary ako sa private office. Ngayong patapos na saka lang nila sinabi yung standards na kailangan ma-meet. How does the rule handle that?','labor'),
            ('I bought a new desk fan from an appliance shop. It worked once and then stopped. The shop says it will only repair it and will never consider replacement or refund. What does the rule actually allow?','consumer'),
            ('Sabi ng gadget store brand new yung phone, pero refurbished pala. What does the Consumer Act say about selling something used as new?','consumer')]:
            with self.subTest(text=text):
                p=self.ask(text);r=p['result']
                self.assertEqual(r['routing']['predicted_primary'],domain)
                self.assertEqual(r['routing']['routing_action'],'retrieve_supported_evidence')
                self.assertEqual(len(r['components']),1)
                self.assertEqual(r['components'][0]['allowed_domain'],domain)
                self.assertTrue(r['components'][0]['candidates'])

    def test_background_and_rule_followups_do_not_make_empty_extra_retrievals(self):
        for text in [
            'sa private printing company kami. isang beses lang kada month nagbibigay sahod. tama ba yung pagitan ng payday namin?',
            'A private office closed for a regular holiday. The staff were told that no work means no pay. Is that the general rule?',
            'may warranty card ako sa bagong microwave. ayaw tanggapin ng retailer yung complaint ko, sa supplier daw ako dumiretso. ano responsibility ng retailer?']:
            with self.subTest(text=text):
                p=self.ask(text)
                self.assertEqual(len(p['result']['components']),1)
                self.assertTrue(p['result']['components'][0]['candidates'])

    def test_scope_request_does_not_create_an_extra_consumer_search_or_erase_privacy(self):
        p=self.ask('An online store sent a faulty rice cooker. Separately, a neighbor published my personal information. Please explain the purchase issue and tell me where your scope ends.')
        r=p['result']
        self.assertEqual(r['routing']['predicted_scope'],'partially_supported')
        self.assertEqual(len(r['components']),1)
        self.assertEqual(r['components'][0]['allowed_domain'],'consumer')
        self.assertEqual(len(r['excluded_components']),1)
        self.assertIn('personal information',r['excluded_components'][0]['text'])

    def test_excluded_jobs_and_missing_relationships_are_not_admitted(self):
        for text in [
            'Probationary ako sa government office. Saka lang nila sinabi ang standards. What civil-service procedure applies?',
            'Seafarer ako. My question is about the employment terms for my overseas vessel assignment.']:
            with self.subTest(text=text):
                p=self.ask(text)
                self.assertEqual(p['result']['routing']['routing_action'],'refer_out_of_scope')
                self.assertFalse(p['result']['components'])
                self.assertFalse(p['response']['quotes'])
        for text in ['Sa private printing company kami.','They did not follow the standards. What can I do?']:
            with self.subTest(text=text):
                p=self.ask(text)
                self.assertEqual(p['result']['routing']['routing_action'],'clarify')


if __name__=='__main__':unittest.main()
