"""Bounded, append-only live AI development evaluation of 100 frozen questions."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from backend.application.service import ApplicationService
from backend.application.controls import CancellableTransport, UsageLedger
from backend.application.conversation import GENERAL_SCOPE
from backend.application.identity import identity
from backend.application.privacy import redact
from backend.normalization_metrics import assess, summarize_path

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()] if Path(path).exists() else []


def prepare(target):
    if target.exists():
        raise ValueError('Use a new output directory; preserve every previous attempt')
    manifest = json.loads((BASE / 'case-manifest.json').read_text(encoding='utf-8'))
    if sha(BASE / 'cases.json') != manifest['cases_sha256']:
        raise ValueError('Frozen question file changed')
    service = ApplicationService.configured()
    if service.normalizer.provider is None or service.development_provider is None:
        raise ValueError('Both providers must be configured')
    target.mkdir(parents=True)
    first_ledger=BASE / 'first-pass' / 'usage.sqlite3'
    shared_ledger=BASE / 'live-budget.sqlite3'
    if target.name != 'first-pass' and not shared_ledger.exists() and first_ledger.exists():
        shutil.copyfile(first_ledger, shared_ledger)
    shutil.copyfile(BASE / 'cases.json', target / 'cases.json')
    shutil.copyfile(__file__, target / 'evaluator.py')
    save(target / 'source-allowlist.json', sorted({hashlib.sha256(v['parent_text'].encode()).hexdigest() for v in service.verifier.records.values()}))
    current=json.loads((ROOT / 'CURRENT_ARTIFACTS.json').read_text(encoding='utf-8'))
    save(target / 'current-config-snapshot.json', current)
    save(target / 'protocol.json', {
        **{k:current[k] for k in ['classifier','retrieval','verifier']},
        'prepared_at_utc': datetime.now(timezone.utc).isoformat(), **identity(),
        'cases_sha256': sha(target / 'cases.json'), 'evaluator_sha256': sha(__file__),
        'input_forms': 100, 'maximum_provider_attempts': 750, 'estimated_cost_stop_usd': .50,
        'parallel_workers': 2, 'automatic_retries': 0,
        'provider': service.development_provider.name, 'model': service.development_provider.model,
        'normalizer_model': service.normalizer.provider.model,
        'configured_estimate_rates_per_million': UsageLedger.PRICES,
        'role': 'AI-authored synthetic development usability test',
        'independent_human_questions': 0, 'legal_accuracy_measured': False,
        'rejected_drafts': 'Saved only in local diagnostic file; never displayed as approved answers',
        'budget': 'Shared replay ledger seeded from first pass; final repair protocol extends the attempt ceiling to 750 while retaining the $0.50 total estimate cap; website limits unchanged; not verified billing',
        'export': 'Frozen fictional questions, accepted wording variants, precise conditional scope suffix, pinned corpus source text',
    })
    save(target / 'freeze.json', {name: sha(target / name) for name in ['cases.json', 'evaluator.py', 'source-allowlist.json', 'protocol.json', 'current-config-snapshot.json']})
    print('Prepared 100 frozen synthetic cases, two workers, 750 cumulative attempts maximum, unchanged $0.50 total estimated-cost stop.', flush=True)


def run(target, limit=None):
    frozen = json.loads((target / 'freeze.json').read_text(encoding='utf-8'))
    if any(sha(target / name) != value for name, value in frozen.items()):
        raise ValueError('Frozen input/protocol changed')
    protocol = json.loads((target / 'protocol.json').read_text(encoding='utf-8'))
    if identity()['runtime_signature'] != protocol['runtime_signature'] or sha(__file__) != protocol['evaluator_sha256']:
        raise ValueError('Runtime/evaluator changed since freeze')
    cases = json.loads((target / 'cases.json').read_text(encoding='utf-8'))
    by_id = {c['case_id']: c for c in cases}
    previous = read_rows(target / 'observations.jsonl')
    completed = {o['case']['case_id'] for o in previous}
    if len(completed) != len(previous):
        raise ValueError('Duplicate case observations')
    pending = [c for c in cases if c['case_id'] not in completed]
    if limit is not None:
        pending = pending[:limit]
    allowed_sources = set(json.loads((target / 'source-allowlist.json').read_text(encoding='utf-8')))
    service = ApplicationService.configured()
    ledger_path=target / 'usage.sqlite3' if target.name=='first-pass' else BASE / 'live-budget.sqlite3'
    service.ledger = UsageLedger(ledger_path, maximum_calls=protocol['maximum_provider_attempts'], maximum_usd=protocol['estimated_cost_stop_usd'])
    service.history_store = None
    suffix = '\n\nResponse scope: ' + GENERAL_SCOPE + ' Describe the recorded rules conditionally. Never assert that this person is a private-sector employee.'
    allowed_questions = {c['case_id']: set() for c in cases}
    def allow(cid, question):
        allowed_questions[cid].update([question, question + suffix])
    for case in cases:
        allow(case['case_id'], case['question_text'])
        allow(case['case_id'], redact(case['question_text'])['text'])
    lock = threading.Lock()
    diagnostics = (target / 'provider-completions.jsonl').open('a', encoding='utf-8')
    class FrozenTransport(CancellableTransport):
        def __call__(self, request, timeout):
            cid = self.context.request_id
            if cid not in by_id:
                raise RuntimeError('Request outside frozen cases')
            body = json.loads(request.data)
            if body['model'] not in {protocol['model'], protocol['normalizer_model']} or request.full_url != 'https://api.together.ai/v1/chat/completions':
                raise RuntimeError('Provider/model outside protocol')
            payload = json.loads(body['messages'][-1]['content'])
            question = payload.get('question_text', payload.get('question'))
            with lock:
                if question not in allowed_questions[cid]:
                    raise RuntimeError('Question outside frozen export allowlist')
            for component in payload.get('components', payload.get('source_components', [])):
                for source in component.get('sources', []):
                    if hashlib.sha256(source['parent_text'].encode()).hexdigest() not in allowed_sources:
                        raise RuntimeError('Source outside pinned corpus')
            response = super().__call__(request, timeout)
            # Only synthetic completion text, usage and public source IDs. No key,
            # headers or provider request objects are written to diagnostics.
            with lock:
                diagnostics.write(json.dumps({'case_id': cid, 'stage': self.context.calls[-1]['stage'],
                    'completion': response['choices'][0]['message'].get('content'),
                    'finish_reason': response['choices'][0].get('finish_reason'), 'usage': response.get('usage', {})}, ensure_ascii=False) + '\n')
                diagnostics.flush()
            if self.stage == 'normalization':
                try:
                    candidate = json.loads(response['choices'][0]['message']['content']).get('normalized_question')
                    if isinstance(candidate, str) and candidate:
                        with lock:
                            allow(cid, candidate)
                except (ValueError, TypeError, KeyError, IndexError):
                    pass
            return response
    def execute(case):
        start = time.monotonic()
        try:
            packet = service.chat({'question_text': case['question_text'], 'request_id': case['case_id'], 'use_ai': True, 'save_history': False}, session='ai100:' + case['case_id'])
            return {'case': case, 'normalized': {'packet': packet, 'assessment': assess(case, packet)}, 'elapsed_ms': (time.monotonic() - start) * 1000}
        except Exception as error:
            return {'case': case, 'error': getattr(error, 'code', type(error).__name__), 'elapsed_ms': (time.monotonic() - start) * 1000}
    observations = list(previous)
    try:
        with patch('backend.application.service.CancellableTransport', FrozenTransport), (target / 'observations.jsonl').open('a', encoding='utf-8') as stream, ThreadPoolExecutor(max_workers=2) as pool:
            for start in range(0, len(pending), 2):
                batch = list(pool.map(execute, pending[start:start + 2]))
                failure_codes = []
                for item in batch:
                    observations.append(item)
                    stream.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + '\n')
                    stream.flush()
                    packet = item.get('normalized', {}).get('packet', {})
                    exp = packet.get('explanation', {})
                    if exp.get('failure_code'):
                        failure_codes.append(exp['failure_code'])
                    print(item['case']['case_id'], exp.get('status', item.get('error')), exp.get('reason', ''), round(item['elapsed_ms']), 'ms', flush=True)
                if any(c in {'provider_auth_failed', 'daily_provider_limit', 'model_pricing_not_configured'} for c in failure_codes):
                    print('Stopped dispatch: configuration or budget limit. Remaining cases stay pending.', flush=True)
                    break
                if 'provider_circuit_open' in failure_codes:
                    print('Provider circuit opened; pausing dispatch for natural 60-second recovery, no retries.', flush=True)
                    time.sleep(61)
                if len(observations) % 10 == 0:
                    print('Usage:', service.ledger.summary(), flush=True)
    finally:
        diagnostics.close()
        finalize(target, observations, service.ledger.summary(), cases)


def finalize(target, observations, usage, cases):
    packets = [o for o in observations if 'normalized' in o]
    explanations = [o['normalized']['packet']['explanation'] for o in packets]
    generated = [e for e in explanations if e['status'] in {'generated', 'verified'}]
    latency = [o['elapsed_ms'] for o in observations]
    failures = [o['case']['case_id'] for o in packets if o['normalized']['assessment']['issues']]
    metrics = {
        'input_forms': len(observations), 'pending': len(cases) - len(observations),
        'successful_packets': len(packets), 'errors': dict(Counter(o['error'] for o in observations if 'error' in o)),
        'routing_and_retrieval': summarize_path(packets, 'normalized') if packets else None,
        'classification_or_route_failure_ids': failures,
        'explanation_status': dict(Counter(e['status'] for e in explanations)),
        'non_generated_reasons': dict(Counter(e['reason'] for e in explanations if e['status'] not in {'generated', 'verified'})),
        'failure_codes': dict(Counter(e['failure_code'] for e in explanations if e.get('failure_code'))),
        'validation_failures': dict(Counter(e['validation_failure'] for e in explanations if e.get('validation_failure'))),
        'generated_paragraphs': sum(len(e['claims']) for e in generated),
        'generated_without_automated_support': sum(not e.get('automated_support_checked') for e in generated),
        'normalizer_calls': sum((o['normalized']['packet'].get('normalization') or {}).get('llm_calls', 0) for o in packets),
        'latency_ms': {name: float(np.quantile(latency, q)) for name, q in [('p50', .5), ('p95', .95), ('maximum', 1)]} if latency else None,
        'usage': usage, 'legal_accuracy_measured': False, 'independent_human_questions': 0,
        'runtime_unchanged': identity()['runtime_signature'] == json.loads((target / 'protocol.json').read_text(encoding='utf-8'))['runtime_signature'],
        'limitations': ['Synthetic development questions; not independent human gold.', 'Only in-scope cases; no out-of-scope or partial-support recall estimate.', 'Same-model support acceptance does not establish legal correctness.', 'Known-relevant source IDs were not pre-judged; candidate count is not retrieval accuracy.'],
    }
    save(target / 'metrics.json', metrics)
    print('Summary:', json.dumps({k: metrics[k] for k in ['input_forms', 'pending', 'errors', 'explanation_status', 'non_generated_reasons', 'failure_codes', 'validation_failures', 'latency_ms', 'usage']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('target', type=Path)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.target.resolve())
    else:
        run(args.target.resolve(), args.limit)
