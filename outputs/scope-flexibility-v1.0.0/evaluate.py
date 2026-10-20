"""Offline raw classifier diagnostics; never calls an LLM or network service."""
import argparse, collections, hashlib, json, sys, time, cProfile, pstats
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
import joblib
from classifier_runtime import predict_records

def main():
    p=argparse.ArgumentParser();p.add_argument('--split',default='development',choices=['development','reserved']);p.add_argument('--name',required=True)
    p.add_argument('--model',default='outputs/item10-classifier-v1.5.16');p.add_argument('--profile',action='store_true');args=p.parse_args()
    path=HERE/(args.split+'.jsonl');manifest=json.loads((HERE/'frozen_manifest.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['files'][path.name]['sha256']
    if args.split=='reserved':assert (HERE/'implementation_frozen.json').exists(),'Freeze implementation first'
    dest=HERE/(args.name+'.json');assert not dest.exists(),'Immutable evaluation result exists'
    cases=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
    start=time.perf_counter();bundle=joblib.load(ROOT/args.model/'classifier.joblib');load_ms=(time.perf_counter()-start)*1000
    start=time.perf_counter();predictions=predict_records(bundle,cases);cold_batch_ms=(time.perf_counter()-start)*1000
    timings=[]
    profiler=cProfile.Profile()
    if args.profile:profiler.enable()
    for case in cases[:20]:
        start=time.perf_counter();predict_records(bundle,[case]);timings.append((time.perf_counter()-start)*1000)
    if args.profile:
        profiler.disable();profiler.dump_stats(str(HERE/(args.name+'.prof')))
        with (HERE/(args.name+'-profile.txt')).open('w') as f:pstats.Stats(profiler,stream=f).sort_stats('cumtime').print_stats(30)
    records=[];counts=collections.Counter();topic=collections.defaultdict(collections.Counter)
    for case,result in zip(cases,predictions):
        checks={'route':case['expected_route']==result['routing_action']}
        if 'expected_primary' in case:
            checks.update(primary=case['expected_primary']==result['predicted_primary'],scope=case['expected_scope']==result['predicted_scope'])
        counts.update({k+'_correct':int(v) for k,v in checks.items()});counts.update({k+'_total':1 for k in checks})
        topic[case['topic_id']].update(total=1,passed=int(all(checks.values())))
        records.append({'case':case,'checks':checks,'passed':all(checks.values()),'actual':result})
    out={'model':args.model,'split':args.split,'network_calls':0,'counts':counts,'all_passed':sum(r['passed'] for r in records),
        'total':len(cases),'per_topic':topic,'load_ms':load_ms,'cold_batch_ms':cold_batch_ms,
        'warm_single_ms':{'median':sorted(timings)[len(timings)//2],'max':max(timings),'values':timings},'records':records}
    dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in {'records','per_topic'}},indent=2))
    for r in records:
        if not r['passed']:
            a=r['actual'];print(r['case']['case_id'],r['checks'],a['predicted_primary'],a['routing_action'],a['reason'],repr(r['case']['question_text']))

if __name__=='__main__':main()
