"""Exercise the actual application service locally without any provider calls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer

def run(target,split):
    base=Path(__file__).resolve().parent
    if target.exists():raise SystemExit('Refusing to overwrite a run')
    cases=json.loads((base/'cases.json').read_text(encoding='utf-8'))
    manifest=json.loads((base/'manifest.json').read_text())
    assert hashlib.sha256((base/'cases.json').read_bytes()).hexdigest()==manifest['sha256']
    selected=[c for c in cases if c['split']==split]
    service=ApplicationService(normalizer=ConditionalNormalizer())
    target.mkdir(parents=True)
    rows=[]
    for case in selected:
        start=time.perf_counter()
        packet=service.chat({'question_text':case['question_text'],'use_ai':False,'save_history':False})
        result=packet.get('result') or {};route=result.get('routing',{});components=result.get('components',[])
        actual_domains=sorted(set(c['allowed_domain'] for c in components))
        errors=[k for k,actual in [('primary',route.get('predicted_primary')),('scope',route.get('predicted_scope')),('route',route.get('routing_action')),('domains',actual_domains)]
                if actual!=case['expected_'+k]]
        if not packet['response']['paragraphs']:errors.append('empty_response')
        if packet['explanation']['llm_calls'] or packet.get('network_requests'):errors.append('unexpected_provider_call')
        row={'case':case,'packet':packet,'issues':errors,'elapsed_ms':(time.perf_counter()-start)*1000}
        rows.append(row)
        with (target/'observations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    summary={'split':split,'cases':len(rows),'all_expectations_matched':sum(not r['issues'] for r in rows),
             'issue_counts':dict(Counter(e for r in rows for e in r['issues'])),'provider_calls':0,
             'cases_sha256':manifest['sha256'],'runtime':service.health(),
             'software_or_legal_acceptance':False}
    (target/'metrics.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='runtime'}))
    for r in rows:
        if r['issues']:
            result=r['packet'].get('result') or {}
            print(json.dumps({'id':r['case']['case_id'],'q':r['case']['question_text'],'issues':r['issues'],
                              'route':result.get('routing'),'components':[(c['query'],c['allowed_domain']) for c in result.get('components',[])]}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('target',type=Path);p.add_argument('--split',choices=['discovery','confirmation'],required=True)
    a=p.parse_args();run(a.target,a.split)
