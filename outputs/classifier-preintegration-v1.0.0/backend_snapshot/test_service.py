"""Classifier adapter and HTTP boundary software checks; no accuracy claims."""
from __future__ import annotations
import copy
import http.client
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

from .contracts import MAX_BODY_BYTES, MAX_CHARACTERS, RESPONSE_SCHEMA, RequestError, strict_json, validate_contract, validate_request
from .service import ROOT, DEFAULT_CONFIG, ArtifactError, ClassifierService, inside, sha
from .server import ClassifierHTTPServer, validate_origin


class ContractTests(unittest.TestCase):
    def test_unknown_fields_and_overrides_are_rejected(self):
        for key in ['thresholds','primary_label','model_path','deployment_allowed','reviews','answer_text']:
            with self.subTest(key=key), self.assertRaises(RequestError):
                validate_request({'question_text':'test',key:True})

    def test_non_string_input_is_rejected(self):
        for value in [None,False,1,[],{}]:
            with self.subTest(value=value),self.assertRaises(RequestError):validate_request({'question_text':value})
        for value in [None,[],False,42]:
            with self.assertRaises(RequestError):validate_request(value)

    def test_controls_surrogates_and_size_are_rejected(self):
        for text in ['x\0y','x\x7fy','x\ud800y','x'*(MAX_CHARACTERS+1)]:
            with self.assertRaises(RequestError):validate_request({'question_text':text})
        text='line one\nline two\twith tabs'
        self.assertEqual(validate_request({'question_text':text})[0],text)

    def test_request_ids_cannot_inject_headers_or_log_lines(self):
        for rid in [None,1,'bad\r\nheader','x'*65,'']:
            with self.assertRaises(RequestError):validate_request({'question_text':'test','request_id':rid})
        self.assertEqual(validate_request({'question_text':'test','request_id':'test:1-a.b_2'})[1],'test:1-a.b_2')

    def test_duplicate_nonfinite_and_malformed_json_are_rejected(self):
        for value in ['{"question_text":"x","question_text":"y"}','{"x":NaN}','{"x":Infinity}',
                      '{"x":1e999}','{"question_text":','[']:
            with self.assertRaises(RequestError):strict_json(value)

    def test_operator_paths_stay_in_workspace(self):
        self.assertEqual(inside(ROOT,'backend/classifier').parent,ROOT/'backend')
        for name in ['../outside','C:/Windows',None,'']:
            with self.assertRaises(ArtifactError):inside(ROOT,name)

    def test_origins_are_exact_not_wildcards_or_paths(self):
        self.assertEqual(validate_origin('http://localhost:5173'),'http://localhost:5173')
        for origin in ['*','null','file:///tmp','http://localhost:5173/','https://a.example/path',
                       'https://user:password@a.example','https://a.example\r\nx:y']:
            with self.assertRaises(ValueError):validate_origin(origin)


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service=ClassifierService()

    def prediction(self,text):
        return self.service.classify({'question_text':text})

    def test_health_describes_implementation_without_claiming_evaluation(self):
        result=self.service.health()
        self.assertEqual(result['status'],'ready')
        for key in ['formal_evaluation_completed','website_integration_completed','llm_connected',
                    'answer_generation_allowed','deployment_allowed']:self.assertFalse(result[key])

    def test_supported_component_returns_a_request_not_a_legal_answer(self):
        result=self.prediction('My private employer owes overtime pay.')
        validate_contract(result,RESPONSE_SCHEMA)
        self.assertEqual(result['classification']['primary_label'],'labor')
        self.assertTrue(result['permissions']['retrieval_allowed'])
        self.assertTrue(result['routing']['retrieval_requests'])
        self.assertNotIn('answer_text',result)
        self.assertFalse(result['permissions']['answer_generation_allowed'])

    def test_partial_component_excludes_insurance_from_retrieval(self):
        result=self.prediction('A shop refuses my warranty. My insurer denied a claim. How do I raise each dispute?')
        self.assertEqual(result['classification']['scope_label'],'partially_supported')
        self.assertTrue(result['routing']['excluded_components'])
        self.assertTrue(all('insur' not in r['query'] for r in result['routing']['retrieval_requests']))
        self.assertTrue(all(not c['retrieval_allowed'] for c in result['routing']['excluded_components']))
        self.assertEqual(len({c['component_id'] for c in result['components']}),len(result['components']))

    def test_referral_only_has_no_retrieval_and_contacts_stay_candidates(self):
        result=self.prediction('My government employer delayed my salary.')
        self.assertEqual(result['routing']['action'],'refer_out_of_scope')
        self.assertEqual(result['routing']['retrieval_requests'],[])
        self.assertFalse(result['permissions']['retrieval_allowed'])
        self.assertTrue(result['routing']['referral_candidates'])
        for r in result['routing']['referral_candidates']:
            self.assertTrue(r['candidate_only']);self.assertTrue(r['requires_contact_refresh'])
            self.assertNotIn('email',r);self.assertNotIn('phone',r)

    def test_vague_and_empty_inputs_clarify_without_retrieval(self):
        for text in ['', '  ', 'My employer has not paid my salary.', 'They refuse to refund my payment.']:
            with self.subTest(text=text):
                result=self.prediction(text)
                self.assertEqual(result['routing']['action'],'clarify')
                self.assertTrue(result['routing']['clarification_question'])
                self.assertEqual(result['routing']['retrieval_requests'],[])

    def test_original_unicode_text_and_request_id_are_preserved(self):
        text='  Municipal goverment employe here, salry delayd.\nWhat civil servce remedy applies?  '
        result=self.service.classify({'question_text':text,'request_id':'local.test-1'})
        self.assertEqual(result['question_text'],text)
        self.assertEqual(result['request_id'],'local.test-1')
        self.assertEqual(len(result['question_sha256']),64)
        self.assertEqual(result['routing']['action'],'refer_out_of_scope')

    def test_no_outbound_network_or_semantic_download_is_needed(self):
        with (patch('socket.create_connection',side_effect=AssertionError('outbound connection')),
              patch('semantic_encoder.encoder',side_effect=AssertionError('semantic encoder'))):
            self.prediction('A store refuses my kettle warranty.')

    def test_response_contract_rejects_changed_types_and_live_permissions(self):
        result=self.prediction('A store refuses my kettle warranty.')
        for mutate in [lambda r:r['permissions'].update(deployment_allowed=True),
                       lambda r:r['classification'].update(primary_confidence=True),
                       lambda r:r['classification'].update(scope_confidence=float('nan')),
                       lambda r:r.update(answer_text='unchecked')]:
            altered=copy.deepcopy(result);mutate(altered)
            with self.assertRaises(ValueError):validate_contract(altered,RESPONSE_SCHEMA)

    def test_probabilities_and_invalid_route_fail_closed(self):
        from classifier_runtime import predict_records
        raw=predict_records(self.service.bundle,[{'question_text':'A store refuses my kettle warranty.'}])[0]
        for mutate in [lambda p:p.update(primary_confidence=.01),lambda p:p['scope_probabilities'].update(unsupported=float('nan')),
                       lambda p:p.update(routing_action='answer_now'),lambda p:p.update(deployment_allowed=True),
                       lambda p:p.update(predicted_scope='unsupported')]:
            altered=copy.deepcopy(raw);mutate(altered)
            with self.assertRaises(ArtifactError):ClassifierService.response(altered,'test')

    def test_artifact_mutation_is_checked_on_every_call(self):
        real=sha
        runtime=ROOT/'dataset/pipelines/item10/scope_constraints.py'
        with patch('backend.classifier.service.sha',side_effect=lambda p:'0'*64 if p==runtime else real(p)):
            with self.assertRaises(ArtifactError):self.prediction('A store refuses my warranty.')
            with self.assertRaises(ArtifactError):self.service.health()

    def test_bad_manifest_is_rejected_before_executable_model_load(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as folder:
            config=json.loads(DEFAULT_CONFIG.read_text());config['artifact_checksums_sha256']='0'*64
            path=Path(folder)/'config.json';path.write_text(json.dumps(config))
            with patch('joblib.load',side_effect=AssertionError('unverified pickle loaded')):
                with self.assertRaises(ArtifactError):ClassifierService(path)

    def test_incompatible_dependencies_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as folder:
            config=json.loads(DEFAULT_CONFIG.read_text());config['dependencies']['joblib']='invalid'
            path=Path(folder)/'config.json';path.write_text(json.dumps(config))
            with self.assertRaises(ArtifactError):ClassifierService(path)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service=ClassifierService()
        cls.server=ClassifierHTTPServer(('127.0.0.1',0),cls.service,allowed_origins=['http://localhost:5173'])
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.port=cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=5)

    def call(self,method='POST',path='/v1/classify',body=None,headers=None):
        if body is None:body=json.dumps({'question_text':'A store refuses my kettle warranty.'})
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=10)
        try:
            connection.request(method,path,body=body,headers={'Content-Type':'application/json',**(headers or {})})
            response=connection.getresponse();data=response.read()
            return response.status,dict(response.getheaders()),json.loads(data) if data else None
        finally:connection.close()

    def test_real_http_classification_uses_versioned_contract(self):
        status,headers,data=self.call()
        self.assertEqual(status,200);validate_contract(data,RESPONSE_SCHEMA)
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(headers['X-Request-ID'],data['request_id'])

    def test_read_only_health_and_contract_endpoints(self):
        for path in ['/health','/v1/contract']:
            status,_,data=self.call('GET',path)
            self.assertEqual(status,200);self.assertEqual(data['schema_version'],'1.0')
        self.assertEqual(self.call('GET','/v1/contract')[2]['response'],RESPONSE_SCHEMA)

    def test_unknown_endpoint_methods_and_query_overrides_are_rejected(self):
        for method,path,code in [('POST','/unknown',404),('GET','/v1/classify',405),
                                 ('PUT','/v1/classify',405),('POST','/health',405),
                                 ('POST','/v1/classify?threshold=0',400)]:
            self.assertEqual(self.call(method,path)[0],code)

    def test_origin_allowlist_and_preflight(self):
        status,headers,_=self.call(headers={'Origin':'http://localhost:5173'})
        self.assertEqual(status,200);self.assertEqual(headers['Access-Control-Allow-Origin'],'http://localhost:5173')
        status,headers,_=self.call(headers={'Origin':'https://untrusted.example'})
        self.assertEqual(status,403);self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertEqual(self.call('OPTIONS',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST'})[0],200)
        self.assertEqual(self.call('OPTIONS',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'DELETE'})[0],405)

    def test_json_errors_invalid_utf8_and_unsupported_content_type(self):
        for body in ['{"question_text":', '{"question_text":"a","question_text":"b"}',b'\xff']:
            self.assertEqual(self.call(body=body)[0],400)
        self.assertEqual(self.call(headers={'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.call(headers={'Content-Encoding':'gzip'})[0],415)

    def test_oversized_request_is_rejected(self):
        self.assertEqual(self.call(body='x'*(MAX_BODY_BYTES+1))[0],413)
        self.assertEqual(self.call(body=json.dumps({'question_text':'x'*(MAX_CHARACTERS+1)}))[0],413)

    def test_duplicate_or_chunked_lengths_are_rejected(self):
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        try:
            connection.putrequest('POST','/v1/classify')
            connection.putheader('Content-Length','0');connection.putheader('Content-Length','0')
            connection.putheader('Content-Type','application/json');connection.endheaders()
            response=connection.getresponse();self.assertEqual(response.status,400);response.read()
        finally:connection.close()
        self.assertEqual(self.call(headers={'Transfer-Encoding':'chunked'})[0],400)

    def test_model_failure_returns_no_traceback_question_or_paths(self):
        with patch.object(self.service,'classify',side_effect=RuntimeError('C:/private/file secret question')):
            status,_,data=self.call()
        self.assertEqual(status,500)
        self.assertNotIn('private',json.dumps(data));self.assertNotIn('secret',json.dumps(data))

    def test_integrity_failure_returns_unavailable(self):
        with patch.object(self.service,'classify',side_effect=ArtifactError('bad checksum')):
            self.assertEqual(self.call()[0],503)

    def test_connection_limit_returns_busy(self):
        server=ClassifierHTTPServer(('127.0.0.1',0),self.service,maximum_connections=1)
        self.assertTrue(server.slots.acquire(blocking=False))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        connection=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=5)
        try:
            connection.request('GET','/health')
            response=connection.getresponse();self.assertEqual(response.status,503);response.read()
        finally:
            connection.close();server.slots.release();server.shutdown();server.server_close();thread.join(timeout=5)

    def test_server_cannot_bind_public_interface(self):
        with self.assertRaises(ValueError):ClassifierHTTPServer(('0.0.0.0',0),self.service)


if __name__=='__main__':
    unittest.main(verbosity=2)
