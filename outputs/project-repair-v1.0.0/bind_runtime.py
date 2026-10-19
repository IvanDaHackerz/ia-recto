"""Prepare repaired immutable runtime packages and explicit operator bindings."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def run(args,name):
    with (HERE/name).open('w',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('Build failed; inspect '+name)

def main():
    clf=ROOT/'outputs/item10-classifier-v1.5.15'
    index=ROOT/'outputs/item11-retrieval-v1.3.1'
    verifier=ROOT/'outputs/item12-verifier-v1.0.9'
    run(['dataset/pipelines/item10/build_preintegration.py','--parent','outputs/item10-classifier-v1.5.13','--output',str(clf)],'classifier-final-build.log')
    run(['dataset/pipelines/item11/build_index.py','--output-dir',str(index),'--reuse-vectors-from','outputs/item11-retrieval-v1.2.9','--default-method','bm25','--selection-evidence','outputs/item11-retrieval-v1.0.2/benchmark_metrics.json'],'retrieval-final-build.log')
    parent=ROOT/'outputs/item11-retrieval-v1.2.9'
    for name in ['benchmark_manifest.json','benchmark_queries.jsonl']:shutil.copyfile(parent/name,index/name)
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item11'));sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
    import joblib
    from retrieval import LegalRetriever
    bundle=joblib.load(clf/'classifier.joblib');retriever=LegalRetriever(index)
    integration=json.loads((parent/'classifier_integration_results.json').read_text(encoding='utf-8'))
    for c in integration['cases']:
        c['result']=retriever.retrieve_question(c['result']['classification']['question_text'],bundle,'bm25',5)
    integration['classifier_model_path']=(clf/'classifier.joblib').relative_to(ROOT).as_posix()
    write(index/'classifier_integration_results.json',integration)
    write(index/'implementation_lineage.json',{'parent':parent.relative_to(ROOT).as_posix(),'source_records_unchanged':True,'query_actor_filter_added':True,'independent_evaluation':False})
    write(index/'index_checksums.json',{p.name:sha(p) for p in index.iterdir() if p.is_file() and p.name not in {'index_checksums.json','artifact_checksums.json'}})
    write(index/'artifact_checksums.json',{p.name:sha(p) for p in index.iterdir() if p.is_file() and p.name!='artifact_checksums.json'})
    policy_path=ROOT/'dataset/pipelines/item12/policy.json'
    policy=json.loads(policy_path.read_text(encoding='utf-8'))
    write(HERE/'previous_policy.json',policy)
    policy.update(version=verifier.name,parent_verifier='outputs/item12-verifier-v1.0.8',classifier=clf.relative_to(ROOT).as_posix(),retrieval=index.relative_to(ROOT).as_posix())
    write(policy_path,policy)
    run(['dataset/pipelines/item12/rebind_implementation.py','--output',str(verifier)],'verifier-final-build.log')
    current_path=ROOT/'CURRENT_ARTIFACTS.json';current=json.loads(current_path.read_text(encoding='utf-8'))
    write(HERE/'previous_current_artifacts.json',current)
    current.update(classifier=policy['classifier'],retrieval=policy['retrieval'],verifier=verifier.relative_to(ROOT).as_posix(),
        local_pipeline_evaluation_stack_matches_current=False,conditional_normalization_development_evaluation_stack_matches_current=False,
        conditional_normalization_current_stack_comparison_completed=False,project_repair='outputs/project-repair-v1.0.0')
    write(current_path,current)
    run(['-m','backend.classifier.build_config','--classifier',policy['classifier'],'--output',str(HERE/'classifier_config.json')],'classifier-config-build.log')
    shutil.copyfile(HERE/'classifier_config.json',ROOT/'backend/classifier/config.json')
    print(json.dumps({'classifier':policy['classifier'],'retrieval':policy['retrieval'],'verifier':current['verifier']}))

if __name__=='__main__':main()
