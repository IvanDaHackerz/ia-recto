"""Ensure incomplete contact evidence never exposes old unverified fields."""
import json,unittest
from pathlib import Path
from referral_lookup import lookup
ROOT=Path(__file__).resolve().parents[3]
DIRECTORY=ROOT/'dataset/processed/item10/referral_refresh_v1.0.0/directory.json'
class ContactTests(unittest.TestCase):
    def test_all_original_referral_ids_are_retained(self):
        import csv
        with (ROOT/'dataset/processed/item10/reviewed_v1.0.0/referral_directory.csv').open(encoding='utf-8-sig') as f:
            expected={r['referral_id'] for r in csv.DictReader(f)}
        self.assertEqual({r['referral_id'] for r in json.loads(DIRECTORY.read_text(encoding='utf-8'))},expected)
    def test_masked_email_does_not_become_verified_email(self):
        r=lookup(DIRECTORY,'REF_PAO')
        self.assertNotIn('email',r['contact']);self.assertIn('email',r['unverified_fields_withheld'])
    def test_housing_agency_feedback_email_is_not_exposed_as_case_filing(self):
        r=lookup(DIRECTORY,'REF_HSAC_DHSUD')
        self.assertEqual(r['contact'],{});self.assertFalse(r['contact_verification_complete'])
    def test_portal_and_phone_have_field_specific_evidence(self):
        for row in json.loads(DIRECTORY.read_text(encoding='utf-8')):
            self.assertEqual(set(row['confirmed_fields']),set(row['field_verification']))
            self.assertTrue(all(e['evidence_url'].startswith('https://') for e in row['field_verification'].values()))
    def test_emergency_hotline_qualification_and_no_deployment(self):
        r=lookup(DIRECTORY,'REF_DMW')
        self.assertIn('emergency',r['note']);self.assertFalse(r['deployment_allowed'])
if __name__=='__main__':unittest.main()
