"""Provenance validation tests; fixtures are software inputs, never gold data."""
import unittest
from validate_independent_gold import validate
class GoldTests(unittest.TestCase):
    def fixture(self):
        return {'question_id':'SOFTWARE_FIXTURE','question_text':'A software fixture about an ordinary store warranty.',
            'scenario_family_id':'fixture','language_style':'en','primary_label':'consumer','scope_label':'fully_supported',
            'origin':'independent_human_written','author_id':'fixture','annotator_id':'fixture',
            'written_at':'2026-10-17','annotated_at':'2026-10-17','ai_assisted_writing':False,
            'used_for_tuning':False,'derived_from_question_id':None}
    def issues(self,row,known=()):return [e['issue'] for e in validate([row],known)['errors']]
    def test_blank_form_is_not_valid_gold(self):
        self.assertFalse(validate([{'question_id':'BLANK'}])['passed'])
    def test_ai_writing_cannot_be_accepted_as_independent_human_writing(self):
        r=self.fixture();r['ai_assisted_writing']=True
        self.assertIn('AI writing must not be labeled independent human writing',self.issues(r))
    def test_existing_question_overlap_is_rejected_despite_claimed_human_origin(self):
        r=self.fixture()
        self.assertIn('Exact normalized overlap with an existing project question',self.issues(r,[r['question_text'].upper()]))
    def test_inspected_derivative_and_tuning_rows_are_rejected(self):
        r=self.fixture();r['derived_from_question_id']='EVAL_001';r['used_for_tuning']=True
        issues=self.issues(r)
        self.assertIn('An existing development example cannot become a fresh holdout',issues)
        self.assertIn('Previously used tuning data cannot become a fresh holdout',issues)
    def test_missing_annotation_and_invalid_pair_are_rejected(self):
        r=self.fixture();r['annotator_id']=None;r['scope_label']='unsupported'
        self.assertIn('Author and annotator IDs are required',self.issues(r))
        self.assertIn('Missing or inconsistent human labels',self.issues(r))
if __name__=='__main__':unittest.main()
