"""Real loopback HTTP history/cookie boundaries; no external provider calls."""
import json
from http.client import HTTPConnection
from pathlib import Path
import tempfile
import threading
import unittest
from backend.application.history import HistoryStore
from backend.application.server import ApplicationServer
from backend.application.service import ApplicationService
from backend.application.test_repairs import codec
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime

ROOT=Path(__file__).resolve().parents[2]

class HistoryHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp')
        cls.service=ApplicationService(verifier=load_runtime(),normalizer=ConditionalNormalizer(),history_store=HistoryStore(Path(cls.tmp.name)/'history.sqlite3',codec=codec),use_controls=True)
        cls.service.session_key=b'local-test-session-signing-key-32'[:32]
        cls.server=ApplicationServer(('127.0.0.1',0),cls.service,allowed_origins=['http://127.0.0.1:5173'])
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()
    def request(self,method,path,body=None,cookie=None,origin=None):
        c=HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        headers={}
        if body is not None:body=json.dumps(body);headers['Content-Type']='application/json'
        if cookie:headers['Cookie']=cookie
        if origin:headers['Origin']=origin
        c.request(method,path,body,headers);r=c.getresponse();result=(r.status,dict(r.getheaders()),json.loads(r.read()));c.close();return result
    def session(self):
        _,headers,_=self.request('GET','/api/health')
        self.assertIn('HttpOnly',headers['Set-Cookie']);self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        return headers['Set-Cookie'].split(';',1)[0]
    def test_history_opt_in_export_and_owner_isolation(self):
        a,b=self.session(),self.session()
        _,_,temporary=self.request('POST','/api/chat',{'question_text':'What is the weather tomorrow?','use_ai':False},a)
        self.assertFalse(temporary['history']['saved'])
        self.assertEqual(self.request('GET','/api/history',cookie=a)[2]['conversations'],[])
        status,_,saved=self.request('POST','/api/chat',{'question_text':'What is the weather tomorrow?','use_ai':False,'save_history':True},a)
        self.assertEqual(status,200);cid=saved['history']['conversation_id']
        self.assertEqual(self.request('GET','/api/history/'+cid+'/export',cookie=a)[0],200)
        self.assertEqual(self.request('GET','/api/history/'+cid,cookie=b)[0],404)
        self.assertEqual(self.request('DELETE','/api/history/'+cid,cookie=b)[2]['deleted_turns'],0)
        self.assertEqual(self.request('DELETE','/api/history/'+cid,cookie=a)[2]['deleted_turns'],1)
    def test_cookie_tampering_does_not_select_another_history_owner(self):
        cookie=self.session();forged=cookie[:-1]+('0' if cookie[-1]!='0' else '1')
        _,headers,_=self.request('GET','/api/history',cookie=forged)
        self.assertIn('Set-Cookie',headers)
    def test_cancel_is_scoped_and_blocks_the_same_pending_request_id(self):
        a,b=self.session(),self.session()
        self.assertEqual(self.request('POST','/api/cancel',{'request_id':'racing-test'},a)[0],200)
        self.assertEqual(self.request('POST','/api/chat',{'question_text':'What is the weather tomorrow?','request_id':'racing-test','use_ai':False},a)[0],499)
        self.assertEqual(self.request('POST','/api/chat',{'question_text':'What is the weather tomorrow?','request_id':'racing-test','use_ai':False},b)[0],200)
    def test_unknown_options_and_cross_origin_writes_are_rejected(self):
        a=self.session()
        for payload in [{'question_text':'x','use_ai':'false'},{'question_text':'x','save_history':1},{'question_text':'x','display_allowed':True}]:
            self.assertEqual(self.request('POST','/api/chat',payload,a)[0],400)
        self.assertEqual(self.request('DELETE','/api/history',cookie=a,origin='https://untrusted.example')[0],403)
    def test_client_ids_deduplicate_completed_requests(self):
        a=self.session();payload={'question_text':'What is the weather tomorrow?','use_ai':False,'save_history':True,'request_id':'dedupe'}
        first=self.request('POST','/api/chat',payload,a)[2];second=self.request('POST','/api/chat',payload,a)[2]
        self.assertEqual(first['history']['turn_id'],second['history']['turn_id'])
        self.assertEqual(len(self.request('GET','/api/history',cookie=a)[2]['conversations']),1)

if __name__=='__main__':unittest.main()
