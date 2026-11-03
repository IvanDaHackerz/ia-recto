"""Consequential repair boundaries: privacy, persistence, support and cancellation.

All questions and credentials here are fictional. HTTP/provider replies are mocked.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock,patch
from urllib.request import Request

from backend.application.controls import RequestContext,RequestRegistry,UsageLedger,CancellableTransport,ProviderStopped
from backend.application.development_explanation import TogetherDevelopmentExplanation,checked_claims,explain_recorded_sources,source_options,selected_draft
from backend.application.grounding import support_passed,numeric_facts
from backend.application.history import HistoryStore
from backend.application.privacy import redact
from backend.application.safety import safety_notice
from backend.application.service import ApplicationService
from backend.classifier.contracts import RequestError
from backend.normalization import ConditionalNormalizer,NormalizationUnavailable
from backend.terminal_test import load_runtime

ROOT=Path(__file__).resolve().parents[2]

def codec(data,*,decrypt=False):return data[9:] if decrypt else b'encrypted'+data
def positive(claims):return {'assessments':[{'claim_id':c['claim_id'],'verdict':'supported','qualifications_preserved':True,'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True} for c in claims]}

class PrivacyTests(unittest.TestCase):
    def test_identifiers_are_removed_and_legal_facts_remain(self):
        q='My name is Juan Example. My private employer has not paid 5000 pesos. My bank account number is 1234567890; phone 09123456789; email fake@example.com.'
        r=redact(q)
        for value in ['Juan Example','1234567890','09123456789','fake@example.com']:self.assertNotIn(value,r['text'])
        self.assertIn('5000 pesos',r['text']);self.assertIn('bank account',r['text']);self.assertFalse(r['guaranteed_complete'])
    def test_address_does_not_consume_following_concern(self):
        r=redact('My address is 123 Test Street and my private employer has not paid my salary.')
        self.assertNotIn('123 Test Street',r['text']);self.assertIn('my private employer has not paid my salary',r['text'])
    def test_credential_patterns_do_not_leave_the_local_redactor(self):
        secret='tgp_v1_'+'fictional_'*5
        self.assertNotIn(secret,redact('My key is '+secret)['text'])
    def test_no_redaction_is_claimed_for_unrecognized_identifiers(self):
        r=redact('A hypothetical neighbor named X has a concern.')
        self.assertFalse(r['redacted']);self.assertFalse(r['guaranteed_complete'])

class SafetyTests(unittest.TestCase):
    def test_present_and_filipino_harm_variants(self):
        for q in ['I am being stabbed.','Nasaksak ako sa kalye.','May nanaksak sa akin.','My boss threatened to stab me.']:
            with self.subTest(q=q):self.assertIsNotNone(safety_notice(q))
    def test_history_quotes_and_negation_do_not_raise_current_notice(self):
        for q in ['I was not stabbed.','I was stabbed ten years ago. My private employer has not paid overtime.', 'In our training example the phrase was "I was stabbed". My employer has not paid wages.']:
            with self.subTest(q=q):self.assertIsNone(safety_notice(q))
    def test_present_threat_is_not_hidden_by_a_historical_sentence(self):
        self.assertIsNotNone(safety_notice('I was stabbed ten years ago. My boss threatened to stab me.'))

class GroundingTests(unittest.TestCase):
    def test_offsetting_and_online_return_keep_their_actual_conditions(self):
        from backend.application.grounding import source_qualification_failure
        index=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text())['retrieval']
        records={r['provision_id']:r for r in map(json.loads,(ROOT/index/'records.jsonl').read_text(encoding='utf-8').splitlines())}
        overtime=records['LAB_CODE_2022__art_88']['parent_text']
        self.assertIsNotNone(source_qualification_failure('Undertime must be paid separately.',overtime))
        self.assertIsNone(source_qualification_failure('Undertime on one day cannot be offset by overtime on another day. Leave on another day does not remove the additional compensation required for overtime.',overtime))
        online=records['RA_11967_2023__sec_20']['parent_text']
        self.assertIsNotNone(source_qualification_failure('For a defective product the merchant must accept return of the original goods.',online))
        self.assertIsNotNone(source_qualification_failure('When a merchant delivers the wrong model, the consumer may demand repair, replacement or refund and the originally delivered (incorrect) goods must be returned.',online))
        self.assertIsNone(source_qualification_failure('When the consumer chooses replacement or refund, the merchant is entitled to return of the original goods at no cost to the consumer within a reasonable period unless otherwise agreed.',online))
        self.assertIsNotNone(source_qualification_failure('Thus the employer violates both rules.',overtime))
        status=records['LAB_CODE_2022__art_295']['parent_text']
        self.assertIsNotNone(source_qualification_failure('Regular work has project and seasonal exceptions; otherwise it is casual. Anyone with one year becomes regular.',status))
        self.assertIsNone(source_qualification_failure('The separate casual employment rule provides that a casual employee with at least one year of service becomes regular with respect to that activity.',status))

    def test_generation_and_judge_receive_the_exact_schema_and_bounded_ids(self):
        adapter=TogetherDevelopmentExplanation('mock','fictional-key')
        components=copy.deepcopy(self.components)
        supplied,lookup=source_options(components);qid=next(iter(lookup))
        adapter._send=Mock(return_value={'paragraphs':[{'component_id':'c1','text':'A recorded rule.', 'evidence':[{'quote_id':qid}]}]})
        adapter.complete('Fictional question',{'components':components})
        body=adapter._send.call_args.args[0];schema=body['response_format']['json_schema']['schema']
        self.assertEqual(schema['properties']['paragraphs']['maxItems'],1)
        self.assertEqual(schema['properties']['paragraphs']['items']['properties']['component_id']['enum'],['c1'])
        self.assertEqual(schema['properties']['paragraphs']['items']['properties']['evidence']['items']['properties']['quote_id']['enum'],list(lookup))
        self.assertIn(json.dumps(schema,separators=(',',':')),body['messages'][0]['content'])
        claims=checked_claims(self.draft('The recorded text describes normal daily work hours.'),components)
        components[0]['sources'].append({**components[0]['sources'][0],'chunk_id':'uncited','parent_text':'Uncited-only rule about leave and attendance.'})
        adapter._send.return_value={'assessments':[{'claim_id':'development_1','verdict':'supported',
            'qualifications_preserved':True,'no_case_outcome':True,'no_excluded_advice':True,'no_new_facts':True,
            'answers_requested_issue':True,'actor_scope_preserved':True,'conditions_attached_correctly':True,
            'source_check_reason':'The cited provision describes this hours limit.'}]}
        adapter.assess('Fictional question',claims,components)
        body=adapter._send.call_args.args[0];schema=body['response_format']['json_schema']['schema']
        self.assertEqual(schema['properties']['assessments']['minItems'],1)
        self.assertEqual(schema['properties']['assessments']['maxItems'],1)
        self.assertEqual(schema['properties']['assessments']['items']['properties']['claim_id']['enum'],['development_1'])
        self.assertIn(json.dumps(schema,separators=(',',':')),body['messages'][0]['content'])
        evidence=json.loads(body['messages'][-1]['content'])['source_components']
        self.assertEqual(evidence[0]['claim_id'],'development_1')
        self.assertEqual([s['chunk_id'] for s in evidence[0]['sources']],['h1'])
        self.assertNotIn('Uncited-only',body['messages'][-1]['content'])
    def test_known_disputed_source_cannot_be_approved_by_a_draft(self):
        from backend.application.source_issues import HOLIDAY_PROVISION
        components=copy.deepcopy(self.components)
        components[0]['sources'][0]['provision_id']=HOLIDAY_PROVISION
        with self.assertRaisesRegex(ValueError,'Source wording requires review'):
            checked_claims(self.draft('A source explanation.'),components)
    def test_selected_sources_restore_exact_bytes_and_cannot_cross_concerns(self):
        components=[{'component_id':'c1','sources':[{'chunk_id':'a','parent_text':'The first complete rule.\nThe second complete rule.'}]}]
        supplied,lookup=source_options(components);option=supplied[0]['sources'][0]['quote_options'][1]
        draft={'paragraphs':[{'component_id':'c1','text':'A conditional explanation.','evidence':[{'quote_id':option['quote_id']}]}]}
        restored=selected_draft(draft,lookup)
        self.assertEqual(restored['paragraphs'][0]['evidence'],[{'chunk_id':'a','quote':'The second complete rule.'}])
        draft['paragraphs'][0]['component_id']='c2'
        with self.assertRaises(ValueError):selected_draft(draft,lookup)
        draft['paragraphs'][0]['component_id']='c1';draft['paragraphs'][0]['evidence'][0]['quote_id']='invented'
        with self.assertRaises(ValueError):selected_draft(draft,lookup)
    def setUp(self):
        self.components=[{'component_id':'c1','sources':[{'chunk_id':'h1','provision_id':'p1','document_id':'d1','citation_display':'Article 83','parent_text':'The normal hours of work shall not exceed eight hours per day.'}]}]
    def draft(self,text):return {'paragraphs':[{'component_id':'c1','text':text,'evidence':[{'chunk_id':'h1','quote':'normal hours of work shall not exceed eight hours per day.'}]}]}
    def test_known_unentailed_and_excluded_claims_fail_before_a_judge(self):
        for text in ['You are guaranteed to win your case and your employer can never dismiss you.','Your annulment is automatically granted.','You will receive nine million pesos tomorrow.']:
            with self.subTest(text=text),self.assertRaises(ValueError):checked_claims(self.draft(text),self.components)
    def test_written_numeric_facts_match_literal_quantities(self):
        self.assertEqual(numeric_facts('twenty-five days'),numeric_facts('25 days'))
        self.assertNotEqual(numeric_facts('nine million pesos'),numeric_facts('eight pesos'))
    def test_written_and_digit_ordinal_dates_match_without_accepting_a_new_date(self):
        self.assertEqual(numeric_facts('the twenty-fifth of December'),numeric_facts('December 25'))
        self.assertEqual(numeric_facts('the thirtieth of November'),numeric_facts('November 30th'))
        self.assertEqual(numeric_facts('the ninth of April'),numeric_facts('April 9th'))
        self.assertNotEqual(numeric_facts('December 25'),numeric_facts('the twenty-sixth of December'))
        self.assertEqual(numeric_facts('the twenty-fifth and thirtieth of December'),numeric_facts('December 25 and 30'))
        self.assertEqual(numeric_facts('one hundred and first'),numeric_facts('101st'))
    def test_equivalent_recorded_date_clears_numeric_check_but_an_invented_date_does_not(self):
        components=copy.deepcopy(self.components)
        text='The recorded date is the twenty-fifth of December.'
        components[0]['sources'][0]['parent_text']=text
        draft={'paragraphs':[{'component_id':'c1','text':'The recorded date is December 25.',
                'evidence':[{'chunk_id':'h1','quote':text}]}]}
        self.assertEqual(len(checked_claims(draft,components)),1)
        draft['paragraphs'][0]['text']='The recorded date is December 26.'
        with self.assertRaisesRegex(ValueError,'Uncited numeric detail'):checked_claims(draft,components)
    def test_judge_must_cover_each_claim_once_with_all_checks(self):
        claims=[{'claim_id':'c1'},{'claim_id':'c2'}];good=positive(claims)
        self.assertTrue(support_passed(good,claims))
        for mutate in ['omitted','duplicate','unsupported','qualification']:
            bad=copy.deepcopy(good)
            if mutate=='omitted':bad['assessments'].pop()
            elif mutate=='duplicate':bad['assessments'][1]['claim_id']='c1'
            elif mutate=='unsupported':bad['assessments'][1]['verdict']='unsupported'
            else:bad['assessments'][1]['qualifications_preserved']=False
            self.assertFalse(support_passed(bad,claims))
    def test_malformed_judge_cannot_approve_itself(self):
        with self.assertRaises(ValueError):support_passed({'approved':True},[{'claim_id':'c1'}])
    def test_malformed_provider_envelopes_and_redirects_are_safe(self):
        adapter=TogetherDevelopmentExplanation('mock','fictional-key')
        for response in [[],{'usage':None,'choices':[]},{'choices':[None]}, {'choices':[{'finish_reason':'stop','message':[]}]}]:
            opener=Mock();opener.open.return_value.__enter__=Mock(return_value=io.BytesIO(json.dumps(response).encode()));opener.open.return_value.__exit__=Mock(return_value=False)
            with patch('urllib.request.build_opener',return_value=opener),self.assertRaises(ValueError):adapter.complete('fictional',{'components':[]})
        opener=Mock();opener.open.side_effect=NormalizationUnavailable('redirect rejected')
        with patch('urllib.request.build_opener',return_value=opener),self.assertRaises(ValueError):adapter.complete('fictional',{'components':[]})

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp');self.store=HistoryStore(Path(self.tmp.name)/'history.sqlite3',codec=codec,maximum_turns=2)
        self.packet={'schema_version':'1.0','original_question_text':'Fictional saved salary question','result':{'route':'test'}}
    def tearDown(self):self.tmp.cleanup()
    def test_owner_isolation_and_saved_state_round_trip(self):
        ref=self.store.save('browser-a',self.packet)
        self.assertEqual(len(self.store.list('browser-a')),1);self.assertEqual(self.store.list('browser-b'),[])
        self.assertIsNone(self.store.get('browser-b',ref['conversation_id']))
        p=self.store.get('browser-a',ref['conversation_id'])['turns'][0]['packet']
        self.assertTrue(p['history']['saved']);self.assertEqual(p['history']['turn_id'],ref['turn_id'])
    def test_append_does_not_allow_another_owner_to_claim_a_thread(self):
        ref=self.store.save('a',self.packet)
        with self.assertRaises(ValueError):self.store.save('b',self.packet,ref['conversation_id'])
        self.store.save('a',self.packet,ref['conversation_id']);self.assertEqual(len(self.store.get('a',ref['conversation_id'])['turns']),2)
    def test_delete_is_scoped_and_cap_is_enforced(self):
        first=self.store.save('a',self.packet)
        self.store.save('a',self.packet);self.store.save('a',self.packet)
        self.assertEqual(len(self.store.list('a')),2);self.assertIsNone(self.store.get('a',first['conversation_id']))
        self.assertEqual(self.store.delete('b'),0);self.assertEqual(self.store.delete('a'),2)
    def test_expiry_and_corrupt_data_are_not_returned(self):
        ref=self.store.save('a',self.packet)
        with self.store.connect() as db:db.execute('UPDATE turns SET expires=?',('2000-01-01T00:00:00+00:00',))
        self.assertEqual(self.store.list('a'),[])
        ref=self.store.save('a',self.packet)
        with self.store.connect() as db:db.execute('UPDATE turns SET payload=?',(b'corrupt',))
        self.assertIsNone(self.store.get('a',ref['conversation_id']))
    def test_native_windows_storage_does_not_contain_plain_question(self):
        import os
        if os.name!='nt':self.skipTest('DPAPI test requires Windows')
        store=HistoryStore(Path(self.tmp.name)/'native.sqlite3');ref=store.save('a',self.packet)
        self.assertNotIn(self.packet['original_question_text'].encode(),store.path.read_bytes())
        self.assertIsNotNone(store.get('a',ref['conversation_id']))

class ControlTests(unittest.TestCase):
    def test_success_resets_the_consecutive_outage_streak(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as directory:
            ledger=UsageLedger(Path(directory)/'recovery.sqlite3')
            for outcome in ['unavailable','completed','unavailable','unavailable']:
                rid=ledger.reserve('generation','openai/gpt-oss-120b',10,10)
                ledger.settle(rid,'openai/gpt-oss-120b',{},outcome)
            self.assertIsInstance(ledger.reserve('generation','openai/gpt-oss-120b',10,10),str)
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp')
    def tearDown(self):self.tmp.cleanup()
    def test_idempotence_is_scoped_and_conflicts_are_rejected(self):
        reg=RequestRegistry();ctx,_=reg.begin('a','id',{'question_text':'a'})
        with self.assertRaises(RequestError):reg.begin('a','id',{'question_text':'a'})
        reg.finish(ctx,{'response':'cached'})
        self.assertEqual(reg.begin('a','id',{'question_text':'a'})[1],{'response':'cached'})
        with self.assertRaises(RequestError):reg.begin('a','id',{'question_text':'different'})
        self.assertIsNone(reg.begin('b','id',{'question_text':'a'})[1])
    def test_cancel_tombstone_prevents_a_racing_export(self):
        reg=RequestRegistry();reg.cancel('a','id')
        with self.assertRaises(RequestError) as caught:reg.begin('a','id',{'question_text':'a'})
        self.assertEqual(caught.exception.code,'request_canceled')
    def test_cancellation_closes_an_active_connection(self):
        ctx=RequestContext('a','id');connection=Mock();ctx.connections.append(connection);ctx.cancel()
        connection.sock.shutdown.assert_called_once();connection.close.assert_called_once()
        with self.assertRaises(RequestError):ctx.check()
    def test_daily_request_cap_and_estimated_cost_settlement(self):
        ledger=UsageLedger(Path(self.tmp.name)/'ledger.sqlite3',maximum_calls=2)
        a=ledger.reserve('generation','openai/gpt-oss-120b',100,100)
        ledger.settle(a,'openai/gpt-oss-120b',{'prompt_tokens':100,'completion_tokens':20},'completed')
        ledger.reserve('support','openai/gpt-oss-120b',100,100)
        with self.assertRaises(ProviderStopped):ledger.reserve('generation','openai/gpt-oss-120b',100,100)
        self.assertEqual(ledger.summary()['provider_requests'],2);self.assertFalse(ledger.summary()['billing_verified'])
    def test_unknown_pricing_and_repeated_failures_stop_new_exports(self):
        ledger=UsageLedger(Path(self.tmp.name)/'ledger.sqlite3')
        with self.assertRaises(ProviderStopped):ledger.reserve('test','unknown-model',100,100)
        for _ in range(3):
            rid=ledger.reserve('generation','openai/gpt-oss-120b',100,100);ledger.settle(rid,'openai/gpt-oss-120b',{},'unavailable')
        with self.assertRaises(ProviderStopped) as caught:ledger.reserve('test','openai/gpt-oss-120b',100,100)
        self.assertEqual(caught.exception.safe_code,'provider_circuit_open')
    def test_transport_rejects_other_hosts_before_any_connection(self):
        transport=CancellableTransport(RequestContext('a','id'),Mock(),'test')
        with patch('http.client.HTTPSConnection') as connection,self.assertRaises(ProviderStopped):transport(Request('https://example.com/steal',data=b'{}'),20)
        connection.assert_not_called()
    def test_provider_http_errors_have_safe_diagnostics_without_returning_the_body(self):
        body=json.dumps({'model':'openai/gpt-oss-120b','max_tokens':100}).encode()
        for status,expected in [(400,'provider_http_400'),(503,'provider_http_503'),(429,'provider_rate_limited'),(401,'provider_auth_failed')]:
            with self.subTest(status=status):
                transport=CancellableTransport(RequestContext('a','id'),Mock(),'test')
                with patch('http.client.HTTPSConnection') as connection:
                    response=connection.return_value.getresponse.return_value
                    response.status=status
                    with self.assertRaises(ProviderStopped) as caught:transport(Request('https://api.together.ai/v1/chat/completions',data=body),20)
                    self.assertEqual(caught.exception.safe_code,expected)
                    response.read.assert_not_called()
    def test_provider_timings_identify_stage_without_question_or_credentials(self):
        context=RequestContext('owner','timing-test');ledger=Mock()
        body=json.dumps({'model':'openai/gpt-oss-120b','max_tokens':100,
                         'response_format':{'json_schema':{'name':'explanation_support'}}}).encode()
        with patch('http.client.HTTPSConnection') as connection:
            response=connection.return_value.getresponse.return_value
            response.status=200;response.read.return_value=b'{"usage":{}}'
            CancellableTransport(context,ledger,'explanation_generation')(Request('https://api.together.ai/v1/chat/completions',data=body),20)
        self.assertEqual(len(context.calls),1)
        self.assertEqual(set(context.calls[0]),{'stage','model','elapsed_ms'})
        self.assertEqual(context.calls[0]['stage'],'explanation_support')
        self.assertGreaterEqual(context.calls[0]['elapsed_ms'],0)

class ApplicationRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.verifier=load_runtime()
    def provider(self):
        p=Mock();p.name='test';p.model='mock'
        p.complete.side_effect=lambda question,pre: {'paragraphs':[{'component_id':c['component_id'],'text':'The recorded source describes the general rule; its application depends on the relevant facts.',
            'evidence':[{'chunk_id':c['sources'][0]['chunk_id'],'quote':c['sources'][0]['parent_text'][:120]}]} for c in pre['components']]}
        p.assess.side_effect=lambda question,claims,components:positive(claims)
        return p
    def test_local_only_skips_both_providers_but_keeps_classification(self):
        norm,provider=Mock(),self.provider()
        service=ApplicationService(verifier=self.verifier,normalizer=ConditionalNormalizer(norm),development_provider=provider)
        packet=service.chat({'question_text':'My private employer has not paid my salary.','use_ai':False})
        self.assertEqual(packet['result']['routing']['predicted_primary'],'labor');self.assertEqual(packet['explanation']['reason'],'local_only')
        provider.complete.assert_not_called();norm.complete.assert_not_called()
    def test_disputed_source_stays_inspectable_but_is_not_offered_to_generation(self):
        from backend.application.source_issues import HOLIDAY_PROVISION
        provider=self.provider()
        service=ApplicationService(verifier=self.verifier,normalizer=ConditionalNormalizer(),development_provider=provider)
        packet=service.chat({'question_text':'A private-sector employer refused Christmas holiday pay although no work was performed. What holiday-pay rules apply?'})
        self.assertEqual(packet['explanation']['status'],'generated')
        offered=provider.complete.call_args.args[1]['components']
        self.assertTrue(all(s['provision_id']!=HOLIDAY_PROVISION for c in offered for s in c['sources']))
        held=[h for c in packet['result']['components'] for h in c['candidates'] if h['provision_id']==HOLIDAY_PROVISION]
        self.assertTrue(held)
        self.assertTrue(all(h['explanation_restriction'] for h in held))
    def test_ambiguous_religious_source_is_inspectable_but_never_offered(self):
        from backend.application.source_issues import RELIGIOUS_SCHEDULING_PROVISION
        provider=self.provider()
        service=ApplicationService(verifier=self.verifier,normalizer=ConditionalNormalizer(),development_provider=provider)
        packet=service.chat({'question_text':'I am a private employee asking about a religious rest-day preference. What notice and exception conditions are recorded?'})
        held=[h for c in packet['result']['components'] for h in c['candidates'] if h['provision_id']==RELIGIOUS_SCHEDULING_PROVISION]
        self.assertTrue(held)
        self.assertTrue(all(h['explanation_restriction'] for h in held))
        if provider.complete.called:
            offered=provider.complete.call_args.args[1]['components']
            self.assertTrue(all(s['provision_id']!=RELIGIOUS_SCHEDULING_PROVISION for c in offered for s in c['sources']))

    def test_unsupported_judgment_withholds_the_entire_draft(self):
        provider=self.provider();provider.assess.side_effect=lambda q,claims,c:{'assessments':[{**r,'verdict':'unsupported'} for r in positive(claims)['assessments']]}
        service=ApplicationService(verifier=self.verifier,normalizer=ConditionalNormalizer(),development_provider=provider)
        p=service.chat({'question_text':'Private employee ako. What are normal working hours?'})
        self.assertEqual(p['explanation']['reason'],'claim_support_failed');self.assertEqual(p['explanation']['claims'],[])
    def test_live_referral_fields_and_missing_sources_are_explained(self):
        service=ApplicationService(verifier=self.verifier,normalizer=ConditionalNormalizer())
        p=service.chat({'question_text':'My bank charged my account a hidden fee.','use_ai':False})
        self.assertIn('REF_BSP_CAM',{r['id'] for r in p['referrals']})
        p=service.chat({'question_text':'My private employer has not paid my final pay.','use_ai':False})
        documents={h['document_id'] for c in p['result']['components'] for h in c['candidates']}
        self.assertIn('DOLE_FINAL_PAY_COE_NEWS_2026',documents)
        self.assertNotIn('DOLE_LA_06_20',documents)
        self.assertFalse(p['result']['display_allowed'])
    def test_health_and_another_question_work_while_generation_waits(self):
        provider=self.provider();entered=threading.Event();release=threading.Event();complete=provider.complete.side_effect
        def wait(q,p):entered.set();release.wait(5);return complete(q,p)
        provider.complete.side_effect=wait
        service=ApplicationService(verifier=self.verifier,normalizer=ConditionalNormalizer(),development_provider=provider,use_controls=True)
        finished=[];errors=[]
        def ask():
            try:finished.append(service.chat({'question_text':'Private employee ako. What are normal working hours?','request_id':'long'},session='a'))
            except RequestError as e:errors.append(e.code)
        thread=threading.Thread(target=ask);thread.start()
        try:
            self.assertTrue(entered.wait(10));start=time.monotonic();self.assertEqual(service.health()['status'],'ready');self.assertLess(time.monotonic()-start,.2)
            p=service.chat({'question_text':'What is the weather tomorrow?','use_ai':False},session='b')
            self.assertEqual(p['result']['routing']['predicted_primary'],'out_of_scope')
            service.cancel('a','long')
        finally:release.set();thread.join(10)
        self.assertEqual(finished,[]);self.assertEqual(errors,['request_canceled'])
    def test_full_citation_labels_distinguish_ambiguous_provisions(self):
        service=ApplicationService(verifier=self.verifier,normalizer=ConditionalNormalizer())
        seen={}
        for r in self.verifier.records.values():
            label=service._labels[r['chunk_id']]
            self.assertNotIn(label,seen) if label not in seen else self.assertEqual(seen[label],r['provision_id'])
            seen[label]=r['provision_id']

if __name__=='__main__':unittest.main()
