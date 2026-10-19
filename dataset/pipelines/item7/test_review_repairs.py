"""Consequential section/cross-reference distinction in scanned DTI procedures."""
import unittest
from prepare_review_repairs import dti_sections
class StructureTests(unittest.TestCase):
    def test_cross_references_do_not_split_sections_or_replace_rule(self):
        text='RULE IV\nADJUDICATION\nSection 1. Formal Complaint.\nUse\nSection 2 of Rule IV for venue and\nRule 3 hereof and the same was certified for adjudication.\nSection 2. Venue.\nA formal complaint is filed here.'
        result=dti_sections([{'text':text,'pdf_page':1}])
        self.assertEqual([(r['rule'],r['section']) for r in result],[('IV',1),('IV',2)])
        self.assertIn('Section 2 of Rule IV',result[0]['candidate_text'])
        self.assertIn('Rule 3 hereof',result[0]['candidate_text'])
    def test_ocr_roman_glyph_does_not_change_known_rule_heading(self):
        result=dti_sections([{'text':'RULE Ill\nMEDIATION\nSection 1. Mandatory Mediation.\nMediation is mandatory.','pdf_page':3}])
        self.assertEqual(result[0]['rule'],'III');self.assertFalse(result[0]['answer_eligible'])
    def test_page_continuation_is_retained(self):
        result=dti_sections([{'text':'RULE II\nINITIAL COMPLAINTS\nSection 2. Where Filed.\nThe complaint is','pdf_page':2},
                              {'text':'filed with the appropriate office.\nSection 3. Referral.\nMore legal text.','pdf_page':3}])
        self.assertIn('filed with the appropriate office',result[0]['candidate_text'])
        self.assertEqual((result[0]['pdf_page_start'],result[0]['pdf_page_end']),(2,3))
if __name__=='__main__':unittest.main()
