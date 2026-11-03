"""Disclosed synthetic development checks, always AI off; not legal accuracy."""
import csv,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.terminal_test import load_runtime
def write(path,v):path.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    service=ApplicationService(verifier=load_runtime(),normalizer=ConditionalNormalizer())
    old=json.loads((ROOT/'outputs/website-field-check-v1.0.0/cases.json').read_text())
    with (ROOT/'dataset/data_contract/topic_taxonomy.csv').open(encoding='utf-8-sig') as f:taxonomy={r['topic_id']:r for r in csv.DictReader(f)}
    checks=[]
    for c in old:
        flow={'supported':'local_sources','supported_gap':'local_sources','mixed':'local_sources','partial':'local_sources','excluded':'referral'}.get(c['expect'],c['expect'])
        row={'id':c['id'],'q':c['q'],'flow':flow}
        if c['id'] in taxonomy:
            t=taxonomy[c['id']];row.update(primary=t['domain'] if t['scope_status']=='supported' else 'out_of_scope',scope='fully_supported' if t['scope_status']=='supported' else 'unsupported')
        elif c['id']=='incidental.employer':row.update(primary='labor',scope='fully_supported')
        elif c['id'].startswith('mixed.'):row.update(primary='mixed',scope='fully_supported' if c['id']=='mixed.supported' else 'partially_supported')
        checks.append(row)
    fresh=json.loads((HERE/'fresh_cases.json').read_text())
    names=[('regression',checks),('fresh_synthetic',fresh)]
    summary={'provenance':'AI-authored development/regression checks, not independent human or legal validation','llm_calls':0,'sets':{}}
    for name,cases in names:
        results=[]
        for c in cases:
            p=service.chat({'question_text':c['q'],'use_ai':False})
            r=p['result'];route=r['routing'];kind=p['response']['kind']
            flow='clarify' if kind=='clarification' else 'referral' if kind=='referral' else 'local_sources'
            label_correct=all(route['predicted_'+k]==c[k] for k in ['primary','scope'] if k in c)
            quotes=p['response']['quotes']
            exact=all(q['quote'] in service.verifier.records[q['chunk_id']]['parent_text'] for q in quotes)
            results.append({'case':c,'flow':flow,'flow_correct':flow==c['flow'],'labels_correct':label_correct,
                            'quotes_exact':exact,'quote_headings':[service.verifier.records[q['chunk_id']]['heading'] for q in quotes],
                            'quote_provisions':[service.verifier.records[q['chunk_id']]['provision_id'] for q in quotes],
                            'packet':p})
        write(HERE/(name+'-results.json'),results)
        summary['sets'][name]={'count':len(results),'flow_matches':sum(r['flow_correct'] for r in results),
            'labeled':sum('primary' in r['case'] for r in results),
            'label_matches':sum(r['labels_correct'] for r in results if 'primary' in r['case']),
            'exact_quote_cases':sum(r['quotes_exact'] for r in results),'quoted_responses':sum(bool(r['quote_headings']) for r in results),
            'median_local_analysis_ms':statistics.median(r['packet']['total_query_ms'] for r in results),
            'failures':[{'id':r['case']['id'],'expected':r['case'],'flow':r['flow'],'routing':r['packet']['result']['routing']} for r in results if not (r['flow_correct'] and r['labels_correct'])]}
    write(HERE/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
