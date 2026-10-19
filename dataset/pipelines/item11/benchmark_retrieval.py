"""Compare fixed retrievers against disclosed AI-authored provision relevance labels."""
from __future__ import annotations
import argparse,collections,json,time
from pathlib import Path
import numpy as np
from common import ROOT,readrows,save,jsonl,sha
from retrieval import LegalRetriever

def per_query(row,hits):
    truth=set(row['relevant_provision_ids']);ids=[r['provision_id'] for r in hits];out={}
    for k in [1,3,5,10]:
        relevant=[int(i in truth) for i in ids[:k]];out['hit@'+str(k)]=int(any(relevant));out['recall@'+str(k)]=len(set(ids[:k])&truth)/len(truth)
    first=next((i for i,pid in enumerate(ids,1) if pid in truth),None);out['mrr@10']=1/first if first else 0.
    dcg=sum(int(pid in truth)/np.log2(i+2) for i,pid in enumerate(ids));ideal=sum(1/np.log2(i+2) for i in range(min(10,len(truth))));out['ndcg@10']=float(dcg/ideal)
    return out

def summarize(rows):
    keys=list(rows[0]['metrics']);result={k:float(np.mean([r['metrics'][k] for r in rows])) for k in keys}
    result['queries']=len(rows);result['scenario_families']=len({r['scenario_family_id'] for r in rows});result['language']={}
    for lang in sorted({r['language_style'] for r in rows}):
        subset=[r for r in rows if r['language_style']==lang];result['language'][lang]={k:float(np.mean([r['metrics'][k] for r in subset])) for k in keys}
    groups=collections.defaultdict(list)
    for r in rows:groups[r['scenario_family_id']].append(r)
    values=np.array([[np.mean([r['metrics'][k] for r in group]) for k in keys] for group in groups.values()]);rng=np.random.default_rng(20261017)
    boot=np.array([values[rng.integers(0,len(values),len(values))].mean(axis=0) for _ in range(2000)])
    result['scenario_bootstrap_95']={k:{'lower':float(np.quantile(boot[:,i],.025)),'upper':float(np.quantile(boot[:,i],.975))} for i,k in enumerate(keys)}
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True)
    p.add_argument('--classifier',type=Path,default=ROOT/'outputs/item10-classifier-v1.4.0/classifier.joblib')
    a=p.parse_args();out=a.index.resolve()
    if (out/'benchmark_metrics.json').exists():raise ValueError('Benchmark results already recorded; do not overwrite')
    bm=json.loads((out/'benchmark_manifest.json').read_text());assert sha(out/'benchmark_queries.jsonl')==bm['queries_sha256'];assert sha(out/'index_manifest.json')==bm['index_manifest_sha256']
    rows=readrows(out/'benchmark_queries.jsonl');retriever=LegalRetriever(out);reports={};all_results=[]
    for method in ['bm25','semantic','hybrid']:
        scored=[];negative=[]
        for r in rows:
            started=time.perf_counter();response=retriever.search(r['question_text'],r['domain'],method,10,r['topic_ids']);elapsed=time.perf_counter()-started
            result={'query_id':r['query_id'],'scenario_family_id':r['scenario_family_id'],'language_style':r['language_style'],'method':method,'seconds':elapsed,'response':response}
            if r['relevant_provision_ids']:
                result['metrics']=per_query(r,response['hits']);result['relevant_provision_ids']=r['relevant_provision_ids'];scored.append(result)
            else:
                result['negative_passed']=response['status']==r['expected_status'] and not response['hits'];negative.append(result)
            all_results.append(result)
        summary=summarize(scored);summary['negative_controls']={'passed':sum(r['negative_passed'] for r in negative),'total':len(negative)}
        summary['mean_seconds_positive_including_initial_encoder_load']=float(np.mean([r['seconds'] for r in scored]));reports[method]=summary
        print(json.dumps({'method':method,'hit@5':summary['hit@5'],'recall@5':summary['recall@5'],'mrr@10':summary['mrr@10'],'negative_controls':summary['negative_controls']}),flush=True)
    jsonl(out/'benchmark_results.jsonl',all_results);save(out/'benchmark_metrics.json',{'role':'AI-authored development retrieval benchmark, not independent human/legal evaluation','oracle_domain':True,'positive_queries':bm['positive_queries'],'scenario_families':bm['positive_scenario_families'],'methods':reports,
        'config_sha256':sha(out/'retrieval_config.json'),'queries_sha256':bm['queries_sha256'],'default_method_fixed_before_benchmark':retriever.config['default_method'],
        'method_selection_or_tuning_on_queries':bool(retriever.manifest.get('method_selection')),'relevance_labels_exhaustive':False,'fresh_holdout':False})
    # A small integration check exercises the real frozen classifier's routes.
    import sys,joblib
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
    model=a.classifier;bundle=joblib.load(model)
    cases=[
        ('supported_consumer','A retail store refuses my blender warranty.'),
        ('supported_labor','My private employer owes overtime pay.'),
        ('partial','A retail store refuses my blender warranty. I have a complaint about my seafarer deployment.'),
        ('mixed_full','My private employer owes overtime pay. A retail store refuses my blender warranty.'),
        ('excluded','I have a complaint about my seafarer deployment.'),
        ('clarify','My employer has not paid my salary.'),
        ('evidence_gap','When should my private employer release my final pay and COE?'),
    ]
    integration=[]
    for name,text in cases:integration.append({'case':name,'input':text,'result':retriever.retrieve_question(text,bundle,retriever.config['default_method'],5)})
    save(out/'classifier_integration_results.json',{'classifier_model_version':bundle['model_version'],'classifier_model_path':str(model),'classifier_model_sha256':sha(model),'cases':integration,'answer_generation_allowed':False,'role':'AI-authored development integration checks'})
if __name__=='__main__':main()
