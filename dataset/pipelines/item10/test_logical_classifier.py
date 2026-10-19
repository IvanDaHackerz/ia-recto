"""Leakage, persistence, confidence, and consequential scope-routing regressions.

Counterfactual cases here are AI-authored development tests, not independent gold.
"""
from __future__ import annotations
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(k,'1')
import argparse,json,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import joblib
from sklearn.base import clone
from classifier_runtime import predict_records,route,route_prediction,missing_context,VALID_PAIRS
from clause_classifier import split_clauses,segment_question,state_of,training_atoms,deduplicate
from logical_clause_model import fact_texts,normalized_fact,decoded_state
from train_classifier import sources,readrows,sha,ROOT,gates,evaluate,select_thresholds,save
RUN=None

REGRESSIONS=[
 ('labor','fully_supported','A private manufacturer withheld my overtime pay.'),
 ('out_of_scope','unsupported','A municipal employer withheld my overtime pay.'),
 ('consumer','fully_supported','The phone I bought from a retail shop broke and the seller refuses its warranty.'),
 ('out_of_scope','unsupported','My mobile phone plan has a disputed service charge.'),
 ('consumer','fully_supported','An appliance store charged me for an electric fan repair that was never done.'),
 ('out_of_scope','unsupported','My electricity provider charged me twice on my utility bill.'),
 ('labor','fully_supported','How are minimum wage orders issued for private-sector workers?'),
 ('out_of_scope','unsupported','How much is the exact minimum wage in my region now?'),
 ('out_of_scope','unsupported','I am employed by a private company. Please calculate my SSS pension.'),
 ('consumer','fully_supported','DTI referred my consumer complaint to a government office.'),
 ('labor','fully_supported','I am not a government employee; my private employer delayed my salary.'),
 ('consumer','fully_supported','A shop did not deliver my paid order. I want a refund.'),
 ('mixed','partially_supported','A store refuses my blender warranty. Separately it published my home address online.'),
 ('out_of_scope','unsupported','A fake online store disappeared with my money. I want a criminal investigation.'),
 ('out_of_scope','unsupported','I am an overseas seafarer. The employer withheld my wages.'),
 ('mixed','fully_supported','My private employer owes overtime pay. The retailer refuses to repair my defective toaster.'),
 ('mixed','partially_supported','My private employer owes wages. A bank also froze my savings account.'),
 ('out_of_scope','unsupported','My government employer denied my holiday pay.'),
 ('consumer','fully_supported','A retail store sold me a private desk with a broken leg.'),
]

class LogicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=joblib.load(RUN/'classifier.joblib');cls.parts,cls.general,cls.typing,cls.audit=sources();cls.engine=cls.b['primary_model'].engine
        cls.policy=json.loads((RUN/'policy_snapshot.json').read_text());cls.manifest=json.loads((RUN/'run_manifest.json').read_text())
    def prediction(self,text):return predict_records(self.b,[{'question_text':text}])[0]
    def test_investigation_is_not_investment(self):
        from scope_constraints import constraint
        for text in ['A consumer requests investigation of a store transaction.',
                     'Gusto ko ma-investigate ang store complaint.',
                     'The investigator is examining a retail complaint.']:
            rule=constraint(text)
            self.assertFalse(rule and rule[1]=='consumer.investments',text)
        for text in ['My investment fund is frozen.','I invested in securities.',
                     'Nag-invest ako sa fund.','I want to invest money.']:
            self.assertEqual(constraint(text),('excluded','consumer.investments'))
    def test_household_repair_does_not_create_domestic_employment(self):
        p=self.prediction('A paid household repair service was improperly done.')
        self.assertEqual(p['predicted_primary'],'consumer')
        self.assertFalse(any('kasambahay employment:' in c['text'] for c in p['component_evidence']))
    def test_private_shop_is_not_private_employment(self):
        from scope_constraints import constraint
        self.assertEqual(constraint('A private shop charged a repair fee.')[0],'consumer')
        self.assertEqual(constraint('My private employer charged a uniform fee.')[0],'labor')
    def test_sena_procedure_does_not_override_case_strategy_exclusions(self):
        from scope_constraints import constraint
        self.assertEqual(constraint('What is the SEnA procedure?')[0],'labor')
        self.assertEqual(constraint('Will I win at SEnA?')[0],'excluded')
    def test_criminal_investigation_has_correct_exclusion(self):
        from scope_constraints import constraint
        self.assertEqual(constraint('I want a criminal cyberfraud investigation of a fake store.'),
                         ('excluded','consumer.criminal_online_fraud'))
    def test_service_quality_constraint_preserves_regulated_boundaries(self):
        from scope_constraints import constraint
        self.assertEqual(constraint('A service supplier performed flawed work.')[0],'consumer')
        self.assertEqual(constraint('A medical service provider performed defective work.')[0],'excluded')
        self.assertEqual(constraint('My telecom service provider performed defective work.')[0],'excluded')
        self.assertIsNone(constraint('A service provider has a problem.'))
    def test_regulated_provider_context_does_not_request_another_provider(self):
        self.assertIsNone(missing_context('A public transport operator charged an improper fare.'))
        self.assertIsNone(missing_context('My recruitment agency charged deployment fees.'))
        self.assertIsNotNone(missing_context('Someone charged me extra.'))
    def test_source_checksums_and_group_partitions(self):
        self.assertEqual(self.audit['status'],'passed');self.assertEqual(self.audit['leakage_groups_crossing_partitions'],0)
    def test_training_membership_excludes_every_evaluation_partition(self):
        expected={r['question_id'] for r in self.parts['train']};self.assertEqual(set(self.b['train_question_ids']),expected)
        self.assertFalse(expected&{r['question_id'] for r in self.parts['validation']+self.parts['test']+self.general+self.typing})
    def test_fitting_texts_and_targets_are_training_only(self):
        estimator=self.engine.joint_model.calibrated_classifiers_[0].estimator
        self.assertEqual(set(estimator.fit_parent_texts_),{r['question_text'] for r in self.parts['train']})
        self.assertEqual({decoded_state(c) for c in estimator.classes_},{state_of(r) for r in self.parts['train']})
    def test_grouped_calibration_covers_every_parent_once(self):
        seen=set();expected=set(self.b['train_group_ids']);n=0
        for f in readrows_json(RUN/'calibration_folds.json'):
            fit=set(f['fit_group_ids']);held=set(f['calibration_group_ids']);self.assertFalse(fit&held);self.assertFalse(seen&held);self.assertEqual(fit|held,expected);seen|=held;n+=f['calibration_rows']
        self.assertEqual(seen,expected);self.assertEqual(n,459)
    def test_purged_atomic_facts_reconstruct_without_held_labels(self):
        byid={r['question_id']:r for r in self.parts['train']}
        for f in readrows_json(RUN/'calibration_folds.json'):
            forbidden={normalized_fact(t) for q in f['held_parent_ids'] for t in fact_texts(byid[q]['question_text'])}
            atoms=[a for q in f['fit_parent_ids'] for a in training_atoms(byid[q])];kept=[a for a in atoms if normalized_fact(a['text']) not in forbidden]
            self.assertEqual(len(atoms)-len(kept),f['shared_atomic_fact_rows_purged']);self.assertFalse({normalized_fact(a['text']) for a in kept}&forbidden)
    def test_vectorizer_idf_rebuild_uses_only_atomic_training_sources(self):
        atomic=self.engine.atomic
        if atomic.lexical is None:self.skipTest('semantic candidate has no lexical vectorizer')
        texts=[a['text'] for a in atomic.atoms]
        for _,v in atomic.lexical.transformer_list:
            ref=clone(v).fit(texts);self.assertEqual(v.vocabulary_,ref.vocabulary_);np.testing.assert_allclose(v.idf_,ref.idf_,atol=1e-12)
    def test_final_atomic_sources_match_training_and_taxonomy(self):
        expected=readrows(RUN/'unique_training_atoms.jsonl')
        self.assertEqual({a['normalized_fact'] for a in expected},{a['normalized_fact'] for a in self.engine.atomic.atoms})
        self.assertEqual(len(readrows(RUN/'taxonomy_training_glossary.jsonl')),42)
    def test_calibration_reproduces_saved_probabilities(self):
        model=clone(self.engine.joint_model);texts=[r['question_text'] for r in self.parts['train']];y=[state_of(r) for r in self.parts['train']]
        model.fit(texts,y);val=[r['question_text'] for r in self.parts['validation']];np.testing.assert_allclose(model.predict_proba(val),self.engine.joint_model.predict_proba(val),atol=1e-10)
    def test_saved_model_replays_all_development_predictions(self):
        for name,rows in [('validation',self.parts['validation']),('ai_general_development',self.general),('ai_typing_development',self.typing)]:
            actual=predict_records(self.b,rows);expected=readrows(RUN/(name+'_predictions.jsonl'))
            for a,b in zip(actual,expected):
                for field in ('predicted_primary','predicted_scope','routing_action','reason'):self.assertEqual(a[field],b[field])
                for head in ('primary','scope'):np.testing.assert_allclose(list(a[head+'_probabilities'].values()),list(b[head+'_probabilities'].values()),atol=1e-12)
    def test_probability_vectors_and_chosen_label_confidence(self):
        for p in predict_records(self.b,self.general+self.typing):
            for head in ('primary','scope'):
                values=np.array(list(p[head+'_probabilities'].values()));self.assertTrue(np.isfinite(values).all());self.assertTrue(((values>=0)&(values<=1)).all());self.assertAlmostEqual(values.sum(),1,places=10)
                self.assertEqual(p[head+'_confidence'],p[head+'_probabilities'][p['predicted_'+head]])
    def test_primary_and_scope_always_coherent(self):
        for p in predict_records(self.b,self.general+self.typing):self.assertIn((p['predicted_primary'],p['predicted_scope']),VALID_PAIRS)
    def test_label_metadata_cannot_change_predictions(self):
        t=self.general[0]['question_text'];a=predict_records(self.b,[{'question_text':t,'primary_label':'labor'}])[0];b=predict_records(self.b,[{'question_text':t,'primary_label':'out_of_scope','supported_topic_ids':['fake']}])[0]
        self.assertEqual(a['primary_probabilities'],b['primary_probabilities']);self.assertEqual(a['scope_probabilities'],b['scope_probabilities'])
    def test_missing_context_precedes_model_uncertainty(self):
        cases=[('My employer has not paid my salary.','employment_category_missing'),('They refuse to refund my payment.','refund_transaction_missing'),('They ended my contract.','contract_relationship_missing'),('They charged me too much.','charge_context_missing')]
        for t,reason in cases:
            p={'question_text':t,'predicted_primary':'out_of_scope','predicted_scope':'unsupported','primary_confidence':.999,'scope_confidence':.999,'has_reliable_component_evidence':False}
            r=route_prediction(p,{'primary':0.,'scope':0.});self.assertEqual(r['reason'],reason);self.assertFalse(r['substantive_answer_admitted'])
    def test_invalid_label_pairs_cannot_admit(self):
        r=route('A retail store sold a defective fan.','consumer','unsupported',1.,1.,{'primary':0.,'scope':0.});self.assertEqual(r['reason'],'inconsistent_primary_scope');self.assertFalse(r['substantive_answer_admitted'])
    def test_confidence_thresholds_cannot_be_bypassed(self):
        p=self.prediction('My private employer owes wages. A store refuses my kettle warranty.');r=route_prediction(p,{'primary':1.01,'scope':1.01});self.assertEqual(r['routing_action'],'clarify');self.assertFalse(r['substantive_answer_admitted'])
    def test_supported_and_excluded_components_never_share_queries(self):
        p=self.prediction('A store refuses my blender warranty. Separately it published my home address online.')
        self.assertEqual(p['routing_action'],'retrieve_supported_components');self.assertEqual(len(p['retrieval_requests']),1);self.assertEqual(len(p['excluded_components']),1)
        for q in p['retrieval_requests']:self.assertNotIn('address',q['query']);self.assertEqual(q['allowed_domain'],'consumer');self.assertTrue(q['requires_answer_eligible_evidence'])
        self.assertFalse(p['excluded_components'][0]['retrieval_allowed'])
    def test_repeated_concern_cannot_create_second_domain(self):
        t='My private employer withheld my overtime pay.';a=self.prediction(t);b=self.prediction(t+' '+t)
        self.assertEqual((a['predicted_primary'],a['predicted_scope']),(b['predicted_primary'],b['predicted_scope']))
    def test_joined_taglish_complaints_keep_labor_and_exclude_landlord(self):
        labor='hindi binayaran ang overtime ko';excluded='ayaw ibalik ng landlord ang rental deposit'
        for connector in ['at','and','pero','but']:
            for first,second in [(labor,excluded),(excluded,labor)]:
                text='Private employee ako. '+first+' '+connector+' '+second+'.'
                with self.subTest(text=text):
                    p=self.prediction(text)
                    self.assertEqual((p['predicted_primary'],p['predicted_scope']),('mixed','partially_supported'))
                    self.assertEqual(p['routing_action'],'retrieve_supported_components')
                    self.assertEqual(len(p['retrieval_requests']),1)
                    self.assertEqual(p['retrieval_requests'][0]['allowed_domain'],'labor')
                    self.assertIn('overtime',p['retrieval_requests'][0]['query'])
                    self.assertNotIn('landlord',p['retrieval_requests'][0]['query'])
                    self.assertNotIn('deposit',p['retrieval_requests'][0]['query'])
                    self.assertEqual(p['excluded_components'][0]['constraint_topic'],'consumer.real_estate')
                    self.assertFalse(p['excluded_components'][0]['retrieval_allowed'])
                    self.assertTrue(p['segmentation_audit']['all_fragments_accounted_for'])
    def test_joined_english_predicate_keeps_both_concerns(self):
        text='My private employer owes wages and will not return my rental deposit as my landlord.'
        p=self.prediction(text)
        self.assertEqual((p['predicted_primary'],p['predicted_scope']),('mixed','partially_supported'))
        self.assertEqual(p['routing_action'],'retrieve_supported_components')
        self.assertNotIn('deposit',p['retrieval_requests'][0]['query'])
    def test_joined_supported_labor_and_consumer_stay_fully_supported(self):
        text='Private employee ako. Hindi binayaran overtime ko at ayaw palitan ng store ang defective blender.'
        p=self.prediction(text)
        self.assertEqual((p['predicted_primary'],p['predicted_scope']),('mixed','fully_supported'))
        self.assertEqual(p['routing_action'],'retrieve_supported_components')
        self.assertEqual({r['allowed_domain'] for r in p['retrieval_requests']},{'labor','consumer'})
    def test_new_splitter_keeps_lists_negated_categories_and_followups(self):
        from clause_classifier import split_joined_complaints
        for text in ['hindi binayaran ang sahod at overtime ko',
                     'private employee ako at hindi government employee',
                     'my private employer owes overtime and did not publish my home address online',
                     'a shop refuses warranty at hindi ko alam ang gagawin',
                     'wages are described as "unpaid at ayaw ibalik ng landlord ang deposit"']:
            with self.subTest(text=text):self.assertEqual(split_joined_complaints(text),[text])
        p=self.prediction('Private employee ako at hindi government employee. Hindi binayaran overtime ko.')
        self.assertEqual((p['predicted_primary'],p['predicted_scope']),('labor','fully_supported'))
    def test_joined_unknown_complaint_requests_clarification(self):
        p=self.prediction('A store refuses my blender warranty at hindi pa resolved ang custody dispute ko.')
        self.assertTrue(p['segmentation_audit']['unresolved_fragment_ids'])
        self.assertEqual(p['routing_action'],'clarify')
        self.assertTrue(p['segmentation_audit']['all_fragments_accounted_for'])
    def test_reordering_distinct_concerns_preserves_labels(self):
        a='My private employer owes overtime pay.';b='A retail store refuses my blender warranty.'
        first=self.prediction(a+' '+b);second=self.prediction(b+' '+a)
        self.assertEqual((first['predicted_primary'],first['predicted_scope']),(second['predicted_primary'],second['predicted_scope']))
    def test_empty_input_requires_clarification(self):
        p=self.prediction('');self.assertEqual(p['reason'],'empty_input');self.assertFalse(p['substantive_answer_admitted'])
    def test_no_live_answer_or_invented_referral(self):
        import csv
        with (ROOT/'dataset/processed/item10/reviewed_v1.0.0/referral_directory.csv').open(encoding='utf-8-sig') as f:
            known={r['referral_id'] for r in csv.DictReader(f)}
        for p in predict_records(self.b,self.general+self.typing):
            self.assertFalse(p['deployment_allowed']);self.assertNotIn('answer_text',p)
            self.assertTrue(set(p['referral_ids'])<=known)
            for r in p.get('referral_candidates',[]):
                self.assertTrue(r['candidate_only']);self.assertTrue(r['requires_contact_refresh'])
                self.assertNotIn('phone',r);self.assertNotIn('email',r)
    def test_financial_referrals_distinguish_bank_and_lending_company(self):
        from referral_routing import select_referrals
        def ids(text):
            return [r['referral_id'] for r in select_referrals(
                [{'text':text,'category':'excluded','constraint':'consumer.banking_credit'}])]
        self.assertEqual(ids('My bank charged a credit card fee.'),['REF_BSP_CAM'])
        self.assertEqual(ids('My lending company charged a loan fee.'),['REF_SEC_IMESSAGE'])
        self.assertEqual(ids('There is an unclear financial fee.'),[])
    def test_seafarer_pay_does_not_route_to_training_certification(self):
        from referral_routing import select_referrals
        refs=select_referrals([{'text':'My seafarer wages are unpaid.','category':'excluded','constraint':'labor.seafarers'}])
        self.assertEqual({r['referral_id'] for r in refs},{'REF_DMW','REF_PAO'})
    def test_lexical_selected_model_needs_no_embedding_download(self):
        if self.engine.atomic.feature_kind!='lexical':self.skipTest('semantic candidate uses local encoder')
        with patch('semantic_encoder.encoder',side_effect=AssertionError('Encoder unexpectedly required')):self.prediction('A retail store refuses my blender warranty.')
    def test_model_and_runtime_match_frozen_hashes(self):
        selection=json.loads((RUN/'selection_frozen.json').read_text());self.assertEqual(sha(RUN/'classifier.joblib'),selection['model_sha256']);self.assertEqual(sha(ROOT/'dataset/pipelines/item10/classifier_runtime.py'),self.manifest['runtime_script_sha256'])
    def test_abstain_all_fails_coverage_target(self):
        rows=self.parts['validation'];preds=predict_records(self.b,rows)
        for p in preds:p.update(routing_action='clarify',substantive_answer_admitted=False)
        check=next(g for g in gates(evaluate(rows,preds),self.policy) if g['name']=='decisive_coverage');self.assertFalse(check['passed'])
    def test_counterfactual_scope_negation_and_background_regressions(self):
        records=[]
        for primary,scope,text in REGRESSIONS:
            p=self.prediction(text);records.append({'text':text,'expected_primary':primary,'expected_scope':scope,'predicted_primary':p['predicted_primary'],'predicted_scope':p['predicted_scope'],'origin':'AI-authored development regression, not independent gold'})
            with self.subTest(text=text):self.assertEqual((p['predicted_primary'],p['predicted_scope']),(primary,scope))
        save(RUN/'scope_regression_results.json',records)

    def test_real_complaint_is_not_classified_as_background(self):
        t="A store refuses my warranty. I have a complaint involving a seafarer's overseas deployment."
        audit=segment_question(t);self.assertEqual(len(audit['components']),2);self.assertTrue(audit['all_fragments_accounted_for']);self.assertFalse(audit['requires_clarification'])
        self.assertEqual([f['role'] for f in audit['fragments']],['concern','concern'])
        p=self.prediction(t);self.assertEqual((p['predicted_primary'],p['predicted_scope']),('mixed','partially_supported'))
    def test_taglish_public_disclosure_is_recognized_as_privacy(self):
        from scope_constraints import constraint
        for text in ['Inilabas ng seller ang home address ko online.',
                     'Ibinunyag ng shop ang tirahan ko sa Facebook.',
                     'Kinakalat nila ang ID ko online.',
                     'Ibinahagi ng retailer ang phone number ko publicly.']:
            with self.subTest(text=text):self.assertEqual(constraint(text),('excluded','consumer.data_privacy'))
    def test_taglish_privacy_concern_is_separate_from_product_warranty(self):
        for text in ['Ayaw ng retail shop sa product warranty ko. Hiwalay na issue, inilabas nila home address ko online.',
                     'Ibinunyag ng shop ang tirahan ko sa Facebook. A retail store refuses my product warranty.']:
            with self.subTest(text=text):
                p=self.prediction(text);self.assertEqual((p['predicted_primary'],p['predicted_scope']),('mixed','partially_supported'))
                self.assertEqual(p['routing_action'],'retrieve_supported_components')
                self.assertTrue(any(c['constraint_topic']=='consumer.data_privacy' for c in p['excluded_components']))
                self.assertTrue(all('address' not in r['query'] and 'tirahan' not in r['query'] for r in p['retrieval_requests']))
    def test_ordinary_shipping_address_is_not_public_disclosure(self):
        from scope_constraints import constraint
        for text in ['Ibinigay ko ang address sa online shop para sa delivery ng kettle.',
                     'Inilabas ng shop ang delivery address para sa rider.',
                     'Ibinahagi ko ang address sa retailer para sa delivery.']:
            with self.subTest(text=text):self.assertNotEqual(constraint(text),('excluded','consumer.data_privacy'))
    def test_negated_taglish_disclosure_does_not_create_partial_support(self):
        text='Hindi nila inilabas ang home address ko online. A shop refuses my product warranty.'
        p=self.prediction(text);self.assertEqual((p['predicted_primary'],p['predicted_scope']),('consumer','fully_supported'))
    def test_partial_concerns_survive_order_punctuation_language_and_typos(self):
        first='A store refuses my blender warranty';second="I have a complaint involving a seafarer's overseas deployment"
        texts=[first+'. '+second+'.',second+'. '+first+'.',first+'; '+second,second+' + '+first,
            'I have a complaint about my seafrer deployment. An appliance store refuses my warranty.',
            'May reklamo ako sa deployment ko bilang seafarer. Ayaw i-honor ng store yung warranty ng blender.']
        for text in texts:
            with self.subTest(text=text):
                p=self.prediction(text);self.assertEqual((p['predicted_primary'],p['predicted_scope']),('mixed','partially_supported'))
                self.assertEqual(p['routing_action'],'retrieve_supported_components');self.assertEqual(len(p['excluded_components']),1)
                self.assertTrue(all('seaf' not in q['query'] and q['allowed_domain']=='consumer' for q in p['retrieval_requests']))
    def test_anaphoric_dispute_followups_do_not_create_new_concerns(self):
        for text in ['A shop refuses my appliance warranty. My home insurer denied my claim. How do I raise each dispute?',
                     "My insurer won't cover a hospital expense. Can you explain the exclusion and how to dispute it?"]:
            with self.subTest(text=text):
                p=self.prediction(text)
                self.assertFalse(p['segmentation_audit']['unresolved_fragment_ids'])
                self.assertEqual(p['segmentation_audit']['fragments'][-1]['role'],'follow_up')
                self.assertNotEqual(p['routing_action'],'clarify')
                self.assertTrue(all('insur' not in r['query'] for r in p.get('retrieval_requests',[])))
    def test_anaphoric_word_does_not_swallow_new_unknown_topic(self):
        text='A shop refuses my warranty. How do I raise this custody dispute?'
        p=self.prediction(text)
        self.assertTrue(p['segmentation_audit']['unresolved_fragment_ids'])
        self.assertEqual(p['routing_action'],'clarify')
        self.assertFalse(p['substantive_answer_admitted'])
    def test_typo_and_taglish_government_complaints_are_not_background(self):
        for text in ['Municipal goverment employe here, salry delayd. What civil servce remedy applies?',
                     'Delayed yung sahod ko bilang empleyado ng municipal government. Ano ang remedy sa civil service?']:
            with self.subTest(text=text):
                p=self.prediction(text)
                self.assertEqual((p['predicted_primary'],p['predicted_scope']),('out_of_scope','unsupported'))
                self.assertEqual(p['routing_action'],'refer_out_of_scope')
                self.assertTrue(any(c['constraint']=='labor.government_employment' for c in p['component_evidence']))
                self.assertEqual(p['question_text'],text)
    def test_typo_background_does_not_exclude_ordinary_purchase(self):
        text='Municipal goverment employe here. A store refuses my kettle warranty.'
        p=self.prediction(text)
        self.assertEqual((p['predicted_primary'],p['predicted_scope']),('consumer','fully_supported'))
        self.assertEqual(p['segmentation_audit']['fragments'][0]['role'],'background')
    def test_private_workplace_duties_are_distinct_from_private_purchases(self):
        from scope_constraints import constraint
        for text in ['Sa private office, walang meal break dahil may phone duty.',
                     'Required yung briefing after shift sa private warehouse namin.',
                     'Pinalitan yung weekly rest day ko sa private shop.']:
            self.assertEqual(constraint(text)[0],'labor',text)
        for text in ['On my rest day I bought a faulty kettle from a private shop.',
                     'A customer at a private restaurant was charged for a meal during a shift.',
                     'A private shop sold a faulty chair.']:
            rule=constraint(text)
            self.assertTrue(rule is None or rule[0]=='consumer',text)
    def test_case_prediction_and_union_boundaries_keep_real_topics(self):
        from scope_constraints import constraint
        self.assertEqual(constraint('Siguradong mananalo ba ako sa dismissal case?'),('excluded','labor.case_outcome_prediction'))
        self.assertEqual(constraint('Predict the result of my administrative appeal.'),('excluded','labor.case_outcome_prediction'))
        self.assertEqual(constraint('A disagreement about the bargaining unit and union representation.'),('excluded','labor.union_cba'))
        self.assertEqual(constraint('What is the SEnA procedure?')[0],'labor')
        self.assertNotEqual(constraint('A shop sold an unsafe product.'),('excluded','labor.case_outcome_prediction'))
    def test_low_confidence_retains_real_probabilities_and_clarification(self):
        from classifier_runtime import uncertainty_question
        p=self.prediction('My private employer owes wages. A store refuses my kettle warranty.')
        values=(p['primary_confidence'],p['scope_confidence'])
        r=route_prediction(p,{'primary':1.01,'scope':1.01})
        self.assertEqual(r['reason'],'low_confidence')
        self.assertEqual(r['clarification_question'],uncertainty_question(p))
        self.assertEqual((p['primary_confidence'],p['scope_confidence']),values)
        self.assertFalse(r['substantive_answer_admitted'])
    def test_incidental_background_does_not_create_false_partial_support(self):
        for background in ['I am a seafarer','I am not a seafarer','I am a government employee']:
            for text in [background+'. A store refuses my blender warranty.','A store refuses my blender warranty. '+background+'.']:
                with self.subTest(text=text):
                    p=self.prediction(text);self.assertEqual((p['predicted_primary'],p['predicted_scope']),('consumer','fully_supported'))
                    self.assertTrue(any(f['role']=='background' for f in p['segmentation_audit']['fragments']))
    def test_excluded_only_complaint_stays_unsupported(self):
        p=self.prediction("I have a complaint involving a seafarer's overseas deployment.")
        self.assertEqual((p['predicted_primary'],p['predicted_scope']),('out_of_scope','unsupported'));self.assertFalse(p['substantive_answer_admitted'])
    def test_background_only_input_requires_an_actual_concern(self):
        p=self.prediction('I am a seafarer.');self.assertEqual(p['routing_action'],'clarify');self.assertFalse(p['substantive_answer_admitted']);self.assertEqual(p['segmentation_audit']['fragments'][0]['role'],'background')
    def test_prefaces_without_a_recognized_concern_supply_no_domain_evidence(self):
        p=self.prediction('Hello there. Could you explain what happens next?')
        self.assertFalse(p['has_reliable_component_evidence']);self.assertEqual(p['component_evidence'],[]);self.assertEqual(p['routing_action'],'clarify')
    def test_background_still_supplies_context_to_actual_employment_concerns(self):
        for text in ['I work for a private firm. They require me to work through my meal break.',
            'I am employed by a private firm. They insist I sign a resignation letter.']:
            with self.subTest(text=text):
                p=self.prediction(text);self.assertEqual((p['predicted_primary'],p['predicted_scope']),('labor','fully_supported'))
                self.assertFalse(p['segmentation_audit']['requires_clarification']);self.assertTrue(any('private employment:' in c['text'] for c in p['component_evidence']))
    def test_standalone_questions_do_not_require_a_structural_cue_keyword(self):
        text='A sales promotion used misleading conditions that were not clearly disclosed.'
        audit=segment_question(text);self.assertFalse(audit['requires_clarification']);self.assertEqual(audit['fragments'][0]['role'],'concern')
        p=self.prediction(text);self.assertEqual((p['predicted_primary'],p['predicted_scope']),('consumer','fully_supported'))
    def test_fragment_accounting_survives_background_and_followups(self):
        text="Hello there. A store refuses my warranty. What options do I have? I am a seafarer."
        audit=segment_question(text);self.assertEqual(len(audit['fragments']),4);self.assertTrue(audit['all_fragments_accounted_for'])
        self.assertEqual([f['role'] for f in audit['fragments']],['preface','concern','follow_up','background'])
        self.assertEqual(len(audit['components']),1);self.assertIn('hello there',audit['components'][0]);self.assertIn('what options',audit['components'][0])
    def test_every_development_fragment_is_accounted_for(self):
        for r in self.parts['validation']+self.general+self.typing:
            audit=segment_question(r['question_text']);self.assertTrue(audit['all_fragments_accounted_for'],r['question_id'])
            for f in audit['fragments']:
                if f['role']!='background':self.assertIsNotNone(f['component_index'])
    def test_unresolved_separate_concern_blocks_high_confidence(self):
        p=self.prediction('A store refuses my blender warranty. My custody dispute is another concern.')
        self.assertTrue(p['segmentation_audit']['unresolved_fragment_ids'])
        p.update(primary_confidence=1.,scope_confidence=1.)
        r=route_prediction(p,{'primary':0.,'scope':0.});self.assertEqual(r['reason'],'unresolved_concern');self.assertFalse(r['substantive_answer_admitted'])
    def test_unaccounted_fragment_blocks_admission(self):
        p=self.prediction('A store refuses my blender warranty.');p['segmentation_audit']['all_fragments_accounted_for']=False
        r=route_prediction(p,{'primary':0.,'scope':0.});self.assertEqual(r['reason'],'unaccounted_input_fragment');self.assertFalse(r['substantive_answer_admitted'])
    def test_many_concerns_are_retained_and_require_clarification(self):
        text=' '.join('A retail store refuses my blender warranty for order '+str(i)+'.' for i in range(13))+" I have a complaint involving a seafarer's deployment."
        p=self.prediction(text);self.assertEqual(len(p['segmentation_audit']['components']),14);self.assertTrue(any('seaf' in c['text'] for c in p['component_evidence']))
        self.assertEqual(p['reason'],'too_many_concerns');self.assertFalse(p['substantive_answer_admitted'])
    def test_opened_test_cannot_become_fresh_by_changing_run_directory(self):
        from evaluate_logical_holdout import ensure_unopened_source
        with self.assertRaises(ValueError):ensure_unopened_source({'original_synthetic_test_previously_opened':True},{'data':{}})
        with self.assertRaises(ValueError):ensure_unopened_source({}, {'data':{'synthetic_test_already_opened':True}})
    def test_legacy_test_entry_point_also_blocks_reopened_source(self):
        from train_classifier import final_test
        with self.assertRaisesRegex(ValueError,'already opened'):final_test(RUN)
    def test_parent_package_and_training_weights_are_preserved(self):
        lineage=self.manifest.get('repair_lineage')
        if not lineage:self.skipTest('No parent repair lineage for this run')
        parent=Path(lineage['parent_run'])
        for name,h in json.loads((parent/'artifact_checksums.json').read_text()).items():self.assertEqual(sha(parent/name),h,name)
        old=joblib.load(parent/'classifier.joblib')['primary_model'].engine.atomic
        np.testing.assert_array_equal(self.engine.atomic.model.coef_,old.model.coef_);np.testing.assert_array_equal(self.engine.atomic.model.intercept_,old.model.intercept_)

def readrows_json(path):return json.loads(path.read_text())
def main():
    global RUN
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();RUN=a.run_dir.resolve()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LogicalTests))
    save(RUN/'software_tests.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful(),'counterfactual_development_regressions':len(REGRESSIONS),'accuracy_acceptance_is_separate':True})
    raise SystemExit(0 if result.wasSuccessful() else 1)
if __name__=='__main__':main()
