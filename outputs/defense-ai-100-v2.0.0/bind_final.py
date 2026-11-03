"""Bind completed current-stack evidence, preserving every earlier run."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
target=ROOT/'outputs/local-pipeline-evaluation-v1.6.24'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
current=read(ROOT/'CURRENT_ARTIFACTS.json');protocol=read(target/'protocol.json')
assert all(current[k]==protocol[k] for k in ['classifier','retrieval','verifier'])
assert all(sha(target/name)==expected for name,expected in read(target/'artifact_checksums.json').items())
historical_recheck=read(BASE/'final-targeted/metrics.json')
assert historical_recheck['input_forms']==49 and historical_recheck['pending']==0
recheck=read(BASE/'feedback-targeted/metrics.json')
assert recheck['input_forms']==9 and recheck['pending']==0 and not recheck['errors']
assert all(current[k]==read(BASE/'feedback-targeted/protocol.json')[k] for k in ['classifier','retrieval','verifier'])
micro=read(BASE/'overtime-final/metrics.json')
assert micro['input_forms']==1 and micro['pending']==0 and not micro['errors']
for p in (BASE/'overtime-final/source_snapshot').rglob('*'):
    if p.is_file():assert p.read_bytes()==(ROOT/p.relative_to(BASE/'overtime-final/source_snapshot')).read_bytes()
current.update(local_pipeline_previous_evaluation=current['local_pipeline_evaluation'],
    local_pipeline_evaluation=target.relative_to(ROOT).as_posix(),local_pipeline_evaluation_stack_matches_current=True,
    defense_ai_100_development_study=BASE.relative_to(ROOT).as_posix(),
    defense_ai_100_initial_run=(BASE/'initial').relative_to(ROOT).as_posix(),
    defense_ai_100_repaired_full_run=(BASE/'repaired').relative_to(ROOT).as_posix(),
    defense_ai_100_final_targeted_run=(BASE/'final-targeted').relative_to(ROOT).as_posix(),
    defense_ai_100_targeted_recheck_stack_matches_current=False,
    defense_ai_100_final_followup=(BASE/'feedback-targeted').relative_to(ROOT).as_posix(),
    defense_ai_100_followup_stack_matches_current=True,
    defense_ai_100_last_condition_check=(BASE/'overtime-final').relative_to(ROOT).as_posix(),
    defense_ai_100_independent_human_gold=False,all_project_issues_closed=False)
save(ROOT/'backend/application/performance_current.json',{'path':target.relative_to(ROOT).as_posix(),
    'files':{name:sha(target/name) for name in ['metrics.json','observations.jsonl','protocol.json']}})
save(ROOT/'CURRENT_ARTIFACTS.json',current)
print('Bound the completed current-stack local evaluation and disclosed 49-case AI repair recheck and nine-case final follow-up.')
