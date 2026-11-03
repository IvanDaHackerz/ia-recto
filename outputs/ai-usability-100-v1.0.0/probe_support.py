"""Replay known first-pass source-reading failures against the strengthened checker."""
import json
from pathlib import Path
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.application.service import ApplicationService
from backend.application.controls import CancellableTransport,RequestContext,UsageLedger
from backend.application.grounding import support_passed

BASE=Path(__file__).resolve().parent
TARGETS={'AI100_034','AI100_054','AI100_070','AI100_081','AI100_085','AI100_096','AI100_097','AI100_100'}
target=BASE/'support-probe.json'
if target.exists():raise ValueError('Preserve previous probe observations')
budget=BASE/'live-budget.sqlite3'
if not budget.exists():shutil.copyfile(BASE/'first-pass/usage.sqlite3',budget)
ledger=UsageLedger(budget,maximum_calls=500,maximum_usd=.50)
service=ApplicationService.configured()
observations=[json.loads(x) for x in (BASE/'first-pass/observations.jsonl').read_text(encoding='utf-8').splitlines()]
def probe(o):
    cid=o['case']['case_id'];packet=o['normalized']['packet'];claims=packet['explanation']['claims']
    provider=service.development_provider.fork()
    provider.transport=CancellableTransport(RequestContext('source-check-development',cid),ledger,'explanation_support')
    components=[{'component_id':c['component_id'],'sources':c['candidates']} for c in packet['result']['components']]
    report=provider.assess(o['case']['question_text'],claims,components)
    return {'case_id':cid,'all_claims_accepted':support_passed(report,claims),'assessment':report,
            'feedback':provider.last_support_feedback,'role':'AI audit of inspected failures; not independent legal review'}
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(probe,[o for o in observations if o['case']['case_id'] in TARGETS]))
target.write_text(json.dumps({'results':results,'usage_cumulative':ledger.summary()},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in results:print(r['case_id'],'accepted' if r['all_claims_accepted'] else 'rejected',json.dumps(r['feedback']),flush=True)
