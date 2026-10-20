"""Actual loopback website/API integration; AI off, synthetic questions only."""
import http.cookiejar,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
base='http://127.0.0.1:8776';opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def get(path):
 with opener.open(base+path,timeout=10) as r:return json.load(r)
health=get('/api/health');before=get('/api/status')['usage']['provider_requests']
cases=[('Late ang salary ko.','retrieve_supported_evidence'),
 ('Government employee ako. Hindi binayaran ang overtime ko.','refer_out_of_scope'),
 ('Sira yung binili kong phone at ayaw palitan ng shop.','retrieve_supported_evidence'),
 ('My private company owes overtime. Separately my bank froze my account.','retrieve_supported_components'),
 ('How do I cook sinigang for four people?','refer_out_of_scope'),
 ('qzxw zzpp pqqr','clarify')]
results=[]
for question,expected in cases:
 req=urllib.request.Request(base+'/api/chat',data=json.dumps({'question_text':question,'use_ai':False,'save_history':False}).encode(),
  headers={'Content-Type':'application/json','Origin':'http://127.0.0.1:5174'},method='POST')
 with opener.open(req,timeout=15) as response:packet=json.load(response)
 result=packet['result'];row={'question_text':question,'route':result['routing']['routing_action'],
  'source_count':sum(len(c['candidates']) for c in result['components']),'response_kind':packet['response']['kind'],
  'llm_calls':packet['explanation']['llm_calls'],'network_requests':packet['network_requests'],
  'nonempty_response':bool(packet['response']['paragraphs']),'local_latency_ms':packet['total_query_ms']}
 assert row['route']==expected and row['nonempty_response'] and row['llm_calls']==0 and row['network_requests']==[]
 if expected.startswith('retrieve'):assert row['source_count']>0
 results.append(row)
after=get('/api/status')['usage']['provider_requests'];assert before==after
current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text())
assert health['classifier']==current['classifier'] and health['verifier']==Path(current['verifier']).name
report={'status':'passed','website':'http://127.0.0.1:5174/','classifier':health['classifier'],'retrieval':health['retrieval'],
 'verifier':health['verifier'],'development_explanations_configured':health['development_explanations_enabled'],
 'external_provider_requests_added':after-before,'cases':results}
(HERE/'api-smoke.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
