"""Build immutable dependencies for the website field repairs; no API calls."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def run(args,log):
    with (HERE/log).open('w',encoding='utf-8') as f:
        r=subprocess.run([sys.executable,*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Inspect '+log)
def main():
    classifier=ROOT/'outputs/item10-classifier-v1.5.35'
    parent=ROOT/'outputs/item11-retrieval-v1.3.19'
    index=ROOT/'outputs/item11-retrieval-v1.3.20'
    verifier=ROOT/'outputs/item12-verifier-v1.0.27'
    run(['dataset/pipelines/item11/build_index.py','--output-dir',str(index),'--reuse-vectors-from',str(parent),
         '--default-method','bm25','--selection-evidence','outputs/item11-retrieval-v1.0.2/benchmark_metrics.json'],'retrieval-build-v20.log')
    for name in ['benchmark_manifest.json','benchmark_queries.jsonl']:shutil.copyfile(parent/name,index/name)
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item11'));sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
    import joblib
    from retrieval import LegalRetriever
    bundle=joblib.load(classifier/'classifier.joblib');retriever=LegalRetriever(index)
    integration=json.loads((parent/'classifier_integration_results.json').read_text())
    for case in integration['cases']:
        case['result']=retriever.retrieve_question(case['input'],bundle,'bm25',5)
    integration.update(classifier_model_version=bundle['model_version'],classifier_model_path=(classifier/'classifier.joblib').relative_to(ROOT).as_posix(),classifier_model_sha256=sha(classifier/'classifier.joblib'))
    write(index/'classifier_integration_results.json',integration)
    write(index/'implementation_lineage.json',{'parent':parent.relative_to(ROOT).as_posix(),'canonical_records_and_text_unchanged':True,'derived_rule_coverage_conditions_added':True,'classifier_rebind':classifier.relative_to(ROOT).as_posix(),'independent_evaluation':False,'ranking_changed':True})
    write(index/'index_checksums.json',{p.name:sha(p) for p in index.iterdir() if p.is_file() and p.name not in {'index_checksums.json','artifact_checksums.json'}})
    write(index/'artifact_checksums.json',{p.name:sha(p) for p in index.iterdir() if p.is_file() and p.name!='artifact_checksums.json'})
    policy_path=ROOT/'dataset/pipelines/item12/policy.json';old=policy_path.read_bytes();policy=json.loads(old)
    write(HERE/'previous_policy_v27.json',policy)
    policy.update(version=verifier.name,parent_verifier='outputs/item12-verifier-v1.0.26',classifier=classifier.relative_to(ROOT).as_posix(),retrieval=index.relative_to(ROOT).as_posix())
    write(policy_path,policy)
    try:run(['dataset/pipelines/item12/rebind_implementation.py','--output',str(verifier)],'verifier-build-v27.log')
    except BaseException:policy_path.write_bytes(old);raise
    current_path=ROOT/'CURRENT_ARTIFACTS.json';current=json.loads(current_path.read_bytes());write(HERE/'previous_current_v27.json',current)
    current.update(classifier=policy['classifier'],retrieval=policy['retrieval'],verifier=verifier.relative_to(ROOT).as_posix(),
        classifier_usability_stress=HERE.relative_to(ROOT).as_posix(),application_response_policy='conversational-guidance-v1.1.0',
        local_pipeline_evaluation_stack_matches_current=False,conditional_normalization_development_evaluation_stack_matches_current=False,
        application_generated_answer_evaluation_stack_matches_current=False,all_project_issues_closed=False)
    write(current_path,current)
    config=HERE/(classifier.name+'_'+verifier.name+'_config.json')
    run(['-m','backend.classifier.build_config','--classifier',policy['classifier'],'--output',str(config)],'classifier-config-v27.log')
    shutil.copyfile(config,ROOT/'backend/classifier/config.json')
    print(json.dumps({k:current[k] for k in ['classifier','retrieval','verifier']}))
if __name__=='__main__':main()
