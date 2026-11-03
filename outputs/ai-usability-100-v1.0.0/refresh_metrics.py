"""Bind a completed local replay; never reuse earlier scores as current."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    target=ROOT/'outputs/local-pipeline-evaluation-v1.6.15'
    current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text(encoding='utf-8'))
    protocol=json.loads((target/'protocol.json').read_text(encoding='utf-8'))
    for k in ['classifier','retrieval','verifier']:
        if current[k]!=protocol[k]:raise ValueError('Replay is not current')
    checks=json.loads((target/'artifact_checksums.json').read_text(encoding='utf-8'))
    if any(sha(target/name)!=expected for name,expected in checks.items()):raise ValueError('Replay changed')
    current.update(local_pipeline_previous_evaluation=current['local_pipeline_evaluation'],
        local_pipeline_evaluation=target.relative_to(ROOT).as_posix(),local_pipeline_evaluation_stack_matches_current=True,
        classifier_usability_stress='outputs/usability-stress-v1.0.0',all_project_issues_closed=False,
        classifier_performance_evaluation_pending=True,website_independent_acceptance_completed=False,
        local_pipeline_remaining_conservative_route_deferrals=None,
        local_pipeline_route_deferrals_note='See the current evaluation errors.json; historical routing expectations include earlier policy choices.',
        application_response_policy='conversational-guidance-v1.1.0')
    write(ROOT/'backend/application/performance_current.json',{'path':target.relative_to(ROOT).as_posix(),
        'files':{name:sha(target/name) for name in ['metrics.json','observations.jsonl','protocol.json']}})
    write(ROOT/'CURRENT_ARTIFACTS.json',current)
    print('Bound completed local development replay; independent acceptance remains pending.')
if __name__=='__main__':main()
