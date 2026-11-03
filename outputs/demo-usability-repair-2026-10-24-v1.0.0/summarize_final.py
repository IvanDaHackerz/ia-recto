"""Summarize preserved synthetic observations without relabeling any case."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent;RUN=BASE/'final-pass'
sys.path.insert(0,str(ROOT))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
protocol=read(RUN/'protocol.json');metrics=read(RUN/'metrics.json')
assert metrics['pending']==0
assert all(hashlib.sha256((RUN/n).read_bytes()).hexdigest()==h for n,h in read(RUN/'freeze.json').items())
records={r['chunk_id']:r for r in map(json.loads,(ROOT/protocol['retrieval']/'records.jsonl').read_text(encoding='utf-8').splitlines())}
rows=[json.loads(x) for x in (RUN/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
from backend.application.source_issues import issue_for
checks=Counter();cited={};cases=[];text=['# Demo questions and returned AI explanations','Synthetic engineering diagnostics; not independent human gold or verified legal accuracy. All first observations are retained.']
for o in rows:
    c=o['case'];packet=o.get('normalized',{}).get('packet');ass=o.get('normalized',{}).get('assessment',{})
    if packet is None:
        cases.append({'id':c['case_id'],'error':o.get('error')});continue
    e=packet['explanation'];components={x['component_id']:x for x in (packet.get('result') or {}).get('components',[])}
    for comp in components.values():
        for h in comp['candidates']:
            r=records.get(h['chunk_id']);checks['candidates']+=1
            checks['candidate_failures']+=not(r and comp['allowed_domain'] in r['domains'] and all(h[k]==r[k] for k in ['provision_id','document_id','parent_text']))
    for claim in e.get('claims',[]):
        comp=components.get(claim['component_id'])
        for citation in claim['citations']:
            r=records.get(citation['chunk_id']);checks['citations']+=1
            checks['citation_failures']+=not(r and comp and not issue_for(r) and comp['allowed_domain'] in r['domains'] and r['parent_text'][citation['start']:citation['end']]==citation['quote'] and all(citation[k]==r[k] for k in ['provision_id','document_id']))
            if r:cited[r['provision_id']]=r
    for quote in (packet.get('response') or {}).get('quotes',[]):
        r=records.get(quote['chunk_id']);checks['fallback_excerpts']+=1
        checks['fallback_failures']+=not(r and not issue_for(r) and quote['quote'] in r['parent_text'])
    row={'id':c['case_id'],'fresh':not c.get('development_replay',False),'group':c['group'],'question':c['question_text'],'expectation':c['source_case'],'assessment':ass,'AI_status':e['status'],'reason':e['reason'],'claims':e.get('claims',[]),'unanswered':e.get('unanswered_components',[]),'elapsed_ms':o['elapsed_ms']}
    cases.append(row)
    text.extend([f"\n## {row['id']} — {row['group']}",row['question'],f"AI: {e['status']} / {e['reason']}; route: {ass.get('route')}; recorded issues: {ass.get('issues')}."])
    for claim in row['claims']:text.extend([claim['text'],'Citations: '+', '.join(dict.fromkeys(v['provision_id'] for v in claim['citations']))])
    if row['unanswered']:text.append('Unanswered: '+json.dumps(row['unanswered'],ensure_ascii=False))
summary={'stack':{k:protocol[k] for k in ['classifier','retrieval','verifier','model','runtime_signature']},'metrics':metrics,'mechanical_integrity':dict(checks),'legal_accuracy':None,'independent_human_questions':0,'strata':{}}
for name,fresh in [('fresh_24',True),('inspected_replay_22',False)]:
    subset=[x for x in cases if x.get('fresh')==fresh];summary['strata'][name]={'n':len(subset),'AI_status':dict(Counter(x['AI_status'] for x in subset)),**{k:sum(x['assessment'].get(k) is True for x in subset) for k in ['primary_correct','scope_correct','route_correct','domain_correct']}}
save(BASE/'live-summary.json',summary);save(BASE/'per-question-results.json',cases);save(BASE/'cited-records.json',list(cited.values()))
(BASE/'QUESTIONS_AND_RESULTS.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
print(json.dumps({'strata':summary['strata'],'checks':dict(checks),'errors':metrics['errors'],'latency':metrics['latency_ms'],'usage':metrics['usage']},indent=2))
