"""Freeze selected classifier before opening reserved synthetic predictions."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text());folder=ROOT/current['classifier']
checks=json.loads((folder/'artifact_checksums.json').read_text());bindings={}
for name in ['classifier_runtime.py','clause_classifier.py','logical_clause_model.py','scope_constraints.py','typing_repair.py','typing_vocabulary.py','semantic_encoder.py','referral_routing.py']:
 path=ROOT/'dataset/pipelines/item10'/name
 assert sha(path)==checks[name]
 bindings[path.relative_to(ROOT).as_posix()]=sha(path)
path=HERE/(sys.argv[1] if len(sys.argv)>1 else 'implementation_frozen.json');assert not path.exists()
path.write_text(json.dumps({'classifier':current['classifier'],'model_sha256':sha(folder/'classifier.joblib'),
 'classifier_artifact_checksums_sha256':sha(folder/'artifact_checksums.json'),'runtime_files_sha256':bindings,
 'new_diagnostic_questions_fitted':0,'reserved_predictions_previously_opened':False,
 'final_policy':'Reserved results are reported as observed; do not tune on these results. They are synthetic and share authorship, not independent human gold.'},indent=2)+'\n')
print(current['classifier'])
