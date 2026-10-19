"""Source-review artifact invariants; not independent legal verification."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
REVIEW=ROOT/'dataset/processed/item7/ai_visual_review_dti_v1.0.0'
class VisualReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[json.loads(l) for l in (REVIEW/'provisions.jsonl').read_text(encoding='utf-8').splitlines()]
        cls.by_key={(r['rule'],r['section']):r for r in cls.rows}
    def test_rules_sections_are_complete_unique_and_correctly_grouped(self):
        expected={(rule,n) for rule,count in [('I',3),('II',4),('III',6),('IV',13),('V',3)] for n in range(1,count+1)}
        self.assertEqual(set(self.by_key),expected);self.assertEqual(len(self.rows),29)
    def test_critical_omitted_text_is_present_in_correct_section(self):
        self.assertIn('Section 3, Rule III hereof.',self.by_key['II',3]['normalized_text'])
        self.assertIn('non-extendable period of ten (10) working days',self.by_key['IV',9]['normalized_text'])
        self.assertIn('g. Reply;',self.by_key['IV',11]['normalized_text'])
    def test_visual_comparison_is_not_claimed_as_human_approval(self):
        for r in self.rows:
            self.assertFalse(r['answer_eligible']);self.assertFalse(r['independent_human_review'])
            self.assertTrue(r['human_review_required']);self.assertEqual(r['review_actor'],'Codex')
    def test_original_pdf_and_all_retained_page_images_match_hashes(self):
        pdf=ROOT/'dataset/canonical_sources/raw/consumer/regulations/dao_20_02_mediation_adjudication.pdf'
        pdf_hash=hashlib.sha256(pdf.read_bytes()).hexdigest()
        for r in self.rows:
            self.assertEqual(r['official_pdf_sha256'],pdf_hash)
            for name,expected in r['page_image_sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected)
if __name__=='__main__':unittest.main()
