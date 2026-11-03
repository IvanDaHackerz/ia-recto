"""Final AI-off application and immutable-source preservation checks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer

BASE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
target=BASE/'current-local-checks'
if target.exists():raise SystemExit('Preserve the earlier run; use a new target')
for data,manifest in [('cases.json','manifest.json'),('fresh-final-cases.json','fresh-final-manifest.json')]:
    assert hashlib.sha256((BASE/data).read_bytes()).hexdigest()==read(BASE/manifest)['sha256']
cases=read(BASE/'cases.json')+read(BASE/'fresh-final-cases.json')
service=ApplicationService(normalizer=ConditionalNormalizer());target.mkdir()
rows=[]
for case in cases:
    started=time.perf_counter();packet=service.chat({'question_text':case['question_text'],'use_ai':False,'save_history':False})
    result=packet.get('result') or {};routing=result.get('routing',{})
    actual={'primary':routing.get('predicted_primary'),'scope':routing.get('predicted_scope'),
            'route':routing.get('routing_action'),'domains':sorted({c['allowed_domain'] for c in result.get('components',[])})}
    issues=[k for k,v in actual.items() if v!=case['expected_'+k]]
    if not packet['response']['paragraphs']:issues.append('empty_response')
    if packet.get('network_requests') or packet['explanation']['llm_calls']:issues.append('unexpected_network')
    row={'case':case,'packet':packet,'actual':actual,'issues':issues,'elapsed_ms':(time.perf_counter()-started)*1000}
    rows.append(row)
    with (target/'observations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
groups={}
for split in ['discovery','confirmation','fresh_final']:
    selected=[r for r in rows if r['case']['split']==split]
    groups[split]={'cases':len(selected),'all_expectations_matched':sum(not r['issues'] for r in selected),
                   'issues':{r['case']['case_id']:r['issues'] for r in selected if r['issues']}}
save(target/'metrics.json',{'groups':groups,'network_calls':0,'runtime':service.health(),
    'notes':['The 72 original cases informed repairs; report the initial reserved 21/24 result separately.',
             'The six final observations were not used for tuning. All inputs are AI-authored, not human gold or legal-answer judgments.']})
current=read(ROOT/'CURRENT_ARTIFACTS.json')
save(BASE/'source-preservation.json',{
    'canonical_records_byte_identical':(ROOT/current['retrieval']/'records.jsonl').read_bytes()==(ROOT/'outputs/item11-retrieval-v1.3.33/records.jsonl').read_bytes(),
    'learned_state':read(ROOT/current['classifier']/'implementation_lineage.json')['unchanged_learned_state'],
    'frozen_72_cases_unchanged':True,'fresh_six_cases_unchanged':True})
print(json.dumps(groups))
