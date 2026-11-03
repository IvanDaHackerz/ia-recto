"""Source contrasts from synthetic usability failures; no provider requests."""
import json
from pathlib import Path
import unittest
from backend.application.development_explanation import response_focus
from backend.application.grounding import numeric_facts, source_qualification_failure
from dataset.pipelines.item11.query_relevance import source_relevance

ROOT=Path(__file__).resolve().parents[2]


class FreshUsabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        selected=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text(encoding='utf-8'))
        cls.records={r['provision_id']:r for r in map(json.loads,(ROOT/selected['retrieval']/'records.jsonl').read_text(encoding='utf-8').splitlines())}

    def test_night_pay_cannot_be_supported_by_an_overtime_or_transfer_rule(self):
        question='A private hotel worker asks about night differential, not extra working hours.'
        for provision in ['LAB_CODE_2022__art_87','LAB_CODE_2022__art_157']:
            self.assertEqual(source_relevance(question,'labor',self.records[provision]),0)

    def test_paid_repair_service_does_not_default_to_product_purchase_remedies(self):
        question='A paid repair service returned my fan with the original defect. Explain service quality.'
        self.assertGreater(source_relevance(question,'consumer',self.records['RA_7394_1992__art_102']),0)
        self.assertEqual(source_relevance(question,'consumer',self.records['RA_7394_1992__art_100']),0)
        parts='Repair shop gumamit ng piyesang hindi pasok sa manufacturer specs. Saan ang rule tungkol sa replacement parts?'
        self.assertGreater(source_relevance(parts,'consumer',self.records['RA_7394_1992__art_103']),0)

    def test_deductions_in_noisy_wording_select_actual_loss_deduction_rule(self):
        question='Private worker ako. knaltas sa sahod ang missing equipment. may rules bago magkaltas?'
        self.assertGreater(source_relevance(question,'labor',self.records['LAB_IRR_1989__rule_viii_payment_of_wages__section_14']),0)
        self.assertEqual(source_relevance(question,'labor',self.records['LAB_IRR_1989__rule_viii_payment_of_wages__section_3']),0)

    def test_procedural_first_is_not_a_quantity_but_a_deadline_is(self):
        self.assertEqual(numeric_facts('The employer must first give written notice.'),set())
        self.assertEqual(numeric_facts('The first day and seven days are quantities.'),{'1.0','7.0'})

    def test_online_return_condition_applies_to_named_products_too(self):
        source=self.records['RA_11967_2023__sec_20']['parent_text']
        self.assertIsNotNone(source_qualification_failure('The merchant may request return of the original headphones.',source))
        self.assertIsNone(source_qualification_failure('If the consumer chooses replacement or refund, the merchant may request return of the original headphones at no cost to the consumer.',source))
        self.assertIsNone(source_qualification_failure('When you opt for replacement or refund, the merchant may request return of the original goods at no cost to you.',source))

    def test_payroll_and_closure_do_not_expand_or_reverse_obligations(self):
        payroll=self.records['LAB_IRR_1989__rule_x_administration_and_enforcement__section_6']['parent_text']
        self.assertIsNotNone(source_qualification_failure('These fields must appear on an individual payslip.',payroll))
        self.assertIsNone(source_qualification_failure('These fields must be individually shown in payroll records.',payroll))
        closure=self.records['LAB_CODE_2022__art_298']['parent_text']
        self.assertIsNotNone(source_qualification_failure('Give advance written notice unless closure evades labor law.',closure))
        self.assertIsNone(source_qualification_failure('Closure is permitted when not intended to evade labor law; advance written notice must be given.',closure))
        self.assertIsNotNone(source_qualification_failure('Closure entitles workers to separation pay.',closure))
        self.assertIsNone(source_qualification_failure('Closure not due to serious business losses entails separation pay under the recorded conditions.',closure))

    def test_safety_defenses_keep_third_party_and_manufacturer_actors(self):
        source=self.records['RA_7394_1992__art_97']['parent_text']
        self.assertIsNotNone(source_qualification_failure('The producer is liable unless the consumer alone was at fault.',source))
        self.assertIsNotNone(source_qualification_failure('Liability does not apply unless the seller proves no defect.',source))
        self.assertIsNone(source_qualification_failure('The producer is not liable if it proves the consumer or a third party was solely at fault.',source))

    def test_regular_framework_request_is_not_narrowed_to_seasonal_keyword(self):
        focus=response_focus('Explain regular-versus-casual employment and project or seasonal exceptions.')
        self.assertIn('activity test',focus)
        self.assertIn('both project and seasonal',focus)


if __name__=='__main__':unittest.main()
