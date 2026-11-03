"""Actual application, AI off; frozen scope expectations and full packet retention."""
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.normalization_metrics import assess,summarize_path
BASE=Path(__file__).resolve().parent
target=Path(sys.argv[1])
if target.exists():raise SystemExit('Use a new result directory')
manifest=json.loads((BASE/'live-case-manifest.json').read_text())
assert hashlib.sha256((BASE/'live-cases.json').read_bytes()).hexdigest()==manifest['cases_sha256']
cases=json.loads((BASE/'live-cases.json').read_text(encoding='utf-8'))
service=ApplicationService(normalizer=ConditionalNormalizer())
target.mkdir(parents=True)
rows=[]
for c in cases:
    start=time.monotonic()
    p=service.chat({'question_text':c['question_text'],'use_ai':False,'save_history':False})
    assert p['explanation']['llm_calls']==0
    row={'case':c,'normalized':{'packet':p,'assessment':assess(c,p)},'elapsed_ms':1000*(time.monotonic()-start)}
    rows.append(row)
    with (target/'observations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
metrics={'cases':len(rows),'provider_calls':0,'runtime':service.health(),'scope_metrics':summarize_path(rows,'normalized'),
         'all_expectations_matched':sum(not r['normalized']['assessment']['issues'] for r in rows),
         'failures':[{ 'id':r['case']['case_id'],'issues':r['normalized']['assessment']['issues']} for r in rows if r['normalized']['assessment']['issues']]}
(target/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in metrics.items() if k not in {'runtime','scope_metrics'}}))
