"""Submission regressions: language boundaries, source limits and timeout fallback."""
import json,sys,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from urllib.request import Request
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
from scope_constraints import constraint
from classifier_runtime import missing_context
from clause_classifier import segment_question
from backend.application.grounding import source_qualification_failure,numeric_facts
from backend.application.development_explanation import source_options,selected_draft
from backend.application.controls import RequestContext,CancellableTransport,ProviderStopped
from backend.application.source_issues import issue_for,RELIGIOUS_SCHEDULING_PROVISION
from dataset.pipelines.item11.query_relevance import query_facets,source_relevance


class LanguageBoundaryTests(unittest.TestCase):
    def test_charger_is_not_a_money_charge(self):
        self.assertIsNone(missing_context('My faulty charger was bought through a shopping platform.'))
        self.assertIsNotNone(missing_context('They charged me too much.'))

    def test_workplace_duty_and_customer_purchase_are_distinct(self):
        self.assertEqual(constraint('A private sign-making shop requires extra work after the ordinary daily hours.')[0],'labor')
        self.assertEqual(constraint('A private sign-making shop sold me a broken sign.')[0],'consumer')
        self.assertEqual(constraint('A privately owned repair business closed on a regular holiday.')[0],'labor')

    def test_night_benefit_keeps_special_worker_exclusions(self):
        self.assertEqual(constraint('Private bakery employee ako, walang night differential sa duty.')[0],'labor')
        for text in ['Government employee ako, walang night differential.',
                     'Kasambahay ako at may night differential question.',
                     'Overseas worker ako at may night differential concern.']:
            self.assertEqual(constraint(text)[0],'excluded')

    def test_stock_investment_and_stock_loss_are_distinct(self):
        self.assertEqual(constraint('Which Philippine stock should I buy for profit?')[0],'excluded')
        self.assertEqual(constraint('My private employer deducted a stock shortage from wages.')[0],'labor')

    def test_disclosure_is_privacy_even_before_the_scope_question(self):
        self.assertEqual(constraint('A mobile application disclosed private account details without permission.')[1],'consumer.data_privacy')

    def test_generic_question_does_not_create_a_second_safety_concern(self):
        q='A newly bought extension cord from a retail shop sparks. I want general product-safety information, not a damages computation.'
        self.assertEqual(len(segment_question(q)['components']),1)

    def test_explicit_new_concerns_do_not_disappear(self):
        q='Private restaurant crew ako, may overtime issue. Hiwalay, kulang ang quantity ng package ng tiles sa hardware.'
        a=segment_question(q);self.assertEqual(len(a['components']),2)
        vague=segment_question('The local shop kept my change. Hiwalay, may isa pang problemang hindi ko maipaliwanag.')
        self.assertTrue(vague['requires_clarification'])

    def test_inherited_property_remains_a_third_excluded_concern(self):
        a=segment_question('My private employer withheld wages. An unrelated shop charged above its tag. Separately, I need help dividing inherited land among siblings.')
        self.assertEqual(len(a['components']),3)
        self.assertEqual(constraint(a['components'][-1])[1],'outside.family')

    def test_anaphoric_service_request_stays_with_paid_repair(self):
        a=segment_question('A paid furniture-repair business left a chair unusable. What does the service-quality rule say about proper performance?')
        self.assertEqual(len(a['components']),1)

    def test_notice_followup_keeps_resignation_context(self):
        a=segment_question('Magreresign ako sa private events company. Walang emergency reason na binabanggit, gusto ko lang lumipat ng trabaho. Ano ang ordinary notice rule at ano ang general exceptions?')
        self.assertEqual(len(a['components']),1)

    def test_taglish_resignation_has_an_employee_termination_facet(self):
        facets=query_facets('Magreresign ako sa private events company. Ano ang ordinary notice rule?','labor')
        self.assertTrue(any(x[3]=='employee resignation notice' for x in facets))

    def test_neutral_job_introductions_are_context_not_unanswered_concerns(self):
        for q in ['I label bottles for a private company in Iloilo. The next payday is five weeks later. What is the wage-payment rule?',
                  'Empleyado ako ng private garment shop. Walang deductions sa payroll. Anong records ang dapat tingnan?',
                  'Sa private office namin, binabawas ang coffee break. Ano ang general rule para sa short rest breaks?',
                  'A private convenience store stays open daily. The owner says every employee must work every day. What is the weekly-rest rule?',
                  'A privately owned repair business closed on a regular holiday. Management says closing removes holiday pay. What rules apply?']:
            with self.subTest(q=q):self.assertEqual(len(segment_question(q)['components']),1)
        self.assertGreater(len(segment_question('My private employer has not paid my wages. Separately, a shop refused my warranty.')['components']),1)

    def test_certification_representation_selects_deceptive_sales(self):
        q='Sabi certified ang electric kettle, pero ayaw magpakita ng basehan. Ano ang rule sa certification claim?'
        records={r['provision_id']:r for r in map(json.loads,(ROOT/'outputs/item11-retrieval-v1.3.55/records.jsonl').read_text(encoding='utf-8').splitlines())}
        self.assertGreater(source_relevance(q,'consumer',records['RA_7394_1992__art_50']),source_relevance(q,'consumer',records['RA_7394_1992__art_129']))

    def test_safety_supplier_question_does_not_borrow_a_service_remedy(self):
        records={r['provision_id']:r for r in map(json.loads,(ROOT/'outputs/item11-retrieval-v1.3.55/records.jsonl').read_text(encoding='utf-8').splitlines())}
        s=records['RA_7394_1992__art_102']
        self.assertEqual(source_relevance('A desk fan caught fire. Are manufacturer and supplier liability the same for product safety?','consumer',s),0)
        self.assertGreater(source_relevance('A paid repair service left the speaker unusable. What service-quality remedies apply?','consumer',s),0)


class SourceLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources={r['provision_id']:r['parent_text'] for r in map(json.loads,(ROOT/'outputs/item11-retrieval-v1.3.55/records.jsonl').read_text(encoding='utf-8').splitlines())}

    def source_with(self,*terms):
        return next(s for s in self.sources.values() if all(t in s.casefold() for t in terms))

    def test_religious_pronoun_is_not_assigned_by_paraphrase(self):
        s=self.source_with('religious','his choice')
        self.assertIsNotNone(source_qualification_failure('The employer may choose another rest day at least two days a month.',s))
        self.assertIsNotNone(source_qualification_failure('Puwedeng baguhin ng employer ang araw ng pahinga para sa ilang pagkakataon sa isang buwan.',s))
        self.assertIsNone(source_qualification_failure('The written religious preference must be communicated at least seven days before the desired effectivity.',s))

    def test_ambiguous_religious_passage_is_held_for_interpretation_review(self):
        self.assertIsNotNone(issue_for({'provision_id':RELIGIOUS_SCHEDULING_PROVISION}))
        self.assertIsNone(issue_for({'provision_id':'LAB_CODE_2022__art_91'}))

    def test_quantity_trigger_preserves_inherent_variations(self):
        s=self.sources['RA_7394_1992__art_101']
        self.assertIsNotNone(source_qualification_failure('Ang netong laman ay mas mababa kaysa sa nakasaad sa label.',s))
        self.assertIsNone(source_qualification_failure('Considering inherent variations, the net content is less than indicated on the packaging or label.',s))

    def test_quantity_comparator_does_not_invent_a_receipt_basis(self):
        s=self.sources['RA_7394_1992__art_101']
        self.assertIsNotNone(source_qualification_failure('Kulang ang laman kumpara sa nakasaad sa label o resibo.',s))
        self.assertIsNone(source_qualification_failure('The comparison is with container, packaging, labeling or advertisement, considering inherent variations.',s))

    def test_manufacturer_rule_does_not_exhaust_all_seller_liability(self):
        s=self.sources['RA_7394_1992__art_97']
        self.assertIsNotNone(source_qualification_failure('A seller is not held liable under this rule; its responsibility arises only if it engages in a deceptive act.',s))
        self.assertIsNone(source_qualification_failure('This provision addresses manufacturers, producers and importers; the supplied passage does not establish all retailer liability rules.',s))

    def test_seasonal_exception_is_not_a_contract_validity_judgment(self):
        s=self.sources['LAB_CODE_2022__art_295']
        self.assertIsNotNone(source_qualification_failure('Ang kontrata ay valid lang habang tumatagal ang picking season.',s))
        self.assertIsNone(source_qualification_failure('The seasonal exception concerns seasonal work and employment for the duration of the season.',s))

    def test_price_reduction_does_not_reverse_the_payment_actor(self):
        s=self.sources['RA_7394_1992__art_101']
        for q in ['The consumer must pay the proportionate price.','Puwedeng bayaran ang proporsyonal na presyo.']:
            self.assertIsNotNone(source_qualification_failure(q,s))
        self.assertIsNone(source_qualification_failure('Puwedeng humingi ng dagdag sa nawawalang timbang o sukat.',s))

    def test_warranty_contents_do_not_void_the_entire_warranty(self):
        s=self.sources['RA_7394_1992__art_68']
        self.assertIsNotNone(source_qualification_failure('Any warranty that omits the period is void.',s))
        self.assertIsNone(source_qualification_failure('The warranty must state the period. Any stipulation contrary to this article is null and void.',s))

    def test_taglish_retailer_cost_condition_keeps_both_failures(self):
        s=self.sources['RA_7394_1992__art_68']
        self.assertIsNotNone(source_qualification_failure('Siya ang sasagot sa gastos kung hindi tumugon ang distributor o manufacturer.',s))
        self.assertIsNone(source_qualification_failure('The retailer is subsidiarily liable if both manufacturer and distributor fail to honor the warranty.',s))
        self.assertIsNone(source_qualification_failure('Kapag parehong hindi tumugon ang manufacturer at distributor, subsidiarily liable ang retailer sa gastos. May karapatan pa rin siyang habulin ang distributor o manufacturer para sa bayad.',s))

    def test_missing_proof_does_not_establish_false_certification(self):
        s=self.sources['RA_7394_1992__art_50']
        self.assertIsNotNone(source_qualification_failure('The seller cannot show proof of certification and may have made a false representation.',s))
        self.assertIsNone(source_qualification_failure('The rule prohibits false representations of approval. Failure to produce proof does not establish falsity.',s))

    def test_exhaustion_trigger_is_not_an_only_if_rule(self):
        s=self.source_with('internal redress mechanism','deemed exhausted')
        self.assertIsNotNone(source_qualification_failure('The mechanism is considered exhausted only when the platform has not resolved the complaint.',s))
        self.assertIsNone(source_qualification_failure('The mechanism is deemed exhausted if the complaint remains unresolved within the recorded period.',s))

    def test_same_entity_clause_does_not_exclude_other_platform_liability(self):
        s=self.source_with('primarily liable','same entity')
        self.assertIsNotNone(source_qualification_failure('The platform is only treated as liable when it is the same entity.',s))
        self.assertIsNone(source_qualification_failure('The merchant is primarily liable. This passage also addresses a platform found to be the same entity.',s))

    def test_return_and_salary_actor_directions_are_preserved(self):
        s=self.sources['RA_11967_2023__sec_20']
        self.assertIsNotNone(source_qualification_failure('Ang online merchant ay may karapatang ibalik ang original item.',s))
        self.assertIsNone(source_qualification_failure('When replacement or refund is chosen, the merchant may require the consumer to return the original goods at no cost.',s))
        s=self.sources['SC_110068_1993_STATUTORY_QUOTES__recorded_rule']
        self.assertIsNotNone(source_qualification_failure('Ang basic salary ay sahod na binabayaran mo para sa trabaho.',s))
        self.assertIsNone(source_qualification_failure('Basic salary describes remuneration earned by the employee.',s))

    def test_better_policy_does_not_invent_a_deadline_extension(self):
        s=self.source_with('unless the company has a better policy')
        self.assertIsNotNone(source_qualification_failure('Puwede itong ma-extend kung may collective bargaining agreement.',s))
        self.assertIsNone(source_qualification_failure('Final pay is within 30 days after leaving unless the company has a better policy.',s))

    def test_forwarding_duty_does_not_forbid_voluntary_warranty_honor(self):
        s=self.sources['RA_7394_1992__art_68']
        self.assertIsNotNone(source_qualification_failure('The retailer must not honor the warranty directly.',s))
        self.assertIsNotNone(source_qualification_failure('Pero hindi siya dapat mag-honor ng warranty directly.',s))
        self.assertIsNone(source_qualification_failure('The retailer must forward the claim without cost and retains the recorded subsidiary liability.',s))

    def test_engagement_does_not_invent_an_earlier_probation_deadline(self):
        s=self.sources['LAB_CODE_2022__art_296']
        self.assertIsNotNone(source_qualification_failure('The standards must be communicated before probation begins.',s))
        self.assertIsNone(source_qualification_failure('The reasonable standards must be made known at the time of engagement.',s))

    def test_price_ceiling_does_not_require_exactly_the_displayed_price(self):
        s=self.sources['RA_7394_1992__art_81']
        self.assertIsNotNone(source_qualification_failure('The price shown must be the one charged to every buyer.',s))
        self.assertIsNone(source_qualification_failure('The rule prohibits charging above the displayed price.',s))

    def test_procedural_and_pronominal_one_are_not_new_quantities(self):
        self.assertEqual(numeric_facts('the office where the request was first made'),set())
        self.assertEqual(numeric_facts('the price is the one charged'),set())
        self.assertEqual(numeric_facts('one month and one percent'),{'1.0'})

    def test_limited_quote_does_not_prove_absence_of_proration_law(self):
        s=self.sources['SC_110068_1993_STATUTORY_QUOTES__recorded_rule']
        self.assertIsNotNone(source_qualification_failure('The law does not provide a formula for proportionate pay.',s))
        self.assertIsNone(source_qualification_failure('The supplied excerpt describes the annual basic-salary definition; it does not establish all the rules for prorating.',s))

    def test_correction_period_bounds_do_not_modify_options(self):
        s=self.sources['RA_7394_1992__art_100']
        self.assertIsNotNone(source_qualification_failure('Ang mga opsyon ay maaaring i-adjust ng parties.',s))
        self.assertIsNone(source_qualification_failure('The parties may adjust the correction term within its recorded bounds; the remedy options remain separate.',s))

    def test_duration_alone_does_not_authorize_an_uncited_remedy(self):
        s=self.sources['RA_7394_1992__art_71']
        self.assertIsNotNone(source_qualification_failure('You can demand a free repair or refund under this guarantee.',s))
        self.assertIsNone(source_qualification_failure('Service firms guarantee workmanship and replacement parts for the recorded duration, indicated on the invoice.',s))
        self.assertIsNone(source_qualification_failure('Where the service-quality conditions apply, the consumer may request re-execution or a refund.',s+' '+self.sources['RA_7394_1992__art_102']))

    def test_taglish_promo_and_sale_terms_are_not_adjudicated(self):
        s=self.sources['RA_7394_1992__art_68']
        for text in ['Anumang kondisyon sa discount promo na nagbabawal ng claim ay walang bisa.',
                     'Any clause canceling rights because the item was on sale is void.']:
            self.assertIsNotNone(source_qualification_failure(text,s))
        self.assertIsNone(source_qualification_failure('The article declares stipulations contrary to its provisions null and void, without deciding the promotion terms.',s))

    def test_wrong_delivery_does_not_prove_no_consumer_fault(self):
        s=self.sources['RA_11967_2023__sec_20']
        self.assertIsNotNone(source_qualification_failure('If the delivered model is different, that is a nonconformity that is not your fault.',s))
        self.assertIsNone(source_qualification_failure('For a nonconformity through no fault of the consumer, the recorded remedy conditions apply.',s))

    def test_only_internal_trailing_selection_markup_is_removed(self):
        comp=[{'component_id':'concern_001','sources':[{'chunk_id':'s1','parent_text':'The provision records a source condition.'}]}]
        _,lookup=source_options(comp);qid=next(iter(lookup))
        draft={'paragraphs':[{'component_id':'concern_001','text':f'The source describes this condition. ({qid})','evidence':[{'quote_id':qid}]}]}
        fixed=selected_draft(draft,lookup)
        self.assertEqual(fixed['paragraphs'][0]['text'],'The source describes this condition.')
        self.assertTrue(draft['paragraphs'][0]['text'].endswith(')'))
        draft['paragraphs'][0]['text']='The provision records this condition (see q1-q3). The source is inspectable (Art. 300).'
        self.assertEqual(selected_draft(draft,lookup)['paragraphs'][0]['text'],'The provision records this condition. The source is inspectable (Art. 300).')


