"""Offline synthetic probes. Outputs preserve every failure, no provider calls."""
import argparse,collections,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',default='development_cases.json');p.add_argument('--out',required=True);p.add_argument('--raw',action='store_true');a=p.parse_args()
 cases=json.loads((HERE/a.cases).read_text(encoding='utf-8'))
 if a.raw:
  sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
  import joblib
  from classifier_runtime import predict_records
  current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text());bundle=joblib.load(ROOT/current['classifier']/'classifier.joblib')
 else:
  from backend.application.service import ApplicationService
  from backend.normalization import ConditionalNormalizer
  from backend.terminal_test import load_runtime
  service=ApplicationService(verifier=load_runtime(),normalizer=ConditionalNormalizer())
 results=[]
 for c in cases:
  start=time.perf_counter()
  if a.raw:
   row=predict_records(bundle,[{'question_id':c['id'],'question_text':c['q']}])[0];route=row
   flow='clarify' if route['routing_action']=='clarify' else 'referral' if route['routing_action']=='refer_out_of_scope' else 'local_sources'
   packet=row;exact=True;headings=[];llm=0
  else:
   packet=service.chat({'question_text':c['q'],'use_ai':False});r=packet['result'];route=r['routing'];kind=packet['response']['kind']
   flow='clarify' if kind=='clarification' else 'referral' if kind=='referral' else 'local_sources'
   quotes=packet['response']['quotes'];exact=all(q['quote'] in service.verifier.records[q['chunk_id']]['parent_text'] for q in quotes)
   headings=[service.verifier.records[q['chunk_id']]['heading'] for q in quotes]
   llm=packet['explanation']['llm_calls']+(packet.get('normalization') or {}).get('llm_calls',0)
  results.append({'case':c,'primary':route['predicted_primary'],'scope':route['predicted_scope'],'flow':flow,
   'labels_correct':all(route['predicted_'+k]==c[k] for k in ['primary','scope'] if k in c),
   'flow_correct':flow==c['flow'],'exact_quotes':exact,'headings':headings,'llm_calls':llm,'ms':round((time.perf_counter()-start)*1000,1),'packet':packet})
  if len(results)%25==0:print(f'Completed {len(results)}/{len(cases)}',flush=True)
 target=HERE/a.out;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 summary={'count':len(results),'labeled':sum('primary' in r['case'] for r in results),'labels_correct':sum(r['labels_correct'] for r in results if 'primary' in r['case']),
  'flow_correct':sum(r['flow_correct'] for r in results),'exact_quote_cases':sum(r['exact_quotes'] for r in results),'provider_calls':sum(r['llm_calls'] for r in results),
  'quoted_responses':sum(bool(r['headings']) for r in results),'median_ms':statistics.median(r['ms'] for r in results),
  'failures':[{'id':r['case']['id'],'q':r['case']['q'],'expected':[r['case'].get('primary'),r['case'].get('scope'),r['case']['flow']],
  'actual':[r['primary'],r['scope'],r['flow']],'reason':r['packet'].get('result',r['packet']).get('routing',r['packet']).get('reason')} for r in results if not(r['labels_correct'] and r['flow_correct'])]}
 target.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
