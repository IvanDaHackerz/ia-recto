"""Audit Item 12 on the same 67 inspected Item 11 development cases; no new gold."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'dataset/pipelines/item12'))
from contracts import PREFLIGHT_SCHEMA, RESULT_SCHEMA, validate
from verification import EvidenceVerifier

v = EvidenceVerifier(as_of='2026-10-17')
source = ROOT / v.policy['retrieval'] / 'benchmark_queries.jsonl'
queries = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line.strip()]
records = []
for q in queries:
    start = time.perf_counter()
    pre = v.preflight(q['question_text'], 'recorded_excerpt')
    current = v.preflight(q['question_text'])
    validate(pre, PREFLIGHT_SCHEMA)
    validate(current, PREFLIGHT_SCHEMA)
    expected = set(q['relevant_provision_ids'])
    flags_ok = all(not result[k] for result in [pre, current] for k in
                   ['answer_generation_allowed', 'deployment_allowed', 'display_allowed'])
    if expected:
        draft = {'schema_version': '1.0', 'question_text': q['question_text'], 'claims': []}
        for component in pre['components']:
            hit = next((h for h in component['candidates'] if h['provision_id'] in expected), None)
            if hit is None:
                continue
            draft['claims'].append({'claim_id': component['component_id'] + '_quote',
                'component_id': component['component_id'], 'kind': 'source_excerpt', 'text': hit['parent_text'],
                'evidence': [{k: hit[k] for k in ['chunk_id', 'provision_id', 'document_id']} |
                             {'quote': hit['parent_text'], 'start': 0, 'end': len(hit['parent_text'])}]})
        post = v.verify(q['question_text'], draft, 'recorded_excerpt')
        validate(post, RESULT_SCHEMA)
        passed = flags_ok and bool(draft['claims']) and post['offline_preview_allowed'] and not current['offline_drafting_allowed']
    else:
        post = None
        no_candidates = not any(c['candidates'] for c in pre['components'])
        expected_decision = 'insufficient_evidence' if q['expected_status'] == 'no_eligible_evidence' else 'refer_out_of_scope'
        passed = flags_ok and no_candidates and pre['decision'] == expected_decision and not current['offline_drafting_allowed']
    records.append({'query_id': q['query_id'], 'scenario_family_id': q['scenario_family_id'],
        'positive': bool(expected), 'passed': bool(passed), 'seconds_for_combined_checks': time.perf_counter() - start,
        'preflight': pre, 'current_guidance_preflight': current, 'postflight': post})
summary = {'role': 'Reused inspected AI Item 11 development cases, not independent human gold or Item 13 final evaluation.',
    'total': len(records), 'passed': sum(r['passed'] for r in records),
    'positive_cases': sum(r['positive'] for r in records),
    'positive_passed': sum(r['passed'] and r['positive'] for r in records),
    'negative_cases': sum(not r['positive'] for r in records),
    'negative_passed': sum(r['passed'] and not r['positive'] for r in records),
    'current_guidance_candidates_permitted': sum(r['current_guidance_preflight']['offline_drafting_allowed'] for r in records),
    'failed_query_ids': [r['query_id'] for r in records if not r['passed']],
    'live_llm_called': False, 'legal_answer_accuracy_measured': False, 'deployment_allowed': False}
for name, value in [('integration_results.json', records), ('integration_summary.json', summary)]:
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if summary['passed'] == summary['total'] else 1)
