"""Readable review of every response; no status-only correctness claims."""
import json,sys
from pathlib import Path
target=Path(sys.argv[1]);lo=int(sys.argv[2]) if len(sys.argv)>2 else 1;hi=int(sys.argv[3]) if len(sys.argv)>3 else 100
rows=[json.loads(s) for s in (target/'observations.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
for r in rows:
    if not lo<=int(r['case']['case_id'].split('_')[-1])<=hi:continue
    print('\n'+r['case']['case_id']+' '+r['case']['question_text'])
    if 'normalized' not in r:print('ERROR',r.get('error'));continue
    p=r['normalized']['packet'];e=p['explanation']
    print('ASSESSMENT',r['normalized']['assessment']['issues'],'AI',e['status'],e.get('reason'),e.get('validation_failure',''),e.get('failure_code',''))
    for c in (p.get('result') or {}).get('components',[]):
        print('COMPONENT',c['component_id'],c['query'],'SOURCES',[(h['provision_id'],h.get('answer_context_eligible')) for h in c['candidates'][:2]])
    for c in e.get('claims',[]):print('CLAIM',c['component_id'],c['text'],'CITES',[x['provision_id'] for x in c['citations']])
    if e.get('unanswered_components'):print('UNANSWERED',e['unanswered_components'])
    if e['status'] not in {'generated','partially_generated','verified'}:
        response=p.get('response') or {}
        print('RESPONSE',json.dumps({k:v for k,v in response.items() if k!='quotes'},ensure_ascii=False))
