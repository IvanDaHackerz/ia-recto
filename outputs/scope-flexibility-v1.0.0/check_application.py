"""Scope-wide local application checks; provider methods cannot run."""
import cProfile,json,pstats,socket,statistics,sys,time
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from backend.terminal_test import load_runtime
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.application.development_explanation import source_options,prompt_sources
from contrast_cases import CASES
v=load_runtime();wording=Mock();explanation=Mock()
service=ApplicationService(verifier=v,normalizer=ConditionalNormalizer(wording),development_provider=explanation)
cases=[json.loads(l) for l in (HERE/'development.jsonl').read_text(encoding='utf-8').splitlines()]
cases += [{'case_id':f'contrast.{k}.{i}','question_text':q} for k,values in CASES.items() for i,q in enumerate(values)]
results=[];payloads=[];profile=cProfile.Profile();profile.enable()
with patch('socket.socket',side_effect=AssertionError('No network permitted in local diagnostics')):
 for case in cases:
  packet=service.chat({'question_text':case['question_text'],'use_ai':False})
  result=packet['result'];route=result['routing'];components=result['components'];response=packet['response']
  checks={'nonempty_response':bool(response['paragraphs']),'no_external_calls':packet['network_requests']==[],
   'no_ai_claim':not response['ai_generated'],'legal_gates_closed':not any(result[k] for k in ['display_allowed','answer_generation_allowed','deployment_allowed']),
   'source_integrity':all(not v.check_candidate(h,c['allowed_domain']) for c in components for h in c['candidates'])}
  results.append({'case_id':case['case_id'],'question_text':case['question_text'],'routing_action':route['routing_action'],
   'primary':route['predicted_primary'],'scope':route['predicted_scope'],'candidate_count':sum(len(c['candidates']) for c in components),
   'response_kind':response['kind'],'checks':checks,'passed':all(checks.values()),'total_query_ms':packet['total_query_ms']})
  if len(payloads)<12 and components and components[0]['candidates']:
   comp=[{'component_id':c['component_id'],'sources':[{k:h[k] for k in ['chunk_id','citation_display','parent_text','conditions']} for h in c['candidates'][:3]]} for c in components]
   expanded,_=source_options(comp);compact=prompt_sources(expanded)
   payloads.append({'case_id':case['case_id'],'source_characters':len(json.dumps(expanded)),
    'compact_source_characters':len(json.dumps(compact)),'full_sources_preserved':all(a['parent_text']==b['parent_text'] for ac,bc in zip(expanded,compact) for a,b in zip(ac['sources'],bc['sources']))})
wording.complete.assert_not_called();explanation.complete.assert_not_called();profile.disable()
with (HERE/'application-profile.txt').open('w') as f:pstats.Stats(profile,stream=f).sort_stats('cumtime').print_stats(25)
times=sorted(r['total_query_ms'] for r in results)
report={'provenance':'Synthetic inspected development checks, application layer; no provider/LLM evaluation',
 'count':len(results),'passed':sum(r['passed'] for r in results),'network_calls':0,'median_ms_profiled':statistics.median(times),
 'p95_ms_profiled':times[int(.95*len(times))-1],'payload_measurements':payloads,'records':results}
(HERE/'application-check.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in {'records','payload_measurements'}},indent=2))
