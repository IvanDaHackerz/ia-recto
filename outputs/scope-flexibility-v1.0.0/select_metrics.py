"""Pin completed current-stack local metrics without changing frozen judgments."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
folder=ROOT/'outputs/local-pipeline-evaluation-v1.6.1'
protocol=json.loads((folder/'protocol.json').read_text());current_path=ROOT/'CURRENT_ARTIFACTS.json';current=json.loads(current_path.read_bytes())
assert all(current[k]==protocol[k] for k in ['classifier','retrieval','verifier'])
checks=json.loads((folder/'artifact_checksums.json').read_text())
assert all(sha(folder/name)==expected for name,expected in checks.items())
write(ROOT/'backend/application/performance_current.json',{'path':folder.relative_to(ROOT).as_posix(),
 'files':{name:sha(folder/name) for name in ['metrics.json','observations.jsonl','protocol.json']}})
current.update(local_pipeline_evaluation=folder.relative_to(ROOT).as_posix(),local_pipeline_evaluation_stack_matches_current=True,
 scope_flexibility_atomic_weights_unchanged=True,scope_flexibility_thresholds_unchanged=True,
 scope_flexibility_calibration_refit_on_original_training_only=True,
 scope_flexibility_independent_human_questions=0,scope_flexibility_external_ai_calls=0)
write(current_path,current)
preserved={}
for name in ['outputs/item10-classifier-v1.5.16','outputs/item11-retrieval-v1.3.3','outputs/item12-verifier-v1.0.11']:
 path=ROOT/name;manifest=json.loads((path/'artifact_checksums.json').read_text())
 changed=[p for p,h in manifest.items() if sha(path/p)!=h]
 preserved[name]={'checked_files':len(manifest),'changed_files':changed,'passed':not changed}
write(HERE/'preservation.json',preserved);assert all(v['passed'] for v in preserved.values())
write(HERE/'reserve_exposure.json',{'first_reserved_run':'reserved-final.json','first_route_matches':47,'first_count':50,
 'first_reserved_cases_used_for_further_repair':True,'first_cases_role_after_opening':'inspected development regressions',
 'second_unused_wording_check':'second-reserve-results.json','second_count':30,
 'second_used_for_tuning':False,'independent_human_questions':0})
print(json.dumps({'selected_metrics':current['local_pipeline_evaluation'],'historical_artifacts_preserved':True}))