class ProviderBudgetTests(unittest.TestCase):
    def request(self):
        return Request('https://api.together.ai/v1/chat/completions',data=json.dumps({'model':'openai/gpt-oss-120b','max_tokens':10}).encode(),method='POST')

    def test_no_new_export_when_only_finalization_time_remains(self):
        ctx=RequestContext('test','budget',deadline=104);ledger=Mock()
        with patch('backend.application.controls.time.monotonic',return_value=100):
            with self.assertRaises(ProviderStopped) as error:CancellableTransport(ctx,ledger,'generation')(self.request(),20)
        self.assertEqual(error.exception.safe_code,'provider_time_budget_exhausted')
        ledger.reserve.assert_not_called()

    def test_provider_cutoff_keeps_the_outer_context_alive(self):
        ctx=RequestContext('test','budget',deadline=160);ledger=Mock();ledger.reserve.return_value='reserved'
        conn=Mock();conn.getresponse.return_value.status=200
        with patch('backend.application.controls.time.monotonic',return_value=100) as clock, patch('backend.application.controls.http.client.HTTPSConnection',return_value=conn):
            def timeout(*args):clock.return_value=156;raise TimeoutError()
            conn.getresponse.return_value.read.side_effect=timeout
            with self.assertRaises(ProviderStopped) as error:CancellableTransport(ctx,ledger,'generation')(self.request(),20)
            self.assertEqual(error.exception.safe_code,'provider_time_budget_exhausted')
            ctx.check()  # Local source fallback can still finish before 160.
        conn.close.assert_called_once();ledger.settle.assert_called_once()


if __name__=='__main__':unittest.main()
