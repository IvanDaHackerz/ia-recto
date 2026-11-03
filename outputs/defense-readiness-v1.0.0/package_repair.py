"""Package and bind the repair without changing source records or learned weights."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
CLASSIFIER='outputs/item10-classifier-v1.5.47'
PARENT='outputs/item11-retrieval-v1.3.35'
INDEX='outputs/item11-retrieval-v1.3.36'
VERIFIER='outputs/item12-verifier-v1.0.43'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def run(args,name):
    with (HERE/name).open('w',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('Inspect '+name)

def main():
    parent=ROOT/PARENT;index=ROOT/INDEX
    run(['dataset/pipelines/item11/build_index.py','--output-dir',INDEX,'--reuse-vectors-from',PARENT,
         '--default-method','bm25','--selection-evidence','outputs/item11-retrieval-v1.0.2/benchmark_metrics.json'],'retrieval-selected-build.log')
    for name in ['benchmark_manifest.json','benchmark_queries.jsonl']:shutil.copyfile(parent/name,index/name)
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item11'))
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
    import joblib
    from retrieval import LegalRetriever
    bundle=joblib.load(ROOT/CLASSIFIER/'classifier.joblib');retriever=LegalRetriever(index)
    integration=read(parent/'classifier_integration_results.json')
    for case in integration['cases']:case['result']=retriever.retrieve_question(case['input'],bundle,'bm25',5)
    integration.update(classifier_model_version=bundle['model_version'],classifier_model_path=CLASSIFIER+'/classifier.joblib',classifier_model_sha256=sha(ROOT/CLASSIFIER/'classifier.joblib'))
    write(index/'classifier_integration_results.json',integration)
    write(index/'implementation_lineage.json',{'parent':PARENT,'canonical_records_and_text_unchanged':True,
        'classifier_rebind':CLASSIFIER,'ranking_changed':True,'independent_evaluation':False})
    write(index/'index_checksums.json',{p.name:sha(p) for p in index.iterdir() if p.is_file() and p.name not in {'index_checksums.json','artifact_checksums.json'}})
    write(index/'artifact_checksums.json',{p.name:sha(p) for p in index.iterdir() if p.is_file() and p.name!='artifact_checksums.json'})
    policy_path=ROOT/'dataset/pipelines/item12/policy.json';old=policy_path.read_bytes();policy=json.loads(old)
    policy.update(version=Path(VERIFIER).name,parent_verifier='outputs/item12-verifier-v1.0.42',classifier=CLASSIFIER,retrieval=INDEX)
    write(policy_path,policy)
    try:run(['dataset/pipelines/item12/rebind_implementation.py','--output',VERIFIER],'verifier-selected-build.log')
    except BaseException:policy_path.write_bytes(old);raise
    current=read(ROOT/'CURRENT_ARTIFACTS.json')
    current.update(classifier=CLASSIFIER,retrieval=INDEX,verifier=VERIFIER,
        classifier_scope_retest_repair=HERE.relative_to(ROOT).as_posix(),
        local_pipeline_evaluation_stack_matches_current=False,
        conditional_normalization_development_evaluation_stack_matches_current=False,
        application_generated_answer_evaluation_stack_matches_current=False,
        all_project_issues_closed=False)
    write(ROOT/'CURRENT_ARTIFACTS.json',current)
    config=HERE/(Path(CLASSIFIER).name+'-config.json')
    run(['-m','backend.classifier.build_config','--classifier',CLASSIFIER,'--output',str(config)],'classifier-selected-config.log')
    shutil.copyfile(config,ROOT/'backend/classifier/config.json')
    print(json.dumps({'classifier':CLASSIFIER,'retrieval':INDEX,'verifier':VERIFIER}))

if __name__=='__main__':
    run(['dataset/pipelines/item10/build_preintegration.py','--parent','outputs/item10-classifier-v1.5.46','--output',CLASSIFIER],'classifier-selected-build.log')
    main()
