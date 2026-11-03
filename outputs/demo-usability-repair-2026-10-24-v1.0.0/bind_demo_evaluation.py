import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
TARGET=ROOT/'outputs/local-pipeline-evaluation-v1.6.27'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(ROOT/'CURRENT_ARTIFACTS.json');protocol=read(TARGET/'protocol.json')
assert all(c[k]==protocol[k] for k in ['classifier','retrieval','verifier'])
assert all(sha(TARGET/n)==h for n,h in read(TARGET/'artifact_checksums.json').items())
assert read(TARGET/'metrics.json')['counts']['input_forms']==436
for k in c:
    if k.endswith('stack_matches_current'):c[k]=False
c.update(local_pipeline_previous_evaluation=c['local_pipeline_evaluation'],local_pipeline_evaluation=TARGET.relative_to(ROOT).as_posix(),
    local_pipeline_evaluation_stack_matches_current=True,local_pipeline_development_evaluation_completed=True,
    classifier_scope_retest_repair='outputs/defense-ai-100-v2.0.0',
    demo_usability_repair=HERE.relative_to(ROOT).as_posix(),demo_usability_repair_stack_matches_current=True,
    demo_usability_live_evaluation=(HERE/'final-pass').relative_to(ROOT).as_posix(),all_project_issues_closed=False)
save(ROOT/'backend/application/performance_current.json',{'path':TARGET.relative_to(ROOT).as_posix(),'files':{n:sha(TARGET/n) for n in ['metrics.json','observations.jsonl','protocol.json']}})
save(ROOT/'CURRENT_ARTIFACTS.json',c)
print('Bound current-stack local evaluation; historical AI studies explicitly remain stale.')
