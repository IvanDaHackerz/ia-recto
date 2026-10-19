"""Build a versioned, read-only-source legal retrieval index; never overwrite a build."""
from __future__ import annotations
import argparse,collections,json,platform,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from common import ROOT,PIPELINE,sources,curate,save,jsonl,sha
from encoder import windows,encode,MODEL_NAME,MAX_TOKENS,reuse_index_vectors

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--reuse-vectors-from',type=Path)
    p.add_argument('--default-method',choices=['bm25','semantic','hybrid'],default='hybrid');p.add_argument('--selection-evidence',type=Path)
    a=p.parse_args();out=a.output_dir.resolve()
    if out.exists():raise ValueError('Use a new output directory; index builds are immutable')
    started=time.time();source=sources();records,excluded=curate(source)
    reused=reuse_index_vectors(a.reuse_vectors_from) if a.reuse_vectors_from else 0
    if not records:raise ValueError('No eligible retrieval records')
    out.mkdir(parents=True);jsonl(out/'records.jsonl',records);jsonl(out/'excluded_chunks.jsonl',excluded)
    planned=[]
    for i,r in enumerate(records):
        for w in windows(r['display_text'],r['heading'] or r['citation_display']):planned.append({'record_index':i,'chunk_id':r['chunk_id'],**w})
    print('Encoding '+str(len(planned))+' windows from '+str(len(records))+' eligible chunks locally',flush=True)
    vectors=encode([w['text'] for w in planned]);np.savez_compressed(out/'semantic_vectors.npz',vectors=vectors,record_indices=np.array([w['record_index'] for w in planned],dtype=np.int32))
    jsonl(out/'semantic_windows.jsonl',planned)
    topic_counts=collections.Counter(t for r in records for t in r['supported_topics'])
    coverage=[{**t,'indexed_chunks':topic_counts[t['topic_id']],'evidence_status':'no_eligible_chunks' if not topic_counts[t['topic_id']] else 'candidates_with_source_conditions','answer_generation_allowed':False} for t in source['taxonomy'] if t['scope_status']=='supported']
    save(out/'topic_coverage.json',coverage)
    save(out/'source_audit.json',{'source_sha256':source['source_sha256'],'raw_source_sha256':source['raw_source_sha256'],'original_documents':len(source['documents']),'original_provisions':len(source['provisions']),'original_chunks':len(source['chunks']),
        'item7_eligible_chunks':sum(c['answer_eligible'] for c in source['chunks']),'indexed_chunks':len(records),'indexed_provisions':len({r['provision_id'] for r in records}),'indexed_documents':len({r['document_id'] for r in records}),
        'extra_scope_quarantine_chunks':sum(x['item7_answer_eligible'] for x in excluded),'exclusion_reason_counts':dict(collections.Counter(reason for x in excluded for reason in x['reasons'])),'scope_screen_origin':'AI-authored conservative heading/hierarchy screen; not an independent human/legal review',
        'source_data_modified':False,'legal_status_refreshed':False,'legal_status_as_of':sorted({r['status_as_of'] for r in records}),'all_candidates_conditional':all(r['status_family']=='current_with_conditions' for r in records)})
    # Method settings are fixed before authoring/scoring the retrieval benchmark.
    config={'bm25_k1':1.2,'bm25_b':.75,'rrf_k':60,'rrf_candidate_depth':50,'default_method':a.default_method,'methods':['bm25','semantic','hybrid'],
        'semantic_pooling':'max over token-bounded document/query windows','semantic_max_tokens':MAX_TOKENS,'semantic_overlap_tokens':20,'returned_unit':'unique provision, retaining best chunk and full eligible parent text',
        'score_is_confidence':False,'minimum_score_claim':'No answer-sufficiency threshold is claimed; Item 12 evidence verification remains required'}
    save(out/'retrieval_config.json',config)
    manifest={'index_version':out.name,'status':'offline_index_built','as_of':'2026-10-17','indexed_chunks':len(records),'indexed_provisions':len({r['provision_id'] for r in records}),
        'semantic_windows':len(planned),'semantic_model':MODEL_NAME,'semantic_model_manifest_sha256':sha(ROOT/'models/embedding_backbone_manifest.json'),
        'source_sha256':source['source_sha256'],'source_data_modified':False,'no_question_dataset_fitted':True,'encoder_finetuned':False,'project_text_transmitted':False,
        'deployment_allowed':False,'answer_generation_allowed':False,'legal_status_refreshed':False,'elapsed_seconds':time.time()-started,'python':platform.python_version()}
    manifest['vector_reuse']={'parent_index':str(a.reuse_vectors_from) if a.reuse_vectors_from else None,'cached_exact_text_vectors':reused,'model_weights_unchanged':True}
    manifest['runtime_source_sha256']={name:sha(PIPELINE/name) for name in ['common.py','encoder.py','retrieval.py']}
    if a.selection_evidence:
        evidence=json.loads(a.selection_evidence.read_text());best=max(evidence['methods'],key=lambda name:(evidence['methods'][name]['hit@5'],evidence['methods'][name]['mrr@10']))
        if a.default_method!=best:raise ValueError('Default method does not match the recorded development selection rule')
        manifest['method_selection']={'source':str(a.selection_evidence),'sha256':sha(a.selection_evidence),'role':'AI development selection, not independent test','rule':'Highest Hit@5, then MRR@10','selected':best}
    save(out/'index_manifest.json',manifest)
    for file in PIPELINE.glob('*.py'):shutil.copy2(file,out/file.name)
    (out/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    save(out/'index_checksums.json',{f.name:sha(f) for f in out.iterdir() if f.is_file() and f.name!='index_checksums.json'})
    print(json.dumps(manifest,indent=2),flush=True)
if __name__=='__main__':main()
