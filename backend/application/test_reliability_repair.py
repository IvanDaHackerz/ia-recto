"""Source-bound regressions from the AI-on review; no provider requests."""
import json
from pathlib import Path
import unittest
import sys

from backend.application.grounding import numeric_facts, source_qualification_failure
from backend.application.development_explanation import checked_claims

ROOT=Path(__file__).resolve().parents[2]


class NumericMeaningTests(unittest.TestCase):
    def test_procedural_first_and_anaphoric_one_are_not_quantities(self):
        for text in ['First, the mediator clarifies the issues.',
                     'The mediator begins by first clarifying the issues.',
                     'Begin by first validating each position.',
                     'The appliance differs from the one ordered.',
                     'Compare the one purchased with the one delivered.']:
            with self.subTest(text=text):self.assertEqual(numeric_facts(text),set())

    def test_actual_counts_ordinals_rates_and_dates_remain_checked(self):
        for text,expected in [('one employee',{'1.0'}),('the first working day',{'1.0'}),
                              ('one percent',{'1.0'}),('one ordered unit',{'1.0'}),
                              ('the first and second days',{'1.0','2.0'}),
                              ('twenty-fifth and thirtieth of December',{'25.0','30.0'}),
                              ('the one ordered on the second day',{'2.0'})]:
            with self.subTest(text=text):self.assertEqual(numeric_facts(text),expected)


class SourceConditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows=[json.loads(s) for s in (ROOT/'outputs/item11-retrieval-v1.3.54/records.jsonl').read_text(encoding='utf-8').splitlines()]
        cls.records={r['provision_id']:r for r in rows}

    def source(self,*ids):return ' '.join(self.records[i]['parent_text'] for i in ids)

    def test_seasonal_exception_does_not_automatically_assign_regular_status(self):
        source=self.source('LAB_CODE_2022__art_295')
        for text in ['Seasonal work is regular employment only for the duration of the season.',
                     'Ang seasonal work ay regular employment lamang para sa tagal ng season.']:
            with self.subTest(text=text):self.assertIsNotNone(source_qualification_failure(text,source))
        self.assertIsNone(source_qualification_failure('Where the seasonal exception applies, the work is seasonal in nature and the employment is for the duration of the season. This description does not determine the worker’s legal status.',source))

    def test_negated_holiday_exception_does_not_require_both_negations(self):
        source=self.source('LAB_CODE_2022__art_94')
        for text in ['The worker is covered only if the establishment is not retail or service and does not have fewer than 10 workers.',
                     'Covered kung hindi retail/service at hindi mas mababa sa 10 workers.']:
            with self.subTest(text=text):self.assertIsNotNone(source_qualification_failure(text,source))
        self.assertIsNone(source_qualification_failure('The recorded regular-holiday rule excepts retail and service establishments regularly employing fewer than 10 workers. Confirm the establishment category and headcount rather than deciding coverage here.',source))

    def test_due_process_requirement_is_not_an_automatic_remedy_finding(self):
        source=self.source('LAB_CODE_2022__art_294','LAB_IRR_1989__rule_xiv_termination_of_employment__section_1')
        self.assertIsNotNone(source_qualification_failure('Dismissal needs cause and due process. If termination does not meet those conditions, the employee is unjustly dismissed and entitled to reinstatement and backwages.',source))
        self.assertIsNone(source_qualification_failure('The sources require a just or authorized cause and due process. The separate security-of-tenure provision describes reinstatement and backwages for an unjustly dismissed employee; this does not determine whether this dismissal meets that condition.',source))

    def test_unresolved_redress_is_exhaustion_not_the_only_completion(self):
        source=self.source('RA_11967_2023__sec_24')
        self.assertIsNotNone(source_qualification_failure('The platform can consider the internal process finished only if the complaint remains unresolved after seven calendar days.',source))
        self.assertIsNone(source_qualification_failure('The aggrieved party must use the internal redress mechanism first. If the complaint remains unresolved after seven calendar days from filing, the mechanism is deemed exhausted.',source))

    def test_presentment_keeps_the_product_with_the_card_or_receipt(self):
        source=self.source('RA_7394_1992__art_68')
        self.assertIsNotNone(source_qualification_failure('The buyer only needs to present the warranty card or receipt to the immediate seller.',source))
        self.assertIsNotNone(source_qualification_failure('Basta ipakita ang warranty card o resibo sa retailer.',source))
        self.assertIsNone(source_qualification_failure('The buyer presents the warranty card or receipt together with the product to the immediate seller. An ordinary retailer must forward the claim to the distributor at no cost.',source))

    def test_no_hearing_allegation_does_not_prove_the_actual_deduction_illegal(self):
        source=self.source('LAB_IRR_1989__rule_viii_payment_of_wages__section_14')
        bad='Where loss deductions are a recognized practice, the listed conditions apply. Because the employer deducted without giving a hearing, condition (b) was not satisfied, making the deduction unlawful.'
        self.assertIsNotNone(source_qualification_failure(bad,source))
        self.assertIsNone(source_qualification_failure('In a trade where deductions for employer-supplied tools or materials are a recognized practice, responsibility, a reasonable opportunity to show cause, a fair amount within actual loss and the weekly limit all matter. Whether the worker received that opportunity requires facts.',source))

    def test_law_title_must_belong_to_the_cited_authority(self):
        record=self.records['RA_10909_2016__sec_4']
        components=[{'component_id':'c1','query':'What is the cash-change rule?','sources':[record]}]
        draft={'paragraphs':[{'component_id':'c1','text':'The Consumer Act prohibits giving change in anything other than currency.',
                             'evidence':[{'chunk_id':record['chunk_id'],'quote':record['parent_text']}]}]}
        with self.assertRaisesRegex(ValueError,'authority|title'):checked_claims(draft,components)
        draft['paragraphs'][0]['text']='The No Shortchanging Act requires exact change and prohibits asking the consumer to waive its provisions.'
        self.assertEqual(len(checked_claims(draft,components)),1)

    def test_taglish_regular_summary_retains_activity_test(self):
        source=self.source('LAB_CODE_2022__art_295')
        self.assertIsNotNone(source_qualification_failure('Regular ang trabaho maliban kung may project o seasonal exception.',source))
        self.assertIsNone(source_qualification_failure('Regular ang gawaing karaniwang kinakailangan sa negosyo, maliban kung pasok sa project o seasonal exception.',source))
        self.assertIsNotNone(source_qualification_failure('The employment automatically ends at the end of the season.',source))

    def test_meal_source_does_not_supply_an_unpaid_qualifier(self):
        source='Every employer shall give time-off for regular meals. A shorter meal period is credited as compensable hours worked.'
        self.assertIsNotNone(source_qualification_failure('The employer must give unpaid time-off for meals.',source))
        self.assertIsNone(source_qualification_failure('The source requires time-off for regular meals and compensable credit for the qualifying shorter meal period.',source))

    def test_general_warranty_rule_does_not_adjudicate_a_promotion_clause(self):
        source=self.source('RA_7394_1992__art_68')
        self.assertIsNotNone(source_qualification_failure('Any clause that denies a warranty because of a promotion is void.',source))
        self.assertIsNone(source_qualification_failure('The recorded rule declares stipulations contrary to the article’s provisions null and void, without deciding the particular promotion terms.',source))


class FragmentAndRelevanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
        sys.path.insert(0,str(ROOT/'dataset/pipelines/item11'))

    def test_same_scenario_meal_and_online_return_followups_stay_together(self):
        from clause_classifier import segment_question
        for text in [
            'A private assembly plant gives only twenty minutes for lunch while the machines keep running. What sources or limitations apply to a general meal-period question?',
            'A private factory gives us twenty minutes for regular meals. Which meal-break conditions apply?',
            'A Philippine online merchant admits it sent the wrong shoe size. Explain the recorded remedy and distinguish a return obligation after choosing replacement or refund from merely reporting the problem.',
            'The online shop sent the wrong bag model. What are the return conditions after choosing replacement or refund?']:
            with self.subTest(text=text):
                a=segment_question(text)
                self.assertEqual(len(a['components']),1)
                self.assertTrue(a['all_fragments_accounted_for'])

    def test_a_new_employer_or_excluded_subject_is_not_absorbed(self):
        from clause_classifier import segment_question
        for text in [
            'The online shop sent the wrong bag model. Separately, my employer withheld wages.',
            'A private factory gives us twenty minutes for lunch. Separately, my bank charged a dormancy fee.']:
            with self.subTest(text=text):self.assertEqual(len(segment_question(text)['components']),2)

    def test_meal_and_counted_time_do_not_match_bank_payment_or_normal_ceiling(self):
        from query_relevance import source_relevance
        bank={'heading':'Payment of Wages','document_title':'Labor Code rules','parent_text':'Private establishments shall pay wages through banks upon written petition of workers.','conditions':[]}
        ceiling={'heading':'Normal Hours of Work','document_title':'Labor Code','parent_text':'The normal hours of work shall not exceed eight hours a day.','conditions':[]}
        meal={'heading':'Meal and Rest Periods','document_title':'DOLE handbook','parent_text':'Every employer shall give time off for regular meals subject to the recorded exceptions.','conditions':[]}
        query='Private plant gives twenty minutes for lunch. What meal-period conditions apply?'
        self.assertEqual(source_relevance(query,'labor',bank),0)
        self.assertGreater(source_relevance(query,'labor',meal),0)
        self.assertEqual(source_relevance('Does my required pre-shift briefing before clock-in count as hours worked?','labor',ceiling),0)

    def test_new_source_view_keeps_scan_and_suspect_modifier_holds(self):
        from common import sources,curate
        source=sources();records,_=curate(source)
        ids={r['provision_id'] for r in records}
        self.assertIn('LAB_CODE_2022__art_84',ids)
        self.assertIn('LAB_CODE_2022__art_85',ids)
        self.assertIn('LAB_CODE_2022__art_86',ids)
        self.assertIn('LAB_IRR_1989__rule_i_hours_of_work__section_7',ids)
        self.assertIn('SC_110068_1993_STATUTORY_QUOTES__recorded_rule',ids)
        self.assertIn('DOLE_FINAL_PAY_COE_NEWS_2026__recorded_rule',ids)
        self.assertFalse(any(r['document_id'] in {'DOLE_LA_06_20','MO_28_1986','RA_10151_2011'} for r in records))
        self.assertFalse(any(r['document_id']=='DOLE_BWC_HANDBOOK_2024' for r in records))
        self.assertEqual(source['documents']['DOLE_BWC_HANDBOOK_2024']['retrieval_use_policy'],'explanatory_only')

    def test_scope_meta_is_removed_only_from_prompt_copy(self):
        from backend.application.development_explanation import source_question
        original='An online store sent a faulty rice cooker. Please explain the purchase issue and tell me where your scope ends.'
        self.assertEqual(source_question(original),'An online store sent a faulty rice cooker.')
        self.assertIn('scope ends',original)
        self.assertEqual(source_question('What is the scope of the written warranty?'),'What is the scope of the written warranty?')
        raw='Explain only these supported concerns:\nAn employer withheld wages.'
        self.assertEqual(source_question(raw),raw)

    def test_held_related_candidate_cannot_block_or_authorize_independent_evidence(self):
        from unittest.mock import Mock
        from backend.application.development_explanation import explain_recorded_sources
        verifier,provider=Mock(),Mock();verifier.check_candidate.return_value=[]
        provider.name='test';provider.model='mock'
        good={'chunk_id':'good','provision_id':'p','document_id':'d','citation_display':'Recorded excerpt',
              'parent_text':'The normal hours of work shall not exceed eight hours per day.',
              'heading':'Normal Hours of Work','conditions':[]}
        held={**good,'chunk_id':'held'}
        pre={'question_text':'What are normal hours of work?','routing':{'routing_action':'retrieve_supported_evidence'},
             'components':[{'component_id':'c1','query':'normal hours of work','allowed_domain':'labor','candidates':[held,good],
                            'evidence_gates':[{'chunk_id':'held','reasons':['related_authority_unavailable:missing']},
                                              {'chunk_id':'good','reasons':['scoped_currentness_review_missing']}]}]}
        provider.complete.return_value={'paragraphs':[{'component_id':'c1','text':'The recorded rule limits normal daily work hours.',
                                                       'evidence':[{'chunk_id':'good','quote':good['parent_text']}]}]}
        provider.assess.return_value={'assessments':[{'claim_id':'development_1','verdict':'supported','qualifications_preserved':True,
                                                   'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True}]}
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated')
        sent=provider.complete.call_args.args[1]['components'][0]['sources']
        self.assertEqual([s['chunk_id'] for s in sent],['good'])
        self.assertFalse(result['legal_support_verified'])


if __name__=='__main__':unittest.main()
