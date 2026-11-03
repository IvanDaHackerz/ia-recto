"""Synthetic counterfactuals for classifier spelling features; no API calls."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dataset/pipelines/item10"))
from typing_repair import matching_text
from clause_classifier import segment_question
from scope_constraints import constraint


class TypingFeaturesTests(unittest.TestCase):
    def test_ordinary_product_nouns_and_adverbs_survive_compressed_features(self):
        text='The printer, scanner and cooking pot worked badly beside the planter.'
        self.assertEqual(matching_text(text),text)
        self.assertEqual(matching_text('prvte emplyr sfarer wge'),'private employer seafarer wage')

    def test_ordinary_words_and_inflections_are_not_rewritten_as_scope_terms(self):
        text='What role does accounting have in charging fees? Put the proof here; nothing is proved or proven.'
        self.assertEqual(matching_text(text),text)
        self.assertEqual(matching_text('sfarer dplyment'),'seafarer deployment')

    def test_repeated_scope_and_function_words_keep_question_context(self):
        self.assertEqual(matching_text('payrollll stillll have beeeen paid for thattt day'),
                         'payroll still have been paid for that day')

    def test_unique_procedure_and_provider_spellings_use_declared_terms(self):
        self.assertEqual(matching_text('cashiir scrity tnre lettir bargaineng onit explaen raisi'),
                         'cashier security tenure letter bargaining unit explain raise')
        # These alternatives remain ambiguous outside an explicit concept.
        self.assertEqual(matching_text('prdct pnson'), 'prdct pnson')

    def test_product_label_quantity_is_supported_without_guessing_compressed_word(self):
        self.assertEqual(constraint('Klng ang actl laman ng household prdct kmpra sa net quantity sa label.')[0], 'consumer')
        self.assertEqual(constraint('A bank account has a net quantity on a label and a disputed bank fee.')[0], 'excluded')
        self.assertIsNone(constraint('What does this label mean?'))

    def test_existing_training_wordforms_are_preserved_without_evaluation_vocabulary(self):
        from typing_vocabulary import PRESERVED_WORDS, PROVENANCE
        self.assertEqual(matching_text(' '.join(sorted(PRESERVED_WORDS))), ' '.join(sorted(PRESERVED_WORDS)))
        self.assertFalse(PROVENANCE['held_out_or_evaluation_words_loaded'])
        self.assertEqual(PROVENANCE['training_parent_rows'], 459)

    def test_boundaries_preserve_actors_and_function_words(self):
        for original, expected in [
            ("minimumwage", "minimum wage"), ("wagesa", "wage sa"),
            ("employeeako", "employee ako"), ("konagovernment", "ko na government"),
            ("Prvteemployee", "private employee"), ("produccctwrrnty", "product warranty"),
            ("bnling item", "biniling item"), ("sngl sa grocery", "singil sa grocery"),
            ("shrp edgiang table", "shrp edge ang table"),
            ("homeaddress anNLRC sellller faultykeyboard", "home address an nlrc seller faulty keyboard"),
        ]:
            with self.subTest(original=original):
                self.assertEqual(matching_text(original), expected)

    def test_scope_contrasts_survive_typing_noise(self):
        for text, expected in [
            ("prvte emplyr owes shd", "labor"),
            ("gvrnment emplyr owes shd", "excluded"),
            ("shop wrrnty", "consumer"),
            ("bnk accnt chrge", "excluded"),
            ("exact mnmum wge today", "excluded"),
            ("sfarer dplyment", "excluded"),
            ("Please dlte my ID dcment from the website.", "excluded"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(constraint(text)[0], expected)

    def test_literals_names_negation_and_numbers_are_not_repaired(self):
        text = 'Si Goverment paid PHP 500 on 2026-10-19. "sngl prvte" https://example.com/prvte Not hindi wala DTI NLRC.'
        self.assertEqual(matching_text(text), text)
        self.assertEqual(matching_text("first-day rest-day rules"), "first-day rest-day rules")
        self.assertEqual(matching_text("authorized unauthorized"), "authorized unauthorized")
        for clear in ["Kailan dapat ibigay ang final pay?", "Private salon employee ako.",
                      "Is the factory compliant?", "I made a complaint.", "I need a loan."]:
            self.assertEqual(matching_text(clear), clear)
        self.assertEqual(matching_text("Pinalitan yung rest day ko."), "Pinalitan yung rest day ko.")

    def test_separate_supported_and_excluded_concerns_remain_separate(self):
        text = "Prvte emplyr owes shd. Hiwalay na cncrn ang sfarer dplyment."
        audit = segment_question(text)
        self.assertEqual(len(audit["components"]), 2)
        self.assertEqual([constraint(c)[0] for c in audit["components"]], ["labor", "excluded"])
        self.assertFalse(audit["requires_clarification"])

    def test_matching_is_idempotent(self):
        for text in ["Prvteemployee owes shd. gvrnment emplyr also owes salary.",
                     "minimumwage wagesa cety. productwrrnty and bnkaccnt."]:
            repaired = matching_text(text)
            self.assertEqual(matching_text(repaired), repaired)

    def test_privacy_deletion_does_not_exclude_product_label_correction(self):
        self.assertEqual(constraint("A retail store refused to remove the incorrect price label from my purchase.")[0], "consumer")


if __name__ == "__main__":
    unittest.main()
