"""Concern regressions and citation-bound development generation; no paid calls."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
from backend.terminal_test import ROOT, load_runtime
from backend.normalization import ConditionalNormalizer
from backend.application.service import ApplicationService
from backend.application.development_explanation import checked_claims, explain_recorded_sources
from backend.application.safety import safety_notice


class ConcernTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = load_runtime()

    def test_all_frozen_random_background_and_supported_concerns(self):
        from backend.classifier.service import ClassifierService
        service = ClassifierService()
        rows = [json.loads(x) for x in (ROOT / 'outputs/website-explanations-v1.0.0/concern_cases.jsonl').read_text(encoding='utf-8').splitlines()]
        for case in rows:
            with self.subTest(case=case['case_id']):
                r = service.classify({'question_text': case['question_text']})
                # Preserve the frozen historical file; salary clarification
                # predates the new general-information routing policy.
                expected='retrieve_supported_evidence' if case['case_id']=='CONCERN_026' else case['expected_route']
                self.assertEqual(r['routing']['action'], expected)
                if case['expected_primary']:
                    self.assertEqual(r['classification']['primary_label'], case['expected_primary'])

    def test_reported_harm_never_reaches_either_provider(self):
        wording, explanation = Mock(), Mock()
        service = ApplicationService(verifier=self.verifier, normalizer=ConditionalNormalizer(wording), development_provider=explanation)
        p = service.chat({'question_text': 'I was about to get my pay, but i got stabbed in the street.'})
        self.assertEqual(p['result']['routing']['predicted_primary'], 'out_of_scope')
        self.assertEqual(p['result']['routing']['routing_action'], 'refer_out_of_scope')
        self.assertEqual(p['result']['components'], [])
        self.assertEqual(p['safety_notice']['emergency_number'], '911')
        self.assertEqual(p['explanation']['llm_calls'], 0)
        wording.complete.assert_not_called(); explanation.complete.assert_not_called()

    def test_safety_notice_does_not_turn_negation_or_a_termination_report_into_harm(self):
        for text in ['I was not stabbed.', 'My private employer fired me after I reported an assault.', 'My private employer did not pay overtime.']:
            self.assertIsNone(safety_notice(text))

    def test_real_supported_sources_generate_without_invented_legal_approval(self):
        provider = Mock(); provider.name, provider.model = 'test', 'mock'
        def complete(question, pre):
            return {'paragraphs': [{'component_id': c['component_id'], 'text': 'The recorded source describes this rule; its application needs the relevant facts.',
                'evidence': [{'chunk_id': c['sources'][0]['chunk_id'], 'quote': c['sources'][0]['parent_text'][:120]}]} for c in pre['components']]}
        provider.complete.side_effect = complete
        provider.assess.side_effect = lambda question,claims,components: {'assessments':[{'claim_id':c['claim_id'],'verdict':'supported','qualifications_preserved':True,'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True} for c in claims]}
        service = ApplicationService(verifier=self.verifier, normalizer=ConditionalNormalizer(), development_provider=provider)
        p = service.chat({'question_text': 'Private employee ako. Ilang oras ang normal na workday bago maging excess hours?'})
        self.assertEqual(p['explanation']['status'], 'generated')
        self.assertTrue(p['explanation']['citations_checked'])
        self.assertFalse(p['explanation']['legal_support_verified'])
        self.assertFalse(p['result']['answer_generation_allowed'])
        self.assertFalse(p['result']['display_allowed'])
        self.assertEqual(p['explanation']['llm_calls'], 2)
        self.assertTrue(p['explanation']['automated_support_checked'])

    def test_outside_and_clarification_do_not_generate(self):
        provider = Mock()
        for q in ['Who gets custody of our child?', 'They charged me too much.', 'What is the weather tomorrow?']:
            p = self.verifier.preflight(q)
            self.assertEqual(explain_recorded_sources(self.verifier, p, provider)['llm_calls'], 0)
        provider.complete.assert_not_called()


class CitationTests(unittest.TestCase):
    def test_anaphoric_item_is_not_an_invented_quantity_but_actual_units_are(self):
        from backend.application.grounding import numeric_facts, recorded_numeric_facts
        self.assertEqual(numeric_facts('The bag is not the one you ordered.'), set())
        self.assertEqual(numeric_facts('The one that they bought was different.'), set())
        self.assertEqual(numeric_facts('Replace it with the correct one.'), set())
        self.assertEqual(numeric_facts('One correct unit within one day.'), {'1.0'})
        self.assertEqual(numeric_facts('Return one unit within one day.'), {'1.0'})
        self.assertEqual(numeric_facts('The first day is excluded.'), {'1.0'})
        self.assertIn('1.0', recorded_numeric_facts('Undertime on any particular day shall not be offset.'))
        self.assertEqual(numeric_facts('Only if (1) responsibility is shown; (2) a hearing is given; (3) the limit is 20 percent.'), {'20.0'})
        self.assertEqual(numeric_facts('Within (1) day or (2) days, at 20 percent.'), {'1.0','2.0','20.0'})

    def test_cross_reference_must_be_in_the_selected_source(self):
        self.components[0]['sources'][0].update(citation_display='Section 9',parent_text='The additional compensation applies except to employees covered by Section 2 of this Rule.')
        self.draft['paragraphs'][0].update(text='The compensation rule excludes employees covered by Section 2.',evidence=[{'chunk_id':'h1','quote':self.components[0]['sources'][0]['parent_text']}])
        self.assertEqual(len(checked_claims(self.draft,self.components)),1)
        self.draft['paragraphs'][0]['text']='May compensation, maliban sa exempted sa Section 2.'
        self.assertEqual(len(checked_claims(self.draft,self.components)),1)
        self.draft['paragraphs'][0]['text']='Section 99 provides a different compensation rule.'
        with self.assertRaises(ValueError): checked_claims(self.draft,self.components)
        self.components[0]['sources'].append({'chunk_id':'h2','citation_display':'Section 99','parent_text':'Section 99 provides another rule.'})
        with self.assertRaises(ValueError): checked_claims(self.draft,self.components)

    def test_language_hint_does_not_rewrite_the_question_or_quotes(self):
        from backend.application.development_explanation import answer_language
        self.assertIn('Taglish',answer_language('Private employee ako, pwede ba yung overtime?'))
        self.assertEqual(answer_language('What conditions apply to overtime pay?'),'Plain English.')

    def test_plain_activity_test_synonyms_do_not_drop_the_source_condition(self):
        from backend.application.grounding import source_qualification_failure
        source='Regular work is usually necessary or desirable in the usual business unless fixed for a specific project or seasonal work.'
        self.assertIsNone(source_qualification_failure('An employee is regular for work usually needed in the normal business, unless the specific project or seasonal exception applies.',source))
        self.assertIsNotNone(source_qualification_failure('An employee is regular unless a project or seasonal exception applies.',source))

    def test_return_cost_exception_cannot_replace_an_agreed_return_period(self):
        from backend.application.grounding import source_qualification_failure
        source='When choosing replacement or refund, the merchant is entitled to return of original goods at no cost within a reasonable period unless otherwise agreed.'
        self.assertIsNotNone(source_qualification_failure('When choosing replacement or refund, return the original goods at no cost unless agreed otherwise.',source))
        self.assertIsNone(source_qualification_failure('When choosing replacement or refund, return the original goods at no cost within a reasonable period, unless another period is agreed.',source))

    def test_rest_premium_qualifications_and_price_ceiling_cannot_be_rewritten(self):
        from backend.application.grounding import source_qualification_failure
        source='Premium pay of thirty percent applies except to exempt employees on rest days not falling on regular holidays.'
        self.assertIsNotNone(source_qualification_failure('Rest-day work adds 30 percent.',source))
        self.assertIsNotNone(source_qualification_failure('Covered employees get 30 percent for rest-day work.',source))
        self.assertIsNone(source_qualification_failure('Covered employees get 30 percent for a rest day that is not a regular holiday.',source))
        price='A price tag is required. Products shall not be sold at a price higher than the displayed price.'
        self.assertIsNotNone(source_qualification_failure('No higher price is allowed unless the tag is corrected.',price))
        self.assertIsNone(source_qualification_failure('The displayed price is the ceiling. A price list can replace individual tags where permitted.',price))
    def test_seasonal_exception_and_mandatory_retailer_duty_keep_their_direction(self):
        from backend.application.grounding import source_qualification_failure
        status='Regular employment has specific project and seasonal exceptions. Casual employment has its own definition.'
        self.assertIsNotNone(source_qualification_failure('Seasonal work is excepted from regular employment; instead it falls under the casual employment category.',status))
        self.assertIsNone(source_qualification_failure('The general definition has project and seasonal exceptions. Casual employment is separately defined.',status))
        warranty='In the case of a retailer other than the distributor, the former shall take responsibility without cost to the buyer of presenting the warranty claim.'
        self.assertIsNotNone(source_qualification_failure('The retailer may present the claim to the distributor without charging the consumer.',warranty))
        self.assertIsNone(source_qualification_failure('The retailer must present the claim to the distributor without charging the buyer.',warranty))
        self.assertIsNotNone(source_qualification_failure('The retailer must forward the claim to the distributor (or manufacturer) without cost.',warranty))
        self.assertIsNone(source_qualification_failure('The retailer must forward the claim to the distributor and may later pursue the distributor or manufacturer for reimbursement.',warranty))
    def test_product_refund_summary_needs_the_source_condition(self):
        from backend.application.grounding import source_qualification_failure
        source='If the imperfection is not corrected within the applicable period, the buyer may seek reimbursement or a price reduction.'
        self.assertIsNotNone(source_qualification_failure('The supplier is liable and the buyer can demand a refund or a price reduction.',source))
        self.assertIsNone(source_qualification_failure('If the imperfection remains uncorrected after the applicable period, the buyer may seek reimbursement.',source))
        self.assertIsNone(source_qualification_failure('The buyer can use the alternatives immediately where replacing parts would jeopardize product quality.',source))
        self.assertIsNone(source_qualification_failure('Kapag hindi naayos sa applicable period, puwedeng piliin ang refund.',source))

    def test_display_method_exception_cannot_qualify_the_price_ceiling(self):
        from backend.application.grounding import source_qualification_failure
        source = ('Consumer products shall not be sold above the price tag. '
                  'When individual tags are not practical, a nearby price list may be used.')
        self.assertIsNotNone(source_qualification_failure(
            'The price shown must be charged; no higher amount is allowed unless the item is too small to tag, when a price list may be used.', source))
        self.assertIsNotNone(source_qualification_failure(
            'A seller cannot charge more than the posted price except where individual tagging is not practical.', source))
        self.assertIsNone(source_qualification_failure(
            'A price list can replace individual tags where tagging is not practical. The checkout price must not be higher than the displayed price.', source))
        self.assertIsNone(source_qualification_failure(
            'The displayed price must be charged without discrimination.', source))

    def test_source_specific_prerequisites_cannot_be_silently_dropped(self):
        from backend.application.grounding import source_qualification_failure
        payment='In case of payment of wages by results, final settlement shall be made immediately after completion.'
        self.assertIsNotNone(source_qualification_failure('Any final settlement is due as soon as work is completed.',payment))
        self.assertIsNone(source_qualification_failure('For payment by results, final settlement is due after completion.',payment))
        self.assertIsNone(source_qualification_failure('Wages are paid every two weeks.',payment))
        deduction='Where the practice of making deductions is recognized, the conditions must be met.'
        self.assertIsNotNone(source_qualification_failure('Deductions are allowed when the worker caused the loss.',deduction))
        self.assertIsNone(source_qualification_failure('Where that trade practice is recognized, deductions remain subject to the conditions.',deduction))
        status='Employment shall be deemed to be regular unless fixed for a specific project.'
        self.assertIsNotNone(source_qualification_failure('A project-based job is regular only when the project ends on a stated date.',status))
        self.assertIsNone(source_qualification_failure('The rule describes regular employment with an exception for a specific project.',status))

    def test_interest_and_project_status_inferences_need_source_support(self):
        from backend.application.grounding import source_qualification_failure
        self.assertIsNotNone(source_qualification_failure('The buyer can demand a refund with interest.','The buyer may seek reimbursement with monetary updating.'))
        self.assertIsNone(source_qualification_failure('The buyer can demand a refund with monetary updating.','The buyer may seek reimbursement with monetary updating.'))
        project='The exception concerns a specific project. Employment is regular for necessary business activities, except seasonal work.'
        self.assertIsNotNone(source_qualification_failure('The exception makes employment casual.',project))
        self.assertIsNotNone(source_qualification_failure('The contract must state an exact completion date.',project))
        self.assertIsNotNone(source_qualification_failure('Employment is regular for necessary activities.',project))
        self.assertIsNone(source_qualification_failure('Necessary activities are regular subject to the project and seasonal exceptions.',project))
        returns='The online merchant is entitled to the return of the original goods delivered at no cost to the consumer.'
        self.assertIsNotNone(source_qualification_failure('The seller must return the goods at no cost to you.',returns))
        self.assertIsNone(source_qualification_failure('The merchant may require the consumer to return the original goods at no cost.',returns))

    def test_a_fact_error_can_be_removed_once_but_the_revised_draft_must_pass(self):
        provider,verifier,pre=self.revision_fixture()
        report=self.assessment(False,'unsupported');report['assessments'][0]['no_new_facts']=False
        provider.assess.side_effect=[report,self.assessment(True)]
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['llm_calls'],4)
        provider.revise.assert_called_once();self.assertEqual(provider.assess.call_count,2)

    def test_source_selection_reaches_later_warranty_clauses(self):
        from backend.application.development_explanation import source_options
        text='\n'.join('Condition %s requires the supplier to preserve this stated qualification.' % i for i in range(30))
        expanded,lookup=source_options([{'component_id':'c1','sources':[{'chunk_id':'h1','parent_text':text}]}])
        self.assertTrue(any('Condition 29 ' in entry[2] for entry in lookup.values()))
        self.assertTrue(all(entry[2] in text for entry in lookup.values()))

    def test_membership_phrase_does_not_create_an_invented_quantity(self):
        from backend.application.grounding import numeric_facts
        self.assertEqual(numeric_facts('one of the conditions; one employee; one day; one percent'),{'1.0'})
        self.assertEqual(numeric_facts('one of the listed conditions'),set())
        self.assertEqual(numeric_facts('Pay 999 pesos'),{'999.0'})

    def test_typographic_hyphens_preserve_written_quantities(self):
        from backend.application.grounding import numeric_facts
        for separator in ['-','\u2010','\u2011','\u2013']:
            with self.subTest(separator=separator):
                self.assertEqual(numeric_facts('twenty'+separator+'five percent'),{'25.0'})
                self.assertEqual(numeric_facts('twenty'+separator+'four hours'),{'24.0'})
        self.assertNotEqual(numeric_facts('twenty-five percent'),numeric_facts('twenty-six percent'))
        self.assertEqual(numeric_facts('The dispute must first be submitted.'),set())
        self.assertEqual(numeric_facts('The first step is filing.'),set())
        self.assertEqual(numeric_facts('the twenty-first day'),{'21.0'})
        self.assertEqual(numeric_facts('20 percent of wages in a week'),{'20.0'})
        self.assertEqual(numeric_facts('twenty percent of wages in one week'),{'20.0','1.0'})
        from backend.application.grounding import recorded_numeric_facts
        self.assertEqual(recorded_numeric_facts('20 percent of wages in a week'),{'20.0','1.0'})
        self.assertEqual(numeric_facts('It must first undergo conciliation.'),set())
        self.assertEqual(numeric_facts('A product is one that meets the conditions.'),set())

    def test_material_period_and_seller_role_exceptions_are_preserved(self):
        from backend.application.grounding import source_qualification_failure
        source='The parties may agree to reduce or increase the term. The default period is thirty days.'
        self.assertIsNotNone(source_qualification_failure('The buyer has a remedy after thirty days.',source))
        self.assertIsNone(source_qualification_failure('The thirty-day default can be varied by agreement.',source))
        warranty='The immediate seller may be a factory. A retailer other than the distributor forwards the claim.'
        self.assertIsNotNone(source_qualification_failure('The seller must honor the claim right away.',warranty))
        self.assertIsNotNone(source_qualification_failure('The retailer must immediately honor the warranty.',warranty))
        self.assertIsNone(source_qualification_failure('The retailer forwards the warranty claim without cost.',warranty))
        status='The specific project and seasonal exceptions affect regular employment.'
        self.assertIsNotNone(source_qualification_failure('Employment is non\u2011regular only when the project end is identified.',status))
        self.assertIsNone(source_qualification_failure('The regular-employment rule has project and seasonal exceptions.',status))
        # Prose locators are checked against the selected citation metadata by
        # checked_claims, instead of rejecting even an accurately cited number.
        self.assertIsNone(source_qualification_failure('Article 283 lists dismissal causes.','Article 283 lists dismissal causes.'))
        self.assertIsNone(source_qualification_failure('The source lists dismissal causes.','Article 283 lists dismissal causes.'))
        ordinary='Activities usually necessary or desirable in the usual business are regular, unless a specific project or seasonal exception applies.'
        self.assertIsNotNone(source_qualification_failure('Regular status applies unless a project or seasonal exception applies.',ordinary))
        self.assertIsNone(source_qualification_failure('Regular work involves necessary or desirable activities in the usual business, with project and seasonal exceptions.',ordinary))

    def test_support_feedback_is_actionable_and_keeps_the_public_contract(self):
        from backend.application.development_explanation import TogetherDevelopmentExplanation
        from backend.application.grounding import support_passed
        provider=TogetherDevelopmentExplanation('openai/gpt-oss-120b','test-only-key')
        report=self.assessment(True)
        report['assessments'][0]['source_check_reason']='The cited source establishes the conditional hours limit.'
        report['assessments'][0].update(answers_requested_issue=True,actor_scope_preserved=True,conditions_attached_correctly=True)
        provider._send=Mock(return_value=report)
        claims=checked_claims(self.draft,self.components)
        checked=provider.assess('What are normal work hours?',claims,self.components)
        self.assertTrue(support_passed(checked,claims))
        self.assertNotIn('source_check_reason',checked['assessments'][0])
        self.assertIn('conditional hours limit',provider.last_support_feedback['development_1'])
        self.assertEqual(provider._send.call_args.args[0]['reasoning_effort'],'medium')

    def test_irrelevant_true_paraphrase_cannot_pass_live_support_contract(self):
        from backend.application.development_explanation import TogetherDevelopmentExplanation
        from backend.application.grounding import support_passed
        provider=TogetherDevelopmentExplanation('openai/gpt-oss-120b','test-only-key')
        report=self.assessment(True)
        report['assessments'][0].update(source_check_reason='A true paragraph about another issue.',answers_requested_issue=False,actor_scope_preserved=True,conditions_attached_correctly=True)
        provider._send=Mock(return_value=report)
        claims=checked_claims(self.draft,self.components)
        checked=provider.assess('Explain waiting time.',claims,self.components)
        self.assertFalse(support_passed(checked,claims))
        payload=json.loads(provider._send.call_args.args[0]['messages'][1]['content'])
        self.assertIn('query',payload['source_components'][0])
        self.assertIn('response_focus',payload['source_components'][0])

    def test_missing_component_can_be_corrected_once_without_skipping_checks(self):
        provider,verifier,pre=self.revision_fixture()
        pre['components'].append({**pre['components'][0],'component_id':'c2'})
        repaired=copy.deepcopy(self.draft)
        repaired['paragraphs'].append({**copy.deepcopy(repaired['paragraphs'][0]),'component_id':'c2'})
        provider.revise.return_value=repaired
        provider.assess.return_value={'assessments':[self.assessment(True)['assessments'][0],self.assessment(True,claim_id='development_2')['assessments'][0]]}
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['llm_calls'],3)
        self.assertEqual(len(result['claims']),2);provider.revise.assert_called_once();provider.assess.assert_called_once()

    def test_one_invalid_concern_does_not_erase_an_independently_checked_answer(self):
        provider,verifier,pre=self.revision_fixture()
        pre['components'].append({**pre['components'][0],'component_id':'c2'})
        draft=copy.deepcopy(self.draft)
        draft['paragraphs'].append({**copy.deepcopy(draft['paragraphs'][0]),'component_id':'c2','text':'The wage amount is 99999 pesos.'})
        provider.complete.return_value=draft;provider.can_revise=False
        provider.assess.return_value=self.assessment(True)
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'partially_generated')
        self.assertEqual(len(result['claims']),1)
        self.assertEqual(result['unanswered_components'][0]['component_id'],'c2')
        self.assertTrue(result['automated_support_checked'])
        self.assertNotIn('99999',result['claims'][0]['text'])

    def test_wrong_component_selection_correction_still_needs_support(self):
        provider,verifier,pre=self.revision_fixture()
        provider.complete.side_effect=ValueError('Unknown selected source')
        provider.assess.return_value=self.assessment(True)
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['llm_calls'],3)
        provider.revise.assert_called_once();provider.assess.assert_called_once()

    def test_compact_prompt_preserves_full_sources_and_exact_proof(self):
        from backend.application.development_explanation import source_options,prompt_sources,selected_draft
        text='The supplier must preserve '+('each material qualification and exception in this complete recorded authority '*12)+'.'
        components=[{'component_id':'c1','sources':[{'chunk_id':'h1','parent_text':text}]}]
        expanded,lookup=source_options(components);compact=prompt_sources(expanded)
        self.assertEqual(compact[0]['sources'][0]['parent_text'],text)
        for option in compact[0]['sources'][0]['quote_options']:
            self.assertNotIn('quote',option)
            self.assertEqual(text[option['start']:option['end']],lookup[option['quote_id']][2])
        self.assertLess(len(json.dumps(compact)),len(json.dumps(expanded)))
        qid=compact[0]['sources'][0]['quote_options'][0]['quote_id']
        draft={'paragraphs':[{'component_id':'c1','text':'A source-grounded rule.', 'evidence':[{'quote_id':qid}]}]}
        restored=selected_draft(draft,lookup)
        self.assertIn(restored['paragraphs'][0]['evidence'][0]['quote'],text)
        self.assertIn('quote',expanded[0]['sources'][0]['quote_options'][0])
    def revision_fixture(self):
        provider,verifier=Mock(),Mock();provider.name='test';provider.model='mock';provider.last_usage={};provider.can_revise=True
        verifier.check_candidate.return_value=[]
        hit={**self.components[0]['sources'][0],'conditions':[],'heading':'Normal Hours of Work'}
        pre={'question_text':'What are normal hours of work?','routing':{'routing_action':'retrieve_supported_evidence'},
             'components':[{'component_id':'c1','query':'normal hours of work','allowed_domain':'labor',
                            'candidates':[hit],'evidence_gates':[{'chunk_id':'h1','reasons':[]}]}]}
        provider.complete.return_value=copy.deepcopy(self.draft);provider.revise.return_value=copy.deepcopy(self.draft)
        return provider,verifier,pre

    def test_local_rejection_sends_the_actual_bad_prose_for_one_checked_correction(self):
        provider,verifier,pre=self.revision_fixture()
        bad='Normal work is limited to 99999 hours per day.'
        provider.complete.return_value['paragraphs'][0]['text']=bad
        provider.assess.return_value=self.assessment(True)
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated')
        feedback=provider.revise.call_args.args[3]
        self.assertEqual(feedback['rejected_prose'],[{'component_id':'c1','text':bad}])
        self.assertEqual(feedback['validation_failure'],'numeric_detail_not_in_source')
        self.assertNotEqual(result['claims'][0]['text'],bad)
        provider.assess.assert_called_once()

    def test_missing_authority_for_one_component_does_not_erase_a_supported_other_component(self):
        provider,verifier,pre=self.revision_fixture()
        pre['components'].append({'component_id':'c2','query':'thirteenth-month pay','allowed_domain':'labor',
                                  'candidates':[],'evidence_gates':[{'chunk_id':'held','reasons':['related_authority_unavailable:missing']} ]})
        provider.assess.return_value=self.assessment(True)
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'partially_generated')
        self.assertFalse(result['coverage_complete'])
        self.assertEqual([c['component_id'] for c in result['claims']],['c1'])
        self.assertEqual(result['unanswered_components'],[{'component_id':'c2','query':'thirteenth-month pay','reason':'related_authority_missing'}])
        self.assertEqual(len(provider.complete.call_args.args[1]['components']),1)
        self.assertEqual(result['llm_calls'],2)

    def test_failed_individual_support_cannot_remove_an_independently_checked_paragraph(self):
        provider,verifier,pre=self.revision_fixture();provider.can_revise=False
        pre['components'].append({**copy.deepcopy(pre['components'][0]),'component_id':'c2'})
        provider.complete.return_value['paragraphs'].append({**copy.deepcopy(self.draft['paragraphs'][0]),'component_id':'c2'})
        provider.assess.return_value={'assessments':self.assessment(True)['assessments']+self.assessment(False,'unsupported','development_2')['assessments']}
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'partially_generated')
        self.assertEqual([c['component_id'] for c in result['claims']],['c1'])
        self.assertEqual(result['unanswered_components'][0]['reason'],'claim_support_failed')
        self.assertEqual(result['llm_calls'],2);provider.revise.assert_not_called()

    def test_missing_duplicate_or_extra_assessments_cannot_authorize_partial_prose(self):
        from backend.application.development_explanation import supported_claim_subset
        claims=checked_claims(self.draft,self.components)
        good=self.assessment(True)['assessments'][0]
        with self.assertRaises(ValueError):supported_claim_subset({'assessments':[]},claims)
        for rows in [[good,good],[{**good,'claim_id':'unknown'}]]:
            with self.subTest(rows=rows):self.assertEqual(supported_claim_subset({'assessments':rows},claims),[])

    @staticmethod
    def assessment(qualified,verdict='supported',claim_id='development_1'):
        return {'assessments':[{'claim_id':claim_id,'verdict':verdict,'qualifications_preserved':qualified,
                               'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True}]}

    def test_qualification_revision_requires_a_new_complete_check(self):
        provider,verifier,pre=self.revision_fixture()
        provider.assess.side_effect=[self.assessment(False),self.assessment(True)]
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['llm_calls'],4)
        self.assertTrue(result['revision_attempted']);provider.revise.assert_called_once()
        self.assertEqual(provider.assess.call_count,2)

    def test_irrelevant_same_domain_source_never_reaches_the_provider(self):
        provider,verifier,pre=self.revision_fixture()
        pre['question_text']='How does thirteenth-month pay work?'
        pre['components'][0]['query']='thirteenth-month pay'
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['reason'],'source_context_unavailable')
        self.assertEqual(result['llm_calls'],0)
        provider.complete.assert_not_called();provider.assess.assert_not_called()

    def test_revision_is_bounded_and_does_not_override_a_second_failed_check(self):
        provider,verifier,pre=self.revision_fixture()
        provider.assess.return_value=self.assessment(False)
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['reason'],'claim_support_failed');self.assertEqual(result['claims'],[])
        self.assertEqual(result['llm_calls'],4);provider.revise.assert_called_once()

    def test_unsafe_mismatched_or_time_limited_checks_do_not_trigger_revision(self):
        unsafe=self.assessment(False,'unsupported');unsafe['assessments'][0]['no_case_outcome']=False
        for report,allowed in [(unsafe,True),(self.assessment(False,claim_id='wrong'),True),(self.assessment(False),False)]:
            provider,verifier,pre=self.revision_fixture();provider.assess.return_value=report;provider.can_revise=allowed
            result=explain_recorded_sources(verifier,pre,provider)
            self.assertEqual(result['claims'],[]);self.assertEqual(result['llm_calls'],2);provider.revise.assert_not_called()

    def test_citation_support_correction_still_requires_a_passed_new_assessment(self):
        provider,verifier,pre=self.revision_fixture()
        provider.assess.side_effect=[self.assessment(True,'unsupported'),self.assessment(True)]
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['status'],'generated');self.assertEqual(result['llm_calls'],4)
        provider.revise.assert_called_once()

    def test_revised_invented_quote_is_rejected_before_a_second_assessment(self):
        provider,verifier,pre=self.revision_fixture();provider.assess.return_value=self.assessment(False)
        provider.revise.return_value['paragraphs'][0]['evidence'][0]['quote']='An invented source quotation.'
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['reason'],'citation_validation_failed');self.assertEqual(result['claims'],[])
        self.assertEqual(result['llm_calls'],3);self.assertEqual(provider.assess.call_count,1)

    def setUp(self):
        self.components = [{'component_id': 'c1', 'sources': [{'chunk_id': 'h1', 'provision_id': 'p1', 'document_id': 'd1',
            'citation_display': 'Recorded article', 'parent_text': 'The normal hours of work shall not exceed eight hours per day.'}]}]
        self.draft = {'paragraphs': [{'component_id': 'c1', 'text': 'The recorded text sets a limit on normal daily work hours.',
            'evidence': [{'chunk_id': 'h1', 'quote': 'normal hours of work shall not exceed eight hours per day.'}]}]}

    def test_exact_quote_offsets_are_calculated_from_stored_text(self):
        claims = checked_claims(self.draft, self.components); cite = claims[0]['citations'][0]
        text = self.components[0]['sources'][0]['parent_text']
        self.assertEqual(text[cite['start']:cite['end']], cite['quote'])

    def test_whitespace_only_quote_recovery_preserves_the_exact_stored_span(self):
        components = copy.deepcopy(self.components)
        components[0]['sources'][0]['parent_text'] = components[0]['sources'][0]['parent_text'].replace('not exceed', 'not\nexceed')
        cite = checked_claims(self.draft, components)[0]['citations'][0]
        self.assertIn('not\nexceed', cite['quote'])
        self.assertEqual(components[0]['sources'][0]['parent_text'][cite['start']:cite['end']], cite['quote'])

    def test_fabricated_quote_wrong_source_extra_fields_and_numbers_are_rejected(self):
        bad = []
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['evidence'][0]['quote'] = 'A fabricated quotation'; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['evidence'][0]['chunk_id'] = 'other'; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['text'] += ' Pay 999 pesos.'; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['approved'] = True; bad.append(d)
        d = copy.deepcopy(self.draft); d['paragraphs'][0]['component_id'] = 'excluded'; bad.append(d)
        for draft in bad:
            with self.subTest(draft=draft), self.assertRaises(ValueError): checked_claims(draft, self.components)

    def test_missing_supported_component_is_not_silently_omitted(self):
        components = copy.deepcopy(self.components); components.append({**components[0], 'component_id': 'c2'})
        with self.assertRaises(ValueError): checked_claims(self.draft, components)

    def test_same_component_cannot_be_output_twice(self):
        duplicate=copy.deepcopy(self.draft)
        duplicate['paragraphs'].append(copy.deepcopy(duplicate['paragraphs'][0]))
        with self.assertRaisesRegex(ValueError,'duplicated'):checked_claims(duplicate,self.components)

    def test_related_authority_and_fixture_gates_skip_provider(self):
        provider, verifier = Mock(), Mock()
        p = {'routing': {'routing_action': 'retrieve_supported_evidence'}, 'software_fixture_mode': True}
        self.assertEqual(explain_recorded_sources(verifier, p, provider)['llm_calls'], 0)
        p.update(software_fixture_mode=False, components=[{'component_id':'c1','query':'thirteenth-month pay','allowed_domain':'labor','candidates':[], 'evidence_gates': [{'chunk_id': 'x','reasons':['related_authority_unavailable:MO_28_1986']}]}])
        self.assertEqual(explain_recorded_sources(verifier, p, provider)['reason'], 'related_authority_missing')
        provider.complete.assert_not_called()

    def test_empty_supported_output_is_a_distinct_safe_withholding_state(self):
        provider,verifier=Mock(),Mock()
        provider.complete.return_value={'paragraphs':[]}
        verifier.check_candidate.return_value=[]
        pre={'question_text':'What are normal hours of work?','routing':{'routing_action':'retrieve_supported_evidence'},
             'components':[{'component_id':'c1','query':'normal hours of work','allowed_domain':'labor',
                            'candidates':[{**self.components[0]['sources'][0],'heading':'Normal Hours of Work'}],'evidence_gates':[{'chunk_id':'h1','reasons':[]}]}]}
        pre['components'][0]['candidates'][0]['conditions']=[]
        result=explain_recorded_sources(verifier,pre,provider)
        self.assertEqual(result['reason'],'no_supported_explanation')
        self.assertEqual(result['claims'],[])
        self.assertEqual(result['llm_calls'],1)
        provider.assess.assert_not_called()


if __name__ == '__main__': unittest.main()
