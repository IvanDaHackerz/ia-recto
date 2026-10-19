"""Contrastive scope development regressions; no fitting or provider calls."""
from pathlib import Path
import unittest
import joblib
from classifier_runtime import predict_records

class ConcernRepairTests(unittest.TestCase):
    RUN=None
    @classmethod
    def setUpClass(cls): cls.bundle=joblib.load(cls.RUN/'classifier.joblib')

    def check(self,text,primary,scope='fully_supported'):
        p=predict_records(self.bundle,[{'question_text':text}])[0]
        self.assertEqual((p['predicted_primary'],p['predicted_scope']),(primary,scope))
        self.assertNotEqual(p['routing_action'],'clarify')

    def test_incidental_general_words_do_not_override_real_complaints(self):
        cases=[('Because of the weather, my private company has not paid my salary for two months.','labor'),
            ('The shop sold me a defective weather radio and refuses to refund it.','consumer'),
            ('The shop refuses to refund a defective algebra textbook.','consumer'),
            ('The store sold me a damaged recipe book and refuses to replace it.','consumer'),
            ('My private restaurant employer deducts wages if I forget a recipe.','labor'),
            ('Private company ko, di pa binabayaran overtime ko dahil sa weather.','labor'),
            ('The shop sold me a defective football game console and refuses a refund.','consumer')]
        for text,primary in cases:
            with self.subTest(text=text): self.check(text,primary)

    def test_actual_general_requests_remain_excluded(self):
        for text in ['What is the weather tomorrow?','Give me a recipe for adobo.','Help me solve algebra homework.','What is the basketball game score?']:
            with self.subTest(text=text): self.check(text,'out_of_scope','unsupported')

    def test_negated_category_is_not_an_excluded_concern(self):
        self.check('The shop refuses to refund my defective laptop. This is not an insurance claim.','consumer')

    def test_historical_fact_does_not_inflate_current_concern(self):
        self.check('I was stabbed ten years ago. My private company now refuses to pay overtime.','labor')

    def test_actual_joined_concerns_remain_partial(self):
        self.check('My private employer has not paid my salary, and I need an annulment.','mixed','partially_supported')
        self.check('Someone stole my phone, and the store sold me a faulty replacement.','mixed','partially_supported')

    def test_quoted_demonstration_is_not_personal_harm(self):
        self.check('In our training example the phrase was "I was stabbed". My private employer has not paid my overtime.','labor')

    def test_rule_follow_up_keeps_its_existing_scenario(self):
        from clause_classifier import segment_question
        text='A private-sector employer refuses to pay a worker for Christmas Day because the office was closed and no work was performed. What holiday-pay rules and exceptions apply?'
        audit=segment_question(text)
        self.assertEqual(len(audit['components']),1)
        self.assertEqual(audit['fragments'][-1]['role'],'follow_up')
        self.assertIn('christmas day',audit['components'][0])
        self.assertIn('holiday-pay rules and exceptions apply',audit['components'][0])
        self.assertTrue(audit['all_fragments_accounted_for'])
        self.check(text,'labor')

    def test_rule_follow_up_does_not_absorb_new_topics_or_facts(self):
        from clause_classifier import segment_question
        for follow in ['What overtime-pay rules and exceptions apply?', 'What divorce rules apply?',
                       'My government employer also withheld my holiday pay.',
                       'What holiday-pay rules apply to government workers?']:
            with self.subTest(follow=follow):
                audit=segment_question('My private employer withheld my Christmas holiday pay. '+follow)
                self.assertGreaterEqual(len(audit['components']),2)
