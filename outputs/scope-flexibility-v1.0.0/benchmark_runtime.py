"""Comparable warm raw-classifier timings, separate processes, no profiler."""
import argparse,json,random,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',required=True);a=p.parse_args()
sys.path.insert(0,str(ROOT/a.model))
import joblib
from classifier_runtime import predict_records
import referral_routing
referral_routing.ROOT=ROOT
b=joblib.load(ROOT/a.model/'classifier.joblib')
cases=[json.loads(l) for l in (HERE/'development.jsonl').read_text(encoding='utf-8').splitlines()]
predict_records(b,cases)
cases=cases[:40]*3;random.Random(20261020).shuffle(cases);times=[]
for case in cases:
 start=time.perf_counter();predict_records(b,[case]);times.append(1000*(time.perf_counter()-start))
times.sort();report={'model':a.model,'calls':len(times),'median_ms':statistics.median(times),'p95_ms':times[int(.95*len(times))-1],
 'minimum_ms':times[0],'maximum_ms':times[-1],'cold_start_excluded':True,'profiling_disabled':True,'network_calls':0}
(HERE/a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
