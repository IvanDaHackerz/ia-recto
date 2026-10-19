"""Frozen synthetic whole-application development replay; never human/legal accuracy."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import threading
import time
from unittest.mock import patch
import numpy as np
from backend.application.service import ApplicationService
from backend.application.controls import CancellableTransport,UsageLedger
from backend.application.identity import identity
from backend.application.privacy import redact
from backend.normalization_metrics import assess,summarize_path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/local-pipeline-cases-v1.1.0/cases.jsonl'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def rows(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def prepare(target):
    if target.exists():raise ValueError('Use a new immutable output directory')
    current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text(encoding='utf-8'))
    expected=json.loads((SOURCE.parent/'freeze.json').read_text(encoding='utf-8'))['cases_sha256']
    if sha(SOURCE)!=expected:raise ValueError('Frozen inputs changed')
    target.mkdir(parents=True);shutil.copyfile(SOURCE,target/'cases.jsonl');shutil.copyfile(__file__,target/'evaluator.py')
    service=ApplicationService.configured()
    if service.normalizer.provider is None or service.development_provider is None:raise ValueError('Both providers must be configured')
    source_hashes=sorted({hashlib.sha256(v['parent_text'].encode()).hexdigest() for v in service.verifier.records.values()})
    save(target/'source_text_allowlist.json',source_hashes)
    protocol={'version':target.name,'prepared_at_utc':datetime.now(timezone.utc).isoformat(),
        'role':'reused_AI_development_application_replay','independent_human_questions':0,
        **{k:current[k] for k in ['classifier','retrieval','verifier']},**identity(),
        'cases_sha256':sha(target/'cases.jsonl'),'evaluator_sha256':sha(__file__),
        'source_allowlist_sha256':sha(target/'source_text_allowlist.json'),
        'input_forms':len(rows(SOURCE)),'maximum_provider_attempts':2180,'estimated_cost_stop_usd':.50,
        'parallel_workers':4,'automatic_retries':0,'question_origin':'AI synthetic frozen cases only; no personal chat text',
        'provider':service.development_provider.name,'model':service.development_provider.model,
        'normalizer_model':service.normalizer.provider.model,
        'answer_accuracy_measured':False,'legal_review_performed':False,'support_judge_independent':False,
        'source_review_permissions_changed':False,'deployment_allowed':False}
    save(target/'protocol.json',protocol)
    save(target/'freeze.json',{name:sha(target/name) for name in ['cases.jsonl','evaluator.py','source_text_allowlist.json','protocol.json']})
    print('Frozen',protocol['input_forms'],'synthetic inputs; at most',protocol['maximum_provider_attempts'],'attempts and $0.50 estimate',flush=True)

def run(target):
    frozen=json.loads((target/'freeze.json').read_text(encoding='utf-8'))
    if any(sha(target/name)!=value for name,value in frozen.items()):raise ValueError('Protocol/input changed')
    protocol=json.loads((target/'protocol.json').read_text(encoding='utf-8'))
    if identity()['runtime_signature']!=protocol['runtime_signature'] or sha(__file__)!=protocol['evaluator_sha256']:raise ValueError('Application changed after freeze')
    if (target/'observations.jsonl').exists():raise ValueError('No selective retries or overwrite; prepare a new run')
    cases=rows(target/'cases.jsonl');by_id={c['case_id']:c for c in cases}
    allowed_sources=set(json.loads((target/'source_text_allowlist.json').read_text(encoding='utf-8')))
    service=ApplicationService.configured();service.ledger=UsageLedger(target/'usage.sqlite3',maximum_calls=protocol['maximum_provider_attempts'],maximum_usd=protocol['estimated_cost_stop_usd'])
    service.history_store=None
    allowed_questions={c['case_id']:{c['question_text'],redact(c['question_text'])['text']} for c in cases}
    lock=threading.Lock()
    class FrozenTransport(CancellableTransport):
        def __call__(self,request,timeout):
            case=by_id[self.context.request_id];body=json.loads(request.data)
            payload=json.loads(body['messages'][-1]['content'])
            question=payload.get('question_text',payload.get('question'))
            with lock:
                if question not in allowed_questions[case['case_id']]:raise RuntimeError('Question export outside frozen allowlist')
            for component in payload.get('components',payload.get('source_components',[])):
                for source in component.get('sources',[]):
                    if hashlib.sha256(source['parent_text'].encode()).hexdigest() not in allowed_sources:raise RuntimeError('Source export outside pinned eligible corpus')
            response=super().__call__(request,timeout)
            if self.stage=='normalization':
                try:
                    candidate=json.loads(response['choices'][0]['message']['content']).get('normalized_question')
                    if type(candidate) is str and candidate:
                        with lock:allowed_questions[case['case_id']].add(candidate)
                except (ValueError,TypeError,KeyError,IndexError):pass
            return response
    def execute(case):
        start=time.monotonic()
        try:
            packet=service.chat({'question_text':case['question_text'],'request_id':case['case_id'],'use_ai':True,'save_history':False},session='evaluation:'+case['case_id'])
            return {'case':case,'normalized':{'packet':packet,'assessment':assess(case,packet)},'elapsed_ms':(time.monotonic()-start)*1000}
        except Exception as error:
            # Never capture raw provider errors or headers. Every failure remains
            # in this run's denominator and is never silently retried.
            return {'case':case,'error':getattr(error,'code',type(error).__name__),'elapsed_ms':(time.monotonic()-start)*1000}
    observations=[]
    with patch('backend.application.service.CancellableTransport',FrozenTransport):
        with (target/'observations.jsonl').open('x',encoding='utf-8') as stream,ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(execute,c) for c in cases]
            for future in as_completed(futures):
                item=future.result();observations.append(item);stream.write(json.dumps(item,ensure_ascii=False,allow_nan=False)+'\n');stream.flush()
                if len(observations)%25==0:print('Completed',len(observations),'/',len(cases),'; usage:',service.ledger.summary(),flush=True)
    finalize(target,observations,service.ledger.summary())

def finalize(target,observations,usage):
    successful=[o for o in observations if 'normalized' in o]
    explanations=[o['normalized']['packet']['explanation'] for o in successful]
    generated=[e for e in explanations if e['status']=='generated']
    latencies=[o['elapsed_ms'] for o in observations]
    metrics={'role':'AI_development_complete_application_replay','input_forms':len(observations),
        'successful_packets':len(successful),'errors':dict(Counter(o['error'] for o in observations if 'error' in o)),
        'routing_and_retrieval':summarize_path(successful,'normalized'),
        'explanation_status':dict(Counter(e['status'] for e in explanations)),
        'withholding_reasons':dict(Counter(e['reason'] for e in explanations if e['status']!='generated')),
        'generated_paragraphs':sum(len(e['claims']) for e in generated),
        'generated_without_automated_support':sum(not e.get('automated_support_checked') for e in generated),
        'normalizer_calls':sum((o['normalized']['packet'].get('normalization') or {}).get('llm_calls',0) for o in successful),
        'normalizer_status':dict(Counter((o['normalized']['packet'].get('normalization') or {}).get('status','disabled') for o in successful)),
        'latency_ms':{name:float(np.quantile(latencies,q)) for name,q in [('p50',.5),('p95',.95),('maximum',1)]},
        'usage':usage,'independent_human_questions':0,'independent_legal_accuracy':None,
        'limitation':'Same-model automated support acceptance is not answer correctness. Cases are reused synthetic development inputs. HTTP/UI delivery is tested separately.',
        'runtime_unchanged':identity()['runtime_signature']==json.loads((target/'protocol.json').read_text(encoding='utf-8'))['runtime_signature']}
    save(target/'metrics.json',metrics)
    report='# Complete application development replay\n\n'+f"{len(observations)} frozen AI inputs; {len(successful)} returned packets; {len(generated)} generated responses passed exact citation and same-model automated support checks.\n\n"+f"Provider usage: {usage['provider_requests']} attempts; ${usage['estimated_usd']:.6f} estimated at configured rates. No automatic retries.\n\n"+'These results do not establish independent human accuracy, legal entailment, source currentness or deployment readiness. Withheld and failed cases remain in the report. See metrics.json and observations.jsonl.\n'
    (target/'REPORT.md').write_text(report,encoding='utf-8')
    save(target/'artifact_checksums.json',{p.name:sha(p) for p in target.iterdir() if p.is_file() and p.name not in {'artifact_checksums.json','usage.sqlite3'} })
    print(report,flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run']);parser.add_argument('output',type=Path);args=parser.parse_args()
    (prepare if args.action=='prepare' else run)(args.output.resolve())
