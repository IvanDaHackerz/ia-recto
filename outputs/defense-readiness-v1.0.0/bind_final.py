"""Bind the tested classifier repair with unchanged retrieval/source records."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(args,name):
    with (BASE/name).open('w',encoding='utf-8') as f:r=subprocess.run([sys.executable,*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Inspect '+name)

classifier='outputs/item10-classifier-v1.5.46';verifier='outputs/item12-verifier-v1.0.42'
run(['dataset/pipelines/item10/build_preintegration.py','--parent','outputs/item10-classifier-v1.5.45','--output',classifier],'classifier-final-build.log')
policy_path=ROOT/'dataset/pipelines/item12/policy.json';old=policy_path.read_bytes();policy=read(policy_path)
policy.update(version=Path(verifier).name,parent_verifier='outputs/item12-verifier-v1.0.41',classifier=classifier,retrieval='outputs/item11-retrieval-v1.3.34')
write(policy_path,policy)
try:run(['dataset/pipelines/item12/rebind_implementation.py','--output',verifier],'verifier-final-build.log')
except BaseException:policy_path.write_bytes(old);raise
current=read(ROOT/'CURRENT_ARTIFACTS.json')
current.update(classifier=classifier,retrieval=policy['retrieval'],verifier=verifier,
               defense_readiness_repair='outputs/defense-readiness-v1.0.0',application_response_policy='conversational-guidance-v1.2.0',
               local_pipeline_evaluation_stack_matches_current=False,all_project_issues_closed=False)
config=BASE/'classifier-final-config.json'
run(['-m','backend.classifier.build_config','--classifier',classifier,'--output',str(config)],'classifier-final-config.log')
shutil.copyfile(config,ROOT/'backend/classifier/config.json')
write(ROOT/'CURRENT_ARTIFACTS.json',current)
print(json.dumps({k:current[k] for k in ['classifier','retrieval','verifier']}))
