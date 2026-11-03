"""Test new source guards on saved accepted claims, without provider calls."""
import json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];sys.path.insert(0,str(ROOT))
from backend.application.grounding import source_qualification_failure
from backend.application.source_issues import issue_for
run=sys.argv[1] if len(sys.argv)>1 else 'repaired'
rows=[json.loads(x) for x in (BASE/run/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
checks=[]
for row in rows:
 p=row['normalized']['packet'];sources={h['chunk_id']:h for c in (p.get('result') or {}).get('components',[]) for h in c['candidates']}
 for c in p['explanation']['claims']:
  source=' '.join(sources[x['chunk_id']]['parent_text']+' '+sources[x['chunk_id']]['citation_display']+' '+' '.join(sources[x['chunk_id']]['conditions']) for x in c['citations'])
  checks.append({'id':row['case']['case_id'],'claim_id':c['claim_id'],'text':c['text'],'new_guard_failure':'source_held_for_interpretation_review' if any(issue_for(sources[x['chunk_id']]) for x in c['citations']) else source_qualification_failure(c['text'],source)})
result={'role':'Offline guard regression on saved intermediate AI outputs; not a new complete application replay or independent legal review','claims_tested':len(checks),'newly_blocked_claims':[x for x in checks if x['new_guard_failure']],'all_checks':checks,'provider_calls':0}
(BASE/('saved-claim-guard-revalidation.json' if run=='repaired' else run+'-guard-revalidation.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'claims':len(checks),'blocked':len(result['newly_blocked_claims']),'reasons':[(x['id'],x['new_guard_failure']) for x in result['newly_blocked_claims']]},indent=2))
