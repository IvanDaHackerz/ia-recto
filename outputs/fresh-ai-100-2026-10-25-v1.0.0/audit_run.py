"""Audit exact evidence and preserve readable per-question results."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
RUN=BASE/(sys.argv[1] if len(sys.argv)>1 else 'first-pass')
sys.path.insert(0,str(ROOT))
from backend.application.source_issues import issue_for

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

protocol=read(RUN/'protocol.json')
records={r['chunk_id']:r for r in map(json.loads,(ROOT/protocol['retrieval']/'records.jsonl').read_text(encoding='utf-8').splitlines())}
rows=[json.loads(s) for s in (RUN/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
checks=Counter();cited={};results=[]
transcript=['# Questions and returned explanations',
    'Fictional AI-authored engineering inputs. Not independent human gold or verified legal accuracy. Frozen expectations and all observations are preserved.']
for row in rows:
    case=row['case'];packet=row.get('normalized',{}).get('packet');assessment=row.get('normalized',{}).get('assessment',{})
    if packet is None:
        results.append({'case_id':case['case_id'],'error':row.get('error')});continue
    components={c['component_id']:c for c in (packet.get('result') or {}).get('components',[])}
    explanation=packet['explanation'];norm=packet.get('normalization') or {}
    for component in components.values():
        for hit in component['candidates']:
            record=records.get(hit['chunk_id']);checks['candidate_checks']+=1
            checks['candidate_failures']+=not(record and component['allowed_domain'] in record['domains'] and all(hit[k]==record[k] for k in ['provision_id','document_id','parent_text']))
    for claim in explanation.get('claims',[]):
        component=components.get(claim['component_id'])
        checks['claim_checks']+=1
        checks['claim_gate_failures']+=not(explanation.get('automated_support_checked') and explanation.get('citations_checked') and component)
        for citation in claim['citations']:
            record=records.get(citation['chunk_id']);checks['citation_checks']+=1
            checks['citation_failures']+=not(record and component and not issue_for(record) and component['allowed_domain'] in record['domains'] and record['parent_text'][citation['start']:citation['end']]==citation['quote'] and all(citation[k]==record[k] for k in ['provision_id','document_id']))
            if record:cited[record['provision_id']]=record
    for quote in (packet.get('response') or {}).get('quotes',[]):
        record=records.get(quote['chunk_id']);checks['fallback_checks']+=1
        checks['fallback_failures']+=not(record and not issue_for(record) and quote['quote'] in record['parent_text'])
    result={'case_id':case['case_id'],'question':case['question_text'],'group':case['group'],'topic':case['topic'],
        'expected':case['source_case'],'assessment':assessment,'normalization':norm,'explanation':explanation,
        'components':[{'id':c['component_id'],'query':c['query'],'sources':[h['provision_id'] for h in c['candidates']]} for c in components.values()],
        'elapsed_ms':row['elapsed_ms']}
    results.append(result)
    transcript.extend([f"\n## {case['case_id']} ({case['group']}: {case['topic']})",case['question_text'],
        f"Expected: {case['source_case']['expected_primary']} / {case['source_case']['expected_scope']} / {case['source_case']['expected_route']}.",
        f"Observed: {assessment.get('predicted_primary')} / {assessment.get('predicted_scope')} / {assessment.get('route')}. Issues: {assessment.get('issues')}.",
        f"Wording: {norm.get('status')} / {norm.get('reason')}; AI: {explanation['status']} / {explanation['reason']}."])
    if norm.get('status')=='applied':transcript.append('Interpreted wording: '+str(norm.get('effective_question_text')))
    for claim in explanation.get('claims',[]):
        transcript.extend([claim['text'],'Citations: '+', '.join(dict.fromkeys(c['provision_id'] for c in claim['citations']))])
    if explanation.get('unanswered_components'):transcript.append('Unanswered: '+json.dumps(explanation['unanswered_components'],ensure_ascii=False))
summary={'inputs':len(rows),'integrity':dict(checks),'routing_issue_ids':[r['case_id'] for r in results if r.get('assessment',{}).get('issues')],
    'normalization_status':dict(Counter(r.get('normalization',{}).get('status') for r in results)),
    'normalization_failures':dict(Counter(r.get('normalization',{}).get('validation_failure') for r in results if r.get('normalization',{}).get('validation_failure'))),
    'role':'AI-authored synthetic development diagnostic','independent_human_questions':0,'legal_accuracy':None,
    'frozen_files_intact':all(hashlib.sha256((RUN/n).read_bytes()).hexdigest()==h for n,h in read(RUN/'freeze.json').items()),
    'groups':{g:{'n':len(subset),'topic_correct':sum(r.get('assessment',{}).get('primary_correct') is True for r in subset),
        'scope_correct':sum(r.get('assessment',{}).get('scope_correct') is True for r in subset),
        'route_correct':sum(r.get('assessment',{}).get('route_correct') is True for r in subset),
        'AI_status':dict(Counter(r.get('explanation',{}).get('status') for r in subset))}
        for g in sorted({r.get('group') for r in results if r.get('group')})
        for subset in [[r for r in results if r.get('group')==g]]}}
save(RUN/'audit.json',summary);save(RUN/'readable-results.json',results);save(RUN/'cited-records.json',list(cited.values()))
(RUN/'QUESTIONS_AND_RESULTS.md').write_text('\n\n'.join(transcript)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
