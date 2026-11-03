"""Consequential eligibility, provenance, ranking, window and integration checks."""
from __future__ import annotations
import argparse,copy,json,os,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from common import ROOT,PIPELINE,sources,curate,eligibility,readrows,save,sha
from encoder import tokenizer,windows
from retrieval import LegalRetriever
INDEX=None

class RetrievalTests(unittest.TestCase):
    def test_specific_issue_wins_over_incidental_wage_and_product_words(self):
        checks=[
            ('Our private employer offsets overtime against undertime on another day.','labor','LAB_CODE_2022__art_88'),
            ('Our private office chooses a rest day that conflicts with a religious preference.','labor','LAB_IRR_1989__rule_iii_weekly_rest_periods__section_4'),
            ('A private contractor hired a worker for a project without defining its scope at engagement.','labor','LAB_CODE_2022__art_295'),
            ('A grocery charges above its posted price label.','consumer','RA_7394_1992__art_81'),
        ]
        for query,domain,expected in checks:
            with self.subTest(query=query):
                hits=self.retriever.search(query,domain,'bm25',5)['hits']
                self.assertIn(expected,{h['provision_id'] for h in hits})
                self.assertFalse(any('deceased' in h['heading'].lower() or 'arbitration' in h['heading'].lower() for h in hits))

    def test_procedural_question_does_not_reintroduce_an_overtime_facet(self):
        hits=self.retriever.search('I have an overtime dispute with a private company. Can you explain the basic labor complaint and referral process without filing a case for me?','labor','bm25',3)['hits']
        self.assertTrue(hits)
        self.assertFalse(any(h['provision_id'] in {'LAB_CODE_2022__art_87','LAB_IRR_1989__rule_i_hours_of_work__section_8'} for h in hits))
        self.assertTrue(any('conciliation' in h['heading'].lower() or 'conciliat' in h['provision_id'] for h in hits))
    def test_deduction_hearing_is_not_a_dismissal_hearing(self):
        hits=self.retriever.search('A private shop deducts breakages from my salary without hearing me.','labor','bm25',5)['hits']
        self.assertIn('LAB_IRR_1989__rule_viii_payment_of_wages__section_14',{h['provision_id'] for h in hits})
        self.assertFalse(any('termination_of_employment' in h['provision_id'] for h in hits))

    def test_religious_rest_preference_is_not_only_a_generic_schedule(self):
        hits=self.retriever.search('A private employer schedules my weekly rest day but I have a religious preference. What does the recorded scheduling rule require the employer to consider?','labor','bm25',3)['hits']
        self.assertIn('LAB_IRR_1989__rule_iii_weekly_rest_periods__section_4',{h['provision_id'] for h in hits})

    def test_internal_platform_complaint_is_not_a_platform_development_deadline(self):
        hits=self.retriever.search('For an ordinary online retail dispute, what platform complaint steps are recorded before the buyer escalates to a government office?','consumer','bm25',5)['hits']
        self.assertTrue(hits)
        self.assertTrue(any('internal redress' in h['heading'].lower().replace('lnternal','internal') for h in hits))
        self.assertNotIn('RA_11967_2023__sec_17',{h['provision_id'] for h in hits})

    def test_project_and_closure_queries_retrieve_their_actual_frameworks(self):
        project=self.retriever.search('For a private construction employer, what needs to be identified when a worker is hired for a particular project?','labor','bm25',5)['hits']
        self.assertIn('LAB_CODE_2022__art_295',{h['provision_id'] for h in project})
        closure=self.retriever.search('My private employer says the business is closing and has sent a termination letter. What general authorized-cause framework should I inspect?','labor','bm25',5)['hits']
        self.assertEqual(closure[0]['provision_id'],'LAB_CODE_2022__art_298')

    def test_opportunity_to_answer_retrieves_procedure_instead_of_rest_or_disease(self):
        hits=self.retriever.search('A private hotel dismissed a receptionist. The worker was given no chance to explain. What procedural safeguards can be described generally?','labor','bm25',5)['hits']
        self.assertTrue(any('answer and hearing' in h['heading'].lower() or 'notice of dismissal' in h['heading'].lower() for h in hits))
        self.assertNotIn('LAB_CODE_2022__art_299',{h['provision_id'] for h in hits})

    def test_quality_and_cash_change_paraphrases_keep_relevant_regimes(self):
        quality=self.retriever.search('A retail shop sold me a defective fan. No injury occurred.','consumer','bm25',5)['hits']
        self.assertIn('RA_7394_1992__art_100',{h['provision_id'] for h in quality})
        self.assertFalse(any(h['provision_id'] in {'RA_7394_1992__art_97','RA_7394_1992__art_99'} for h in quality))
        change=self.retriever.search('After a cash purchase, the cashier gave sweets instead of the remaining coins.','consumer','bm25',5)['hits']
        self.assertTrue(any('10909' in h['document_id'] for h in change))
        order=self.retriever.search('Online retail purchase: distinguish a change of mind from delivery of a nonconforming item.','consumer','bm25',5)['hits']
        self.assertFalse(any('10909' in h['document_id'] for h in order))

    def test_short_change_and_price_tag_queries_keep_distinct_evidence(self):
        hits=self.retriever.search('The grocery kept my change.','consumer','bm25',5)['hits']
        self.assertTrue(hits)
        self.assertTrue(any('10909' in h['document_id'] for h in hits))
        self.assertFalse(any(h['provision_id'] in {'RA_7394_1992__art_81','RA_7394_1992__art_83'} for h in hits))
        price=self.retriever.search('The store charged above the displayed price tag.','consumer','bm25',5)['hits']
        self.assertIn('RA_7394_1992__art_81',{h['provision_id'] for h in price})
        online=self.retriever.search('I want to change my online order because the retailer sent the wrong item.','consumer','bm25',5)['hits']
        self.assertTrue(online)
        self.assertFalse(any('10909' in h['document_id'] for h in online))

    def test_required_meeting_time_cannot_be_answered_with_an_overtime_rate_alone(self):
        from query_relevance import source_relevance,needs_worked_time_definition
        query='Private company employee. The required meeting is off the clock. Does it count as working time?'
        self.assertTrue(needs_worked_time_definition(query))
        for heading in ['Normal Hours of Work','Overtime Work','Undertime Not Offset by Overtime','Time of payment','Regular and casual employment']:
            with self.subTest(heading=heading):
                self.assertEqual(source_relevance(query,'labor',{'heading':heading,'parent_text':'The normal workday and overtime premium are described here.'}),0)
        self.assertFalse(needs_worked_time_definition('What is the ordinary overtime rate for two extra hours?'))

    def test_functional_defects_and_service_quality_do_not_become_safety_findings(self):
        quality=self.retriever.search('The retailer sold me a blender with a broken motor. What defect rules apply?','consumer','bm25',5)
        self.assertIn('RA_7394_1992__art_100',{h['provision_id'] for h in quality['hits']})
        self.assertNotIn('RA_7394_1992__art_97',{h['provision_id'] for h in quality['hits']})
        safety=self.retriever.search('The extension cord from the retailer has exposed live wires and sparks. What product safety rules apply?','consumer','bm25',5)
        self.assertIn('RA_7394_1992__art_97',{h['provision_id'] for h in safety['hits']})
        service=self.retriever.search('The paid laundry service damaged my curtains. What service quality rules apply?','consumer','bm25',5)
        self.assertIn('RA_7394_1992__art_102',{h['provision_id'] for h in service['hits']})
        self.assertNotIn('RA_7394_1992__art_99',{h['provision_id'] for h in service['hits']})
    def test_procedural_subtopics_are_not_dropped_by_the_broader_topic_filter(self):
        cases=[('Private employee ako. Anong details ang dapat nasa payroll tungkol sa oras, overtime, at deductions?','labor','LAB_IRR_1989__rule_x_administration_and_enforcement__section_6'),
               ('Sa SEnA conference, confidential ba ang usapan at pwede bang mag-video record ang participant?','labor','DOLE_DO_249_25__rule_v_conciliat_on_mediation_proceedings__section_4'),
               ('Sa SEnA meeting, ano ang rule sa pagharap ng lawyer, agent, o representative?','labor','DOLE_DO_249_25__rule_v_conciliat_on_mediation_proceedings__section_2'),
               ('Kailangan bang dumaan muna sa internal complaint process ng online platform bago sa government agency?','consumer','RA_11967_2023__sec_24')]
        for query,domain,expected in cases:
            with self.subTest(query=query):self.assertIn(expected,{h['provision_id'] for h in self.retriever.search(query,domain,top_k=5)['hits']})
    def test_rule_coverage_is_carried_as_an_exact_source_restriction(self):
        record=next(r for r in self.records if r['provision_id']=='LAB_IRR_1989__rule_i_a__section_5')
        coverage=self.source['provisions']['LAB_IRR_1989__rule_i_a__section_1']['normalized_text']
        self.assertIn(coverage,record['conditions'])
        ordinary=self.retriever.search('My private company requires a briefing before clock-in. What is working time?','labor','bm25',10)
        # Clean counted-time mappings have been recovered. Neither a hospital
        # rule nor the normal-hours ceiling substitutes for this authority.
        self.assertTrue(ordinary['hits'])
        self.assertFalse(any(h['provision_id']=='LAB_CODE_2022__art_83' for h in ordinary['hits']))
        self.assertFalse(any(h['provision_id'].startswith('LAB_IRR_1989__rule_i_a__') for h in ordinary['hits']))
        normal=self.retriever.search('What are normal working hours at my private company?','labor','bm25',10)
        self.assertTrue(any(h['provision_id']=='LAB_CODE_2022__art_83' for h in normal['hits']))
        specific=self.retriever.search('My employer is a private hospital. My shift uses regular working hours.','labor','bm25',10)
        self.assertTrue(any(h['provision_id'].startswith('LAB_IRR_1989__rule_i_a__') for h in specific['hits']))
    def test_single_holiday_scenario_retrieves_holiday_provisions(self):
        query='A private-sector employer refuses to pay a worker for Christmas Day because the office was closed and no work was performed. What holiday-pay rules and exceptions apply?'
        result=self.retriever.search(query,'labor','bm25',5)
        self.assertEqual(result['query'],query)
        self.assertEqual(result['explicit_query_topic_filter'],['labor.holiday_premium_pay'])
        self.assertTrue(all('labor.holiday_premium_pay' in h['supported_topics'] for h in result['hits']))
        self.assertTrue({'LAB_CODE_2022__art_94','LAB_IRR_1989__rule_iv_holidays_with_pay__section_3'} & {h['provision_id'] for h in result['hits'][:3]})
        self.assertEqual(result['hits'][0]['provision_id'],'LAB_CODE_2022__art_94')
        self.assertFalse(any('overtime' in h['heading'].lower() for h in result['hits']))

    def test_holiday_filter_does_not_hide_an_explicit_second_labor_topic(self):
        for query in ['My private employer owes holiday pay and overtime pay.',
                      'Private employee: minimum wage and holiday-pay rules.',
                      'Private company dismissal and Christmas holiday pay.',
                      'Private company delayed salary and holiday pay.']:
            with self.subTest(query=query):
                result=self.retriever.search(query,'labor','bm25',5)
                self.assertNotIn('explicit_query_topic_filter',result)

    def test_holiday_comparisons_keep_work_performed_sources_available(self):
        for query in ['Private employee: I did not work on Christmas but worked on New Year holiday.',
                      'Private employee: no work was performed on Christmas; what if I work on a holiday?',
                      'Private employee: unworked holiday and holiday overtime pay.']:
            with self.subTest(query=query):
                result=self.retriever.search(query,'labor','bm25',10)
                self.assertNotEqual(result.get('query_relevance_filter'),'exclude_worked_holiday_premium_for_explicit_unworked_holiday')

    def test_caller_topic_filter_is_preserved(self):
        result=self.retriever.search('Overtime work on Christmas Day','labor','bm25',5,['labor.overtime_pay'])
        self.assertNotIn('explicit_query_topic_filter',result)
        self.assertTrue(all('labor.overtime_pay' in h['supported_topics'] for h in result['hits']))

    def test_tagalog_change_and_procedure_queries_retrieve_known_provisions(self):
        cases = [('Walang barya daw ang grocery kaya candy na lang ang sukli.', 'RA_10909_2016__sec_4'),
                 ('letter complaint consumer investigation', 'RA_7394_1992__art_159'),
                 ('security of tenure termination private employee', 'LAB_CODE_2022__art_294')]
        for query, target in cases:
            with self.subTest(query=query):
                domain = 'labor' if 'employee' in query else 'consumer'
                self.assertIn(target, {h['provision_id'] for h in self.retriever.search(query, domain, 'bm25', 5)['hits']})
    @classmethod
    def setUpClass(cls):
        cls.source=sources();cls.retriever=LegalRetriever(INDEX);cls.records=cls.retriever.records
        cls.windows=readrows(INDEX/'semantic_windows.jsonl');cls.original={r['chunk_id']:r for r in cls.source['chunks']}
    def fixture(self):
        r=next(r for r in self.records if r['provision_id']=='LAB_CODE_2022__art_88')
        return copy.deepcopy(self.original[r['chunk_id']]),copy.deepcopy(self.source['provisions'][r['provision_id']]),copy.deepcopy(self.source['documents'][r['document_id']])
    def test_delayed_wage_queries_retrieve_payment_timing(self):
        target='LAB_IRR_1989__rule_viii_payment_of_wages__section_3'
        for query in ['My private employer delays my salary.', 'Private employee delayed ang sahod.',
                      'Private employe salary delayd.', 'Overdue wages at a private warehouse.']:
            with self.subTest(query=query):
                result=self.retriever.search(query,'labor','bm25',5)
                self.assertIn(target,{h['provision_id'] for h in result['hits']})
                self.assertEqual(result['query'],query)
    def test_unpaid_overtime_retrieves_general_compensation_rule(self):
        target='LAB_CODE_2022__art_87'
        for query in ['My private employer did not pay overtime.', 'Private employee with unpaid overtime.',
                      'Private employer overtime pay missing.']:
            with self.subTest(query=query):
                self.assertIn(target,{h['provision_id'] for h in self.retriever.search(query,'labor','bm25',5)['hits']})
    def test_labor_expansion_does_not_rewrite_consumer_or_wage_amount_queries(self):
        from retrieval import ranking_expansion
        self.assertEqual(ranking_expansion('delayed salary and overtime pay','consumer'),[])
        self.assertEqual(ranking_expansion('What is the minimum wage amount?','labor'),[])
        self.assertEqual(ranking_expansion('A wage deduction for a uniform purchase','labor'),[])
    def test_overtime_qualifications_survive_ranking_expansion(self):
        from retrieval import ranking_expansion
        for text in ['overtime pay for holiday work','overtime pay on a rest day','emergency overtime compensation',
                     'undertime not offset by overtime pay']:
            with self.subTest(text=text):self.assertNotIn('ordinary',ranking_expansion(text,'labor'))
        self.assertIn('ordinary',ranking_expansion('unpaid overtime','labor'))
    def test_valid_investigation_queries_are_not_blocked_as_investments(self):
        for text in ['Can a consumer request investigation of a retail transaction?',
                     'Pwede ma-investigate ang store transaction sa consumer complaint?']:
            response=self.retriever.search(text,'consumer','bm25')
            self.assertNotEqual(response['status'],'blocked_scope')
            self.assertTrue(response['hits'])
    def test_criminal_investigation_and_investment_remain_excluded(self):
        for text,reason in [
            ('I want a criminal investigation of a fake store.','consumer.criminal_online_fraud'),
            ('My investment fund refuses a refund.','consumer.investments')]:
            response=self.retriever.search(text,'consumer','bm25')
            self.assertEqual(response['status'],'blocked_scope')
            self.assertEqual(response['reason'],reason);self.assertEqual(response['hits'],[])
    def test_bilingual_glossary_is_symmetric(self):
        from retrieval import tokens
        for left,right in [('sahod','wages'),('pagharap lawyer','appearance lawyers'),
                           ('bawas presyo','price reduction'),('redo services','reperformance service')]:
            self.assertEqual(sorted(tokens(left)),sorted(tokens(right)))
    def test_overseas_remittance_sources_are_quarantined(self):
        self.assertFalse(any('foreign exchange remittance' in json.dumps(r['source_hierarchy']).lower()
                             for r in self.records))
    def test_source_hashes_and_canonical_files_unchanged(self):
        m=json.loads((INDEX/'index_manifest.json').read_text());self.assertEqual(m['source_sha256'],self.source['source_sha256'])
        self.assertEqual(json.loads((INDEX/'source_audit.json').read_text())['raw_source_sha256'],self.source['raw_source_sha256'])
    def test_rebuild_eligibility_exactly_reproduces_index_membership(self):
        included,excluded=curate(self.source);self.assertEqual({r['chunk_id'] for r in included},{r['chunk_id'] for r in self.records})
        self.assertEqual(len(included)+len(excluded),len(self.source['chunks']));self.assertEqual(len(included),self.retriever.manifest['indexed_chunks'])
    def test_ineligible_historical_and_review_sources_are_absent(self):
        for r in self.records:
            c=self.original[r['chunk_id']];p=self.source['provisions'][r['provision_id']];d=self.source['documents'][r['document_id']]
            self.assertTrue(c['answer_eligible'] and p['provision_answer_eligible'] and d['document_answer_eligible_candidate']);self.assertEqual(eligibility(c,p,d,self.source),[])
    def test_scope_and_glyph_quarantine_is_effective(self):
        ids={r['provision_id'] for r in self.records}
        for pid in ['LAB_CODE_2022__art_263','RA_7394_1992__art_20','RA_7394_1992__art_114','DOLE_DO_249_25__rule_ill_procedures_in_requests_for_assistance__section_1']:
            self.assertNotIn(pid,ids)
        self.assertTrue(all('househelper' not in json.dumps(r['source_hierarchy']).lower() for r in self.records))
    def test_attached_footnote_numbers_do_not_evade_scope_screen(self):
        c,p,d=self.fixture();p['hierarchy']['chapter']='EMPLOYMENT OF HOUSEHELPERS112'
        self.assertIn('scope_quarantine:specialized_employment',eligibility(c,p,d,self.source))
    def test_each_eligibility_level_blocks_independently(self):
        for level,field in [(0,'answer_eligible'),(1,'provision_answer_eligible'),(2,'document_answer_eligible_candidate')]:
            rows=self.fixture();rows[level][field]=False;self.assertTrue(eligibility(*rows,self.source))
    def test_blocking_and_unknown_quality_flags_fail_closed(self):
        for flag in ['official_text_comparison_pending','unrecognized_new_quality_flag']:
            c,p,d=self.fixture();p['quality_flags']=[flag];self.assertTrue(eligibility(c,p,d,self.source))
    def test_unverified_ocr_is_blocked(self):
        c,p,d=self.fixture();p['ocr_used']=True;p['review_status']='machine_validated';self.assertIn('unverified_ocr',eligibility(c,p,d,self.source))
    def test_unknown_status_and_retrieval_policy_are_blocked(self):
        c,p,d=self.fixture();d['status_family']='new_unknown_status';self.assertIn('restricted_legal_status',eligibility(c,p,d,self.source))
        c,p,d=self.fixture();d['retrieval_use_policy']='allow_everything';self.assertIn('unknown_or_restricted_retrieval_policy',eligibility(c,p,d,self.source))
    def test_excluded_topics_and_domain_mismatch_are_blocked(self):
        c,p,d=self.fixture();c['excluded_topics']=['labor.ofw'];self.assertIn('excluded_topic_present',eligibility(c,p,d,self.source))
        c,p,d=self.fixture();c['supported_topics']=['consumer.warranties'];self.assertIn('topic_domain_mismatch',eligibility(c,p,d,self.source))
    def test_missing_locator_is_blocked(self):
        c,p,d=self.fixture();p['source_locator']={'pdf_page_start':None,'source_char_start':None,'html_anchor':None};self.assertIn('missing_source_locator',eligibility(c,p,d,self.source))
    def test_new_text_corruption_is_quarantined(self):
        c,p,d=self.fixture();p['normalized_text']+=' a^x^q^z';self.assertIn('extraction_anomaly_requires_review',eligibility(c,p,d,self.source))
    def test_citations_parent_text_and_offsets_match_sources(self):
        for r in self.records:
            p=self.source['provisions'][r['provision_id']];d=self.source['documents'][r['document_id']]
            self.assertEqual(r['parent_text'],p['normalized_text']);self.assertEqual(r['citation_display'],p['citation_display']);self.assertEqual(r['source_locator'],p['source_locator'])
            self.assertEqual(r['display_text'],p['normalized_text'][r['normalized_char_start']:r['normalized_char_end']]);self.assertEqual(r['official_source_url'],d['official_source_url'])
    def test_windows_are_within_token_limit_and_cover_all_text(self):
        grouped={}
        for w in self.windows:
            self.assertLessEqual(w['token_count'],128);self.assertEqual(w['token_count'],len(tokenizer().encode(w['text']).ids));grouped.setdefault(w['record_index'],[]).append(w)
        for i,r in enumerate(self.records):
            coverage=np.zeros(len(r['display_text']),dtype=bool)
            for w in grouped[i]:coverage[w['char_start']:w['char_end']]=True
            self.assertTrue(all(coverage[j] or char.isspace() for j,char in enumerate(r['display_text'])),r['chunk_id'])
    def test_long_query_keeps_its_tail(self):
        text=('ordinary overtime work '*150)+'UNIQUE ENDING';parts=windows(text)
        self.assertGreater(len(parts),1);self.assertIn('UNIQUE ENDING',parts[-1]['text']);self.assertTrue(all(p['token_count']<=128 for p in parts))
    def test_vectors_are_finite_normalized_and_aligned(self):
        v=self.retriever.vectors;self.assertEqual(v.shape,(len(self.windows),384));self.assertTrue(np.isfinite(v).all());np.testing.assert_allclose(np.linalg.norm(v,axis=1),1,atol=1e-5)
        self.assertEqual(self.retriever.window_records.tolist(),[w['record_index'] for w in self.windows])
    def test_bm25_numeric_reference(self):
        # Single known posting: N=2, df=1, tf=2, dl=3, avgdl=2.5.
        import collections,math
        r=object.__new__(LegalRetriever);r.records=[{},{}];r.counts=[collections.Counter({'apple':2,'pear':1}),collections.Counter({'orange':2})]
        r.length=np.array([3,2]);r.average_length=2.5;r.df=collections.Counter({'apple':1,'pear':1,'orange':1});r.config={'bm25_k1':1.2,'bm25_b':.75}
        expected=math.log(2)*(2*2.2)/(2+1.2*(.25+.75*3/2.5));np.testing.assert_allclose(r.lexical_scores('apple'),[expected,0.],atol=1e-12)
    def test_retrieval_is_deterministic_and_provision_deduplicated(self):
        for method in ['bm25','semantic','hybrid']:
            a=self.retriever.search('private employer overtime pay','labor',method,10);b=self.retriever.search('private employer overtime pay','labor',method,10)
            self.assertEqual(a,b);ids=[h['provision_id'] for h in a['hits']];self.assertEqual(len(ids),len(set(ids)))
    def test_domain_filters_apply_to_every_method(self):
        for method in ['bm25','semantic','hybrid']:
            for domain,text in [('labor','private employer overtime pay'),('consumer','retailer appliance warranty')]:
                r=self.retriever.search(text,domain,method,10);self.assertTrue(r['hits']);self.assertTrue(all(domain in h['domains'] for h in r['hits']))
    def test_supported_topic_filter_is_applied(self):
        r=self.retriever.search('retail price tag','consumer','bm25',10,['consumer.price_tags'])
        self.assertTrue(r['hits']);self.assertTrue(all('consumer.price_tags' in h['supported_topics'] for h in r['hits']))
    def test_invalid_topic_filters_do_not_fall_back(self):
        for topics in [[],['consumer.banking_credit'],['labor.wages_payment'],['made_up_topic']]:
            with self.assertRaises(ValueError):self.retriever.search('warranty','consumer','bm25',5,topics)
    def test_final_pay_evidence_is_official_excerpt_not_unrelated_wages(self):
        r=self.retriever.search('When should my private employer release final pay and COE?','labor','bm25')
        self.assertTrue(r['hits'])
        self.assertTrue(all('labor.final_pay_coe' in h['supported_topics'] for h in r['hits']))
        self.assertIn('DOLE_FINAL_PAY_COE_NEWS_2026',{h['document_id'] for h in r['hits']})
        self.assertNotIn('DOLE_LA_06_20',{h['document_id'] for h in r['hits']})
    def test_excluded_queries_return_no_candidates(self):
        for row in readrows(INDEX/'benchmark_queries.jsonl'):
            if row['expected_status']=='blocked_scope':
                for method in ['bm25','semantic','hybrid']:
                    r=self.retriever.search(row['question_text'],row['domain'],method);self.assertEqual(r['status'],'blocked_scope');self.assertEqual(r['hits'],[])
    def test_empty_unknown_method_domain_and_limits(self):
        self.assertEqual(self.retriever.search('','labor')['status'],'clarify')
        for kwargs in [{'allowed_domain':'all'},{'allowed_domain':'labor','method':'unknown'},{'allowed_domain':'labor','top_k':0},{'allowed_domain':'labor','top_k':True}]:
            with self.assertRaises(ValueError):self.retriever.search('overtime',**kwargs)
    def test_scores_are_not_answer_permission(self):
        r=self.retriever.search('retail appliance warranty','consumer');self.assertFalse(r['answer_generation_allowed']);self.assertFalse(r['deployment_allowed'])
        for h in r['hits']:
            self.assertFalse(h['answer_generation_allowed']);self.assertTrue(h['retrieval_candidate_only']);self.assertTrue(h['conditions'])
            self.assertEqual(h['status_as_of'],self.source['documents'][h['document_id']]['status_as_of'])
    def test_tampered_index_is_rejected(self):
        original_sha=sha
        with patch('retrieval.sha',side_effect=lambda p:'tampered' if Path(p)==INDEX/'records.jsonl' else original_sha(p)):
            with self.assertRaisesRegex(ValueError,'Index checksum mismatch'):LegalRetriever(INDEX)
    def test_changed_runtime_is_rejected(self):
        original_sha=sha
        with patch('retrieval.sha',side_effect=lambda p:'changed' if Path(p)==PIPELINE/'retrieval.py' else original_sha(p)):
            with self.assertRaisesRegex(ValueError,'runtime changed'):LegalRetriever(INDEX)
    def test_changed_canonical_source_is_rejected(self):
        original_sha=sha;target=ROOT/next(iter(self.source['raw_source_sha256']))
        with patch('retrieval.sha',side_effect=lambda p:'changed' if Path(p)==target else original_sha(p)):
            with self.assertRaisesRegex(ValueError,'Canonical file changed'):LegalRetriever(INDEX)
    def test_encoder_is_offline_and_frozen(self):
        self.assertEqual(os.environ['HF_HUB_OFFLINE'],'1');self.assertEqual(sha(ROOT/'models/embedding_backbone_manifest.json'),self.retriever.manifest['semantic_model_manifest_sha256'])
    def test_benchmark_provenance_and_no_topic_oracle_for_positives(self):
        bm=json.loads((INDEX/'benchmark_manifest.json').read_text());self.assertEqual(sha(INDEX/'benchmark_queries.jsonl'),bm['queries_sha256']);rows=readrows(INDEX/'benchmark_queries.jsonl')
        self.assertEqual(sum(bool(r['relevant_provision_ids']) for r in rows),56);self.assertTrue(all(not r['human_validated'] for r in rows));self.assertTrue(all(r['topic_ids'] is None for r in rows if r['relevant_provision_ids']))
    def test_real_classifier_routes_isolate_excluded_and_vague_inputs(self):
        integration=json.loads((INDEX/'classifier_integration_results.json').read_text());cases={r['case']:r['result'] for r in integration['cases']}
        self.assertEqual(len(cases['partial']['components']),1);self.assertEqual(cases['partial']['components'][0]['allowed_domain'],'consumer');self.assertNotIn('seaf',cases['partial']['components'][0]['query'])
        self.assertEqual({r['allowed_domain'] for r in cases['mixed_full']['components']},{'labor','consumer'})
        for name in ['excluded','clarify']:self.assertEqual(cases[name]['components'],[])
        self.assertEqual(cases['evidence_gap']['components'][0]['status'],'candidates_found')
    def test_classifier_cli_works_without_preloaded_classifier_imports(self):
        import subprocess,sys
        integration=json.loads((INDEX/'classifier_integration_results.json').read_text())
        model=ROOT/integration.get('classifier_model_path','outputs/item10-classifier-v1.4.0/classifier.joblib')
        output=subprocess.check_output([sys.executable,str(PIPELINE/'retrieval.py'),'--index',str(INDEX),'--classifier',str(model),
            '--query','A retail store refuses my blender warranty. I have a complaint about my seafarer deployment.'],cwd=str(ROOT/'tmp'),text=True,encoding='utf-8')
        result=json.loads(output);self.assertEqual(len(result['components']),1);self.assertEqual(result['components'][0]['allowed_domain'],'consumer');self.assertFalse(result['answer_generation_allowed'])
    def test_frozen_classifier_package_is_unchanged(self):
        path=ROOT/'outputs/item10-classifier-v1.4.0'
        for name,h in json.loads((path/'artifact_checksums.json').read_text()).items():self.assertEqual(sha(path/name),h,name)
    def test_default_method_matches_recorded_development_selection(self):
        self.assertEqual(self.retriever.config['default_method'],'bm25');selection=self.retriever.manifest['method_selection']
        self.assertEqual(sha(ROOT/selection['source']),selection['sha256']);self.assertEqual(selection['selected'],'bm25')

def main():
    global INDEX
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True);a=p.parse_args();INDEX=a.index.resolve()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RetrievalTests))
    save(INDEX/'software_tests.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful(),'independent_legal_validation':False})
    raise SystemExit(0 if result.wasSuccessful() else 1)
if __name__=='__main__':main()
