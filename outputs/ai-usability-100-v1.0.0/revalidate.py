"""Recheck captured live drafts under current local gates; never invent a judge approval."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.terminal_test import load_runtime
from backend.application.development_explanation import checked_claims
from backend.application.source_issues import issue_for
from dataset.pipelines.item11.query_relevance import source_relevance

BASE=Path(__file__).resolve().parent
verifier=load_runtime()
cases=json.loads((BASE/'cases.json').read_text(encoding='utf-8'))
observations=[json.loads(l) for l in (BASE/'final-replay/observations.jsonl').read_text(encoding='utf-8').splitlines()]
by_id={o['case']['case_id']:o for o in observations}
gaps={f'AI100_{n:03d}' for n in [*range(6,11),*range(26,31),*range(41,46),94]}
results=[];targets=[]
for case in cases:
    cid=case['case_id'];o=by_id.get(cid)
    row={'case_id':cid,'source_gap_audit':cid in gaps,'independent_legal_review':False}
    if not o:
        row.update(status='not_executed_in_latest_bulk_run',reason='bulk_estimated_cost_stop')
        targets.append(cid)
    else:
        packet=o['normalized']['packet'];explanation=packet['explanation']
        row.update(status=explanation['status'],original_reason=explanation['reason'])
        if explanation['status']=='generated':
            components=[]
            for c in packet['result']['components']:
                gates={g['chunk_id']:g for g in c['evidence_gates']}
                eligible=[h for h in c['candidates'] if h['chunk_id'] in gates
                    and not(set(gates[h['chunk_id']]['reasons'])-{'scoped_currentness_review_missing'})
                    and not verifier.check_candidate(h,c['allowed_domain']) and not issue_for(h)
                    and source_relevance(c['query'],c['allowed_domain'],h)>0]
                components.append({'component_id':c['component_id'],'query':c['query'],'sources':eligible[:3]})
            draft={'paragraphs':[{'component_id':c['component_id'],'text':c['text'],
                'evidence':[{'chunk_id':v['chunk_id'],'quote':v['quote']} for v in c['citations']]} for c in explanation['claims']]}
            try:
                checked_claims(draft,components);row['current_local_checks_pass']=True
            except (ValueError,TypeError,KeyError) as error:
                row.update(current_local_checks_pass=False,local_failure=str(error));targets.append(cid)
        elif cid not in gaps:
            targets.append(cid)
    results.append(row)
report={'role':'Current local revalidation of captured live outputs, not a fresh provider or independent legal evaluation',
    'observed_packets':len(observations),'original_generated':sum(r.get('status')=='generated' for r in results),
    'captured_generated_passing_current_local_checks':sum(r.get('current_local_checks_pass') is True for r in results),
    'generated_flagged_by_new_guards':sum(r.get('current_local_checks_pass') is False for r in results),
    'source_gap_audit_is_posthoc':True,'source_gap_case_ids':sorted(gaps),
    'targeted_recheck_ids':targets,'cases':results,'new_provider_calls':0}
(BASE/'current-policy-revalidation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
