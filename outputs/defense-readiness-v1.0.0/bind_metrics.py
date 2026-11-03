"""Bind only a completed replay that actually matches the selected stack."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
target=ROOT/'outputs/local-pipeline-evaluation-v1.6.21'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
current=read(ROOT/'CURRENT_ARTIFACTS.json');protocol=read(target/'protocol.json')
assert all(current[k]==protocol[k] for k in ['classifier','retrieval','verifier'])
assert all(sha(target/name)==expected for name,expected in read(target/'artifact_checksums.json').items())
current.update(local_pipeline_previous_evaluation=current['local_pipeline_evaluation'],
    local_pipeline_evaluation=target.relative_to(ROOT).as_posix(),local_pipeline_evaluation_stack_matches_current=True,
    defense_readiness_repair='outputs/defense-readiness-v1.0.0',defense_readiness_ai_check='outputs/defense-readiness-v1.0.0/live-browser-checked',defense_readiness_initial_ai_check='outputs/defense-readiness-v1.0.0/live-after',defense_readiness_warranty_recheck='outputs/defense-readiness-v1.0.0/warranty-final',
    application_response_policy='conversational-guidance-v1.2.0',all_project_issues_closed=False)
save(ROOT/'backend/application/performance_current.json',{'path':target.relative_to(ROOT).as_posix(),
    'files':{name:sha(target/name) for name in ['metrics.json','observations.jsonl','protocol.json']}})
save(ROOT/'CURRENT_ARTIFACTS.json',current)
print('Bound the completed current-stack AI-off development evaluation.')
