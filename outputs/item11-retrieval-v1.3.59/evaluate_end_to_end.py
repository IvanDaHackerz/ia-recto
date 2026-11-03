"""Actual classifier-to-retrieval development evaluation without oracle domains."""
from __future__ import annotations
import argparse,collections,json,sys
from pathlib import Path
import joblib
from common import ROOT,readrows,save,jsonl,sha
from retrieval import LegalRetriever

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--index',type=Path,required=True)
    p.add_argument('--classifier',type=Path,required=True)
    a=p.parse_args()
    if (a.index/'end_to_end_metrics.json').exists():raise ValueError('Do not overwrite recorded evaluation')
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
    bundle=joblib.load(a.classifier);retriever=LegalRetriever(a.index)
    results=[]
    for q in readrows(a.index/'benchmark_queries.jsonl'):
        response=retriever.retrieve_question(q['question_text'],bundle,'bm25',10)
        prediction=response['classification']
        expected=set(q['relevant_provision_ids'])
        hits=[h for c in response['components'] for h in c['hits'][:5]]
        hit=bool(expected & {h['provision_id'] for h in hits}) if expected else None
        results.append({'query_id':q['query_id'],'scenario_family_id':q['scenario_family_id'],
            'language_style':q['language_style'],'expected_domain':q['domain'],
            'known_relevant_ids':sorted(expected),'hit_at_5_per_component':hit,
            'negative_passed':not hits if not expected else None,'response':response})
    positive=[r for r in results if r['known_relevant_ids']]
    negative=[r for r in results if not r['known_relevant_ids']]
    jsonl(a.index/'end_to_end_results.jsonl',results)
    summary={'role':'Inspected AI development cases; not independent human gold',
        'oracle_domain':False,'answer_generation_evaluated':False,'fresh_holdout':False,
        'classifier_version':bundle['model_version'],'classifier_path':str(a.classifier),
        'classifier_sha256':sha(a.classifier),'positive_rows':len(positive),
        'hit_at_5_per_component_count':sum(r['hit_at_5_per_component'] for r in positive),
        'hit_at_5_per_component':sum(r['hit_at_5_per_component'] for r in positive)/len(positive),
        'language':{lang:{'count':sum(r['language_style']==lang for r in positive),
            'hits':sum(r['hit_at_5_per_component'] for r in positive if r['language_style']==lang)}
            for lang in ['en','en_tl']},
        'routing_counts':dict(collections.Counter(r['response']['classification']['routing_action'] for r in positive)),
        'negative_controls':{'passed':sum(r['negative_passed'] for r in negative),'total':len(negative)},
        'missed_query_ids':[r['query_id'] for r in positive if not r['hit_at_5_per_component']],
        'deployment_allowed':False}
    save(a.index/'end_to_end_metrics.json',summary)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
