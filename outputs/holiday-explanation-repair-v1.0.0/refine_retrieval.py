"""Preserve first repair packages; promote the work-performed relevance repair."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('repair_binding',HERE/'bind_runtime.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def main():
    index=ROOT/'outputs/item11-retrieval-v1.3.3';parent=ROOT/'outputs/item11-retrieval-v1.3.2'
    verifier=ROOT/'outputs/item12-verifier-v1.0.11'
    b.run(['dataset/pipelines/item11/build_index.py','--output-dir',str(index),'--reuse-vectors-from',str(parent),'--default-method','bm25','--selection-evidence','outputs/item11-retrieval-v1.0.2/benchmark_metrics.json'],'retrieval-refined-build.log')
    for name in ['benchmark_manifest.json','benchmark_queries.jsonl','classifier_integration_results.json']:shutil.copyfile(parent/name,index/name)
    b.write(index/'implementation_lineage.json',{'parent':parent.relative_to(ROOT).as_posix(),'source_records_unchanged':True,'explicit_unworked_holiday_relevance_filter':True,'independent_evaluation':False})
    b.write(index/'index_checksums.json',{p.name:b.sha(p) for p in index.iterdir() if p.is_file() and p.name not in {'index_checksums.json','artifact_checksums.json'}})
    b.write(index/'artifact_checksums.json',{p.name:b.sha(p) for p in index.iterdir() if p.is_file() and p.name!='artifact_checksums.json'})
    policy_path=ROOT/'dataset/pipelines/item12/policy.json';old=policy_path.read_bytes();policy=json.loads(old)
    policy.update(version=verifier.name,parent_verifier='outputs/item12-verifier-v1.0.10',retrieval=index.relative_to(ROOT).as_posix())
    b.write(policy_path,policy)
    try:b.run(['dataset/pipelines/item12/rebind_implementation.py','--output',str(verifier)],'verifier-refined-build.log')
    except BaseException:
        policy_path.write_bytes(old)
        raise
    current_path=ROOT/'CURRENT_ARTIFACTS.json';current=json.loads(current_path.read_bytes())
    current.update(retrieval=policy['retrieval'],verifier=verifier.relative_to(ROOT).as_posix(),local_pipeline_evaluation_stack_matches_current=False,application_generated_answer_evaluation_stack_matches_current=False)
    b.write(current_path,current)
    print(json.dumps({'classifier':current['classifier'],'retrieval':current['retrieval'],'verifier':current['verifier']}))

if __name__=='__main__':main()
