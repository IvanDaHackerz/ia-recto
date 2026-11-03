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

    def test_probation_temporal_detail_and_product_operation_stay_with_their_scenarios(self):
        from clause_classifier import segment_question
        samples=[
            ('Probationary ako sa private office. Ngayong patapos na saka lang nila sinabi yung standards na kailangan ma-meet. How does the rule handle that?','labor'),
            ('I bought a new desk fan from an appliance shop. It worked once and then stopped. The shop says it will only repair it and will never consider replacement or refund. What does the rule actually allow?','consumer'),
            ('Sabi ng gadget store brand new yung phone, pero refurbished pala. What does the Consumer Act say about selling something used as new?','consumer')]
        for text,label in samples:
            with self.subTest(text=text):
                self.check(text,label)
                a=segment_question(text)
                self.assertEqual(len(a['components']),1)
                self.assertTrue(a['all_fragments_accounted_for'])
                self.assertTrue(all(f['component_index']==0 for f in a['fragments']))
        self.check('Probationary ako sa government office. Ngayong patapos na saka lang nila sinabi ang standards. What civil-service rule applies?','out_of_scope','unsupported')

    def test_context_and_same_seller_followup_do_not_create_extra_concerns(self):
        from clause_classifier import segment_question
        for text in [
            'sa private printing company kami. isang beses lang kada month nagbibigay sahod. tama ba yung pagitan ng payday namin?',
            'A private office closed for a regular holiday. The staff were told that no work means no pay. Is that the general rule?',
            'may warranty card ako sa bagong microwave. ayaw tanggapin ng retailer yung complaint ko, sa supplier daw ako dumiretso. ano responsibility ng retailer?',
            'I ordered a red school bag from a Philippine online seller and got a different model. If I ask for a replacement, who pays to return the wrong item?']:
            with self.subTest(text=text):
                a=segment_question(text)
                self.assertEqual(len(a['components']),1)
                self.assertTrue(a['all_fragments_accounted_for'])
        intro=segment_question('Sa private printing company kami. Delayed ang sahod.')
        self.assertEqual(intro['fragments'][0]['role'],'background')
        self.assertEqual(len(intro['components']),1)
        self.assertIn('private employment',intro['components'][0])

    def test_scoped_meta_followup_retains_the_excluded_concern_and_targets_the_right_part(self):
        from clause_classifier import segment_question
        text='An online store sent a faulty rice cooker. Separately, a neighbor published my personal information. Please explain the purchase issue and tell me where your scope ends.'
        a=segment_question(text)
        self.assertEqual(len(a['components']),2)
        self.assertEqual(a['fragments'][-1]['component_index'],0)
        self.assertIn('personal information',a['components'][1])
        self.check(text,'mixed','partially_supported')

    def test_temporal_and_product_repairs_keep_independent_actors_and_topic_exclusions(self):
        self.check('Probationary ako sa private office. Saka may bank account fee akong gustong i-dispute.','mixed','partially_supported')
        self.check('A store sold me a refurbished phone as brand new. Separately, I need help with my phone subscription bill.','mixed','partially_supported')
        self.check('A store sold me a refurbished phone as brand new. My private employer has not paid overtime.','mixed')
        self.check('I worked at a private store. My only concern is my bank account interest charge.','out_of_scope','unsupported')
        from clause_classifier import segment_question
        a=segment_question('My private employer delayed wages. A different private employer dismissed me.')
        self.assertEqual(len(a['components']),2)

    def test_background_only_or_unspecified_standards_need_clarification(self):
        for text in ['Sa private printing company kami.', 'Probationary ako sa private office.',
                     'They did not follow the standards. What can I do?']:
            with self.subTest(text=text):
                p=predict_records(self.bundle,[{'question_text':text}])[0]
                self.assertEqual(p['routing_action'],'clarify')
                self.assertFalse(p['substantive_answer_admitted'])

    def test_transaction_replies_and_product_features_remain_with_the_purchase(self):
        from clause_classifier import segment_question
        for text in [
            'I bought a toaster from a local shop. It worked yesterday and stopped today. The seller refuses to discuss a replacement. What rule covers this?',
            'Bagong bili yung blender ko sa appliance store. Gumagana nung una, tapos ayaw na. What consumer rules apply?',
            'May warranty card yung bagong washing machine ko. The retailer says I should complain directly to the distributor. What does the warranty rule say?',
            'An online shop delivered the wrong lamp model. The delivered unit has different features. What consumer rules should I inspect?']:
            with self.subTest(text=text):
                self.check(text,'consumer')
                a=segment_question(text)
                self.assertEqual(len(a['components']),1)
                self.assertTrue(a['all_fragments_accounted_for'])
        separate=segment_question('One shop sold me a faulty kettle. A different shop kept my cash change. Please explain each purchase issue.')
        self.assertEqual(len(separate['components']),2)

    def test_negated_government_category_is_never_propagated_to_private_concerns(self):
        from clause_classifier import segment_question
        text='Sa private hotel ako. Hindi binayaran ang overtime, pero hindi ito government employment. What overtime rule applies?'
        self.check(text,'labor')
        a=segment_question(text)
        self.assertEqual(len(a['components']),1)
        self.assertTrue(any(f['role']=='background' and 'government' in f['text'] for f in a['fragments']))
        self.assertTrue(all('government employment:' not in c for c in a['components']))
        self.check('Probationary ako sa government office. Saka lang nila sinabi ang standards. What civil-service procedure applies?','out_of_scope','unsupported')

    def test_seafarer_category_survives_a_generic_overseas_assignment_followup(self):
        self.check('Seafarer ako. My question is about the employment terms for my overseas vessel assignment.','out_of_scope','unsupported')
        self.check('Seafarer ako. My employer has not paid my overseas wages.','out_of_scope','unsupported')
        self.check('Seafarer ako. A local shop sold me a broken kettle.','consumer')
        self.check('I am a seafarer disputing vessel employment terms. A local shop also refuses my warranty.','mixed','partially_supported')
        from scope_constraints import employment_background
        for text in ['I am a seafarer disputing vessel employment terms.',
                     'I am an OFW asking about employment terms.',
                     'I work for a private employer and need help with my rights.']:
            with self.subTest(text=text):self.assertFalse(employment_background(text))

    def test_misspelled_anaphoric_dispute_request_and_personal_work_history_are_not_new_issues(self):
        from clause_classifier import segment_question
        text='A shop turned down my applianceee waaarranty claim. Separately, my home insurer deeenied a claaaim under my insurance policy. How do I raise each disputtte?'
        self.check(text,'mixed','partially_supported')
        a=segment_question(text)
        self.assertEqual(len(a['components']),2)
        self.assertEqual(a['fragments'][-1]['role'],'follow_up')
        history='Five months lang ako sa company bago nagresign. May explanation ba kayo tungkol sa prorated 13th month?'
        a=segment_question(history)
        self.assertEqual(len(a['components']),1)
        self.assertEqual(a['fragments'][0]['role'],'preface')
        self.check(history,'labor')

    def test_unrelated_means_separate_concern_not_discardable_history(self):
        self.check('My private employer has not paid wages. An unrelated shop delivered the wrong model of lamp.','mixed')
        self.check('Private employee ako na walang overtime pay. Unrelated, may sira ang binili kong fan sa shop.','mixed')
        self.check('I was stabbed ten years ago. My private employer has not paid overtime.','labor')

    def test_comma_enumeration_preserves_supported_and_excluded_parts(self):
        from clause_classifier import segment_question
        text='My private employer withheld salary, a separate shop kept my cash change, and I want criminal-case advice.'
        self.check(text,'mixed','partially_supported')
        self.assertEqual(len(segment_question(text)['components']),3)
        self.check('Pribadong factory worker ako na walang overtime. Hiwalay ang mana ng lupa naming magkapatid.','mixed','partially_supported')

    def test_scope_specific_paraphrases_keep_actor_and_topic(self):
        for text,primary,scope in [
            ('A private manufacturer dismissed me without allowing me to answer.','labor','fully_supported'),
            ('Our private repair shop marked the regular holiday unpaid.','labor','fully_supported'),
            ('I am employed by a household in Hong Kong. My employer owes wages.','out_of_scope','unsupported'),
            ('My online business needs an exact tax computation to file with the BIR.','out_of_scope','unsupported'),
            ('A neighbor uploaded screenshots of our private conversation.','out_of_scope','unsupported'),
            ('Recommend fertilizer for my balcony tomato plant.','out_of_scope','unsupported'),
        ]:
            with self.subTest(text=text):self.check(text,primary,scope)

    def test_same_service_and_coordinate_subject_are_not_duplicate_concerns(self):
        from clause_classifier import segment_question
        for text in [
            'A local seller and I disagree about a faulty desk lamp. What consumer rule applies?',
            'Our private employer pays wages every six weeks. Which rule deals with how often wages are paid?',
            'A paid laundry service damaged my coat. What rules cover defective services?',
        ]:
            with self.subTest(text=text):self.assertEqual(len(segment_question(text)['components']),1)

    def test_schedule_background_and_online_anaphora_keep_the_whole_scenario(self):
        from clause_classifier import segment_question
        for text in [
            'Sa private hotel ako, 10pm to 6am duty. Walang night differential sa payslip. Ano ang recorded rule?',
            'An online merchant sent the wrong model. Explain the recorded remedy after choosing replacement or refund.',
            'A new lamp from a neighborhood store stopped charging. What product-imperfection conditions apply?',
        ]:
            with self.subTest(text=text):self.assertEqual(len(segment_question(text)['components']),1)
        self.check('My private employer at a fertilizer plant has not paid wages.','labor')

    def test_scenario_context_and_exclusive_requests(self):
        from clause_classifier import segment_question
        from typing_repair import matching_text
        self.check('OFW ako working for an employer in Saudi Arabia. Delayed ang overseas salary ko. What overseas labor process should I follow?','out_of_scope','unsupported')
        self.check('What is the exact current regional minimum wage? I want the current rate, not general wage-payment rules.','out_of_scope','unsupported')
        self.check('My private employer dismissed me. I only want you to predict whether I will win my case.','out_of_scope','unsupported')
        self.check('My private employer deducted equipment damage from my wages. My bank also charged an account fee.','mixed','partially_supported')
        for text in ['contractor','production','distributor','worker']:
            self.assertEqual(matching_text(text),text)
        audit=segment_question('A private distributor is abolishing jobs because of redundancy. The affected workers were told verbally to stop coming tomorrow. What written notice applies?')
        self.assertEqual(len(audit['components']),1)
        self.assertTrue(audit['all_fragments_accounted_for'])

    def test_normal_demo_followups_do_not_duplicate_their_scenario(self):
        from clause_classifier import segment_question
        for text in [
            'I work for a private packaging business and finish ten hours on an ordinary weekday. What general overtime rule applies to covered workers?',
            'Probationary employee ako sa private office. Wala silang sinabi na standards noong hiring. What does the probation rule require about those standards?',
            'I ordered a desk lamp from an online merchant but received a different model. What recorded consumer remedy framework can be described?',
            'A newly bought electric kettle sparks near its handle during normal use. What recorded product-safety framework applies without deciding anyone is already liable?',
        ]:
            with self.subTest(text=text):
                audit=segment_question(text)
                self.assertEqual(len(audit['components']),1)
                self.assertTrue(audit['all_fragments_accounted_for'])

    def test_job_setup_and_followup_are_one_concern_without_losing_facts(self):
        from clause_classifier import segment_question
        for text in [
            'Crew ako sa private bakery sa Quezon City. Sabi ng may-ari isang bagsakang sahod lang tuwing katapusan. Ano ang general rule sa pagitan ng mga payday?',
            'The payroll of our private printing business is late. The manager says customers have not paid yet. What wage-payment framework should workers inspect?',
            'Sa private farm ako. Seasonal daw ang trabaho namin. Explain the seasonal exception in the employment-status rule.',
            'A private hotel dismissed a receptionist. The worker was given no chance to explain. What procedural safeguards can be described generally?',
        ]:
            with self.subTest(text=text):
                self.check(text,'labor')
                audit=segment_question(text)
                self.assertEqual(len(audit['components']),1)
                self.assertTrue(audit['all_fragments_accounted_for'])

    def test_scope_boundaries_survive_public_job_and_privacy_paraphrases(self):
        self.check('Government overtime pay ang concern ko.','out_of_scope','unsupported')
        self.check('Private employee ako at hindi government employee. Hindi binayaran overtime ko.','labor')
        self.check('I am a government clerk disputing my employment overtime. A retail store sold me a broken rice cooker.','mixed','partially_supported')
        self.check('My only concern is the personal-data breach, not a product purchase.','out_of_scope','unsupported')
        self.check('What is the exact current minimum daily wage in Region IV-A?','out_of_scope','unsupported')

    def test_ambiguous_distinct_contract_is_not_silently_dropped(self):
        p=predict_records(self.bundle,[{'question_text':'My private construction contract never identifies the alleged project. A separate furniture store also advertised hardwood but supplied particle board.'}])[0]
        self.assertEqual(p['routing_action'],'clarify')
        self.assertEqual(p['reason'],'unresolved_component_scope')
        self.assertEqual(len(p['component_evidence']),2)

    def test_product_safety_and_prediction_intent_remain_distinct(self):
        self.check('A newly bought power strip overheated and scorched a desk. What recorded product-safety framework can you explain?','consumer')
        self.check('My private employer dismissed me. Can you guarantee whether I will win and how much the tribunal will award me?','out_of_scope','unsupported')
        self.check('My private employer dismissed me. What general due-process rules are recorded?','labor')

    def test_polite_and_taglish_rule_questions_keep_the_scenario(self):
        from clause_classifier import segment_question
        for text in [
            'Private grocery staff ako. Eleven days straight ang schedule ko na walang buong araw na pahinga. What weekly rest rule can you explain?',
            'For a private construction employer, what needs to be identified when a worker is hired for a particular project? I want the general employment framework.',
            'A retail seller delivered a dining table with one leg missing. Please explain the product-quality framework without promising an immediate refund.',
            'I ordered the wrong color myself from an ordinary online retailer and want to change my order. Please distinguish a change of mind from delivery of a nonconforming item.',
            'May unpaid salary concern ako sa private repair shop. Ano ang purpose ng SEnA conciliation, at may decision na ba agad doon?',
        ]:
            with self.subTest(text=text):
                self.assertEqual(len(segment_question(text)['components']),1)
                self.assertTrue(segment_question(text)['all_fragments_accounted_for'])

    def test_an_employer_complaint_is_not_an_actor_introduction(self):
        from clause_classifier import segment_question
        from scope_constraints import employment_background
        for issue in ['My private employer deducts inventory losses from everyone.',
                      'My private employer says missing cash will be divided equally among everyone on duty.',
                      'Private shop employee ako asking about weekly rest.']:
            with self.subTest(issue=issue):
                self.assertFalse(employment_background(issue))
                self.check(issue,'labor')
                self.check(issue+' I also bought a defective kettle from a shop.','mixed')
                self.assertEqual(len(segment_question(issue+' I also bought a defective kettle from a shop.')['components']),2)

    def test_new_actor_and_excluded_issue_survive_followup_grouping(self):
        from clause_classifier import segment_question
        self.check('My private employer deducts inventory losses. My bank also deducted a service fee.','mixed','partially_supported')
        self.check('I want to sue a doctor over a medical procedure. This is not an ordinary retail purchase.','out_of_scope','unsupported')
        self.check('The shop sold a defective fan. This is an ordinary retail purchase.','consumer')
        text='Online retail purchase ito. The merchant wants me to pay shipping to return the wrong item. What does the recorded return rule say?'
        self.check(text,'consumer')
        self.assertEqual(len(segment_question(text)['components']),1)

    def test_general_ending_does_not_create_an_extra_concern(self):
        from clause_classifier import segment_question
        text='Private employee ako with missing holiday pay. My online retailer also sent the wrong product. I want separate source-based information.'
        self.check(text,'mixed')
        self.assertEqual(len(segment_question(text)['components']),2)
        deductions='My private employer says missing cash in the till will be divided among everyone. What conditions apply to deductions?'
        self.check(deductions,'labor')
        self.assertEqual(len(segment_question(deductions)['components']),1)

    def test_negated_bank_fee_is_background_but_a_real_fee_remains_excluded(self):
        self.check('Private employee ako. May payroll issue: hindi pa pumapasok yung sahod namin. Bank transfer lang yung payment method, hindi bank fees ang reklamo ko.','labor')
        self.check('My private employer has not paid my wages. My bank separately charged a transfer fee.','mixed','partially_supported')

    def test_three_explicit_scopes_use_scope_rules_without_faking_probabilities(self):
        import copy
        from classifier_runtime import route_prediction
        text='Private employee ako with unpaid wages. A store also sold me a defective fan, and my landlord kept my deposit.'
        p=predict_records(self.bundle,[{'question_text':text}])[0]
        self.assertEqual(p['routing_action'],'retrieve_supported_components')
        self.assertEqual(p['predicted_scope'],'partially_supported')
        self.assertEqual({r['allowed_domain'] for r in p['retrieval_requests']},{'labor','consumer'})
        self.assertEqual(len(p['excluded_components']),1)
        self.assertLess(p['scope_confidence'],self.bundle['thresholds']['scope'])
        learned=copy.deepcopy(p);learned['component_evidence'][0]['decision_source']='learned_atomic_classifier'
        learned['component_evidence'][0]['constraint']=None
        self.assertEqual(route_prediction(learned,self.bundle['thresholds'])['routing_action'],'clarify')
        self.check('I have a private-sector dismissal concern, and a retailer refuses to receive my written warranty claim. Which parts can this project handle?','mixed')

    def test_same_scenario_question_and_native_introduction_stay_together(self):
        from clause_classifier import segment_question
        for text in [
            'My private employer has missed several paydays. What wage-payment rules can you explain?',
            'Sa private factory ako. May bawas sa sahod para sa tools. Anong wage deduction rules ang relevant?',
            'My private employer says a monthly salary covers all extra hours. What overtime information is available?',
            'Sa private warehouse, required kami mag-inspect ng equipment bago magsimula ang paid shift. Counted ba as working time yung required inspection?',
            'Private factory employee ako. Tinanggal agad bago ako nakapagpaliwanag. What recorded due-process rules can you describe?',
        ]:
            with self.subTest(text=text):
                self.assertEqual(len(segment_question(text)['components']),1)
                self.check(text,'labor')

    def test_consumer_framework_and_native_negation_are_not_extra_scopes(self):
        self.check('Bumibili ako ng ordinary goods from retailers. Explain the general Consumer Act framework and the policy interests it protects.','consumer')
        self.check('Yung bagong blender galing sa retailer has a broken motor. Hindi ito insurance or repair-service issue; defective product ang concern ko.','consumer')
        self.check('The retailer sold a defective fan. Hindi binayaran ng insurance ang separate claim ko.','mixed','partially_supported')

    def test_generic_follow_up_and_plural_topics_do_not_create_duplicate_concerns(self):
        from clause_classifier import segment_question
        for text in [
            'Our private employer changes the weekly rest day. Is there information on scheduling rest days?',
            'The shop sold me a cracked toaster. What consumer defect rules can you explain?',
            'The private company calls my job project-based. What employment-contract information is available?',
            'Mas mataas ang singil sa checkout kaysa price tag ng appliance. Anong recorded consumer rule ang relevant?',
        ]:
            with self.subTest(text=text):self.assertEqual(len(segment_question(text)['components']),1)
        both='My private employer withheld my wages. A store advertisement misstates a speaker feature. Explain the employment and consumer information separately.'
        self.assertEqual(len(segment_question(both)['components']),2)
        self.check(both,'mixed')

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

    def test_native_job_introduction_is_background_not_a_purchase(self):
        self.check('Cashier ako sa supermarket. May salary deduction kami pag kulang ang kaha.','labor')
        self.check('The supermarket cashier charged me more than the shelf price.','consumer')

    def test_purchase_role_and_employer_role_remain_distinct(self):
        self.check('The private company that sold me a refrigerator refuses a refund for a defective unit.','consumer')
        self.check('My private employer gave me a gift card. I used it at a store and the store sold me a broken fan.','consumer')
        self.check('I work for a private telecom company. My question is about unpaid overtime, not my phone bill.','labor')
        self.check('My telecom provider incorrectly billed my phone plan.','out_of_scope','unsupported')

    def test_natural_sale_and_native_safety_wording(self):
        for text in ['A salesperson told me a secondhand phone was brand new and I bought it based on that claim.',
                     'May exposed wire yung bagong extension cord sa hardware. Unsafe consumer product ba ito?',
                     'Yung bagong electric fan galing sa appliance shop amoy sunog agad nung sinaksak.',
                     'A retail store displays no prices on any of its household goods.']:
            with self.subTest(text=text):self.check(text,'consumer')

    def test_special_job_categories_and_hyphenated_rate_are_not_admitted(self):
        for text in ['Public school teacher ako. May issue ako sa government salary deductions ko.',
                     'Yaya ako ng bata sa bahay ng isang pamilya, walang day off na binibigay.',
                     'Domestic helper ako sa bahay ng employer at hindi binabayaran nang tama.',
                     'What is the exact minimum-wage rate in my city today?']:
            with self.subTest(text=text):self.check(text,'out_of_scope','unsupported')

    def test_background_trip_to_collect_salary_is_not_a_wage_claim(self):
        self.check('Someone stole my bag while I was heading to collect my salary.','out_of_scope','unsupported')

    def test_vague_pay_and_help_requests_require_detail(self):
        for text in ['I paid but nothing happened.','Hindi ko alam paano ito ayusin.',
                     'Ayaw niya ako bayaran pero di ko alam anong details kailangan.',
                     'Can I ask about something that happened yesterday?']:
            with self.subTest(text=text):
                p=predict_records(self.bundle,[{'question_text':text}])[0]
                self.assertEqual(p['routing_action'],'clarify')
        self.check('A paid shoe-cleaning service damaged my shoes instead of cleaning them.','consumer')
        self.check('Our private office closed for a regular holiday, but payroll marked it unpaid. Should I still have been paid for that day?','labor')

    def test_phone_product_and_separate_network_concern_stay_partial(self):
        self.check('The store sold me a defective phone; the mobile network also charged an unauthorized data-plan fee.','mixed','partially_supported')
        from typing_repair import matching_text
        self.assertEqual(matching_text('network'),'network')

    def test_explicit_request_conjunction_preserves_both_scopes(self):
        self.check('I need general wage-payment rules for my private job and help with my pending NLRC case.','mixed','partially_supported')
        self.check('The private store dismissed me without notice. What are my chances of winning the pending NLRC case?','mixed','partially_supported')

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
        pay='Our private office closed for a regular holiday, but payroll marked it unpaid. Should I still have been paid for that day?'
        self.assertEqual(len(segment_question(pay)['components']),1)
        self.check(pay,'labor')

    def test_rule_follow_up_does_not_absorb_new_topics_or_facts(self):
        from clause_classifier import segment_question
        for follow in ['What overtime-pay rules and exceptions apply?', 'What divorce rules apply?',
                       'My government employer also withheld my holiday pay.',
                       'What holiday-pay rules apply to government workers?']:
            with self.subTest(follow=follow):
                audit=segment_question('My private employer withheld my Christmas holiday pay. '+follow)
                self.assertGreaterEqual(len(audit['components']),2)
