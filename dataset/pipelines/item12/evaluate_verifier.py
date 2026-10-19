"""Run disclosed AI development fixtures, including nontrivial positive controls."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from contracts import PREFLIGHT_SCHEMA, RESULT_SCHEMA, validate
from development_cases import AS_OF, cases, fixture_verifier
from verification import EvidenceVerifier


def wilson(successes, count):
    if not count:
        return None
    z = 1.959963984540054
    p = successes / count
    denom = 1 + z * z / count
    center = (p + z * z / (2 * count)) / denom
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * count)) / count) / denom
    return [max(0.0, center - radius), min(1.0, center + radius)]


def reasons(result):
    return set(result.get('contract_errors', [])) | {r for c in result['claim_results'] for r in c['reasons']} | {
        r for c in result['components'] for r in c['reasons']}


def evaluate(verifier):
    fixtures = cases(verifier)
    records = []
    for case in fixtures:
        runtime = fixture_verifier(verifier, case['software_reviews']) if case['software_reviews'] is not None else verifier
        pre = runtime.preflight(case['question_text'], case['mode'])
        validate(pre, PREFLIGHT_SCHEMA)
        result = runtime.verify(case['question_text'], case['draft'], case['mode'])
        validate(result, RESULT_SCHEMA)
        observed = result['coverage']['components_with_preview']
        observed_ids = sorted({block['component_id'] for block in result['preview']})
        component_ids_ok = observed_ids == sorted(case['expected_preview_component_ids'])
        reason_ok = case['expected_reason'] is None or case['expected_reason'] in reasons(result)
        flags_ok = not any(result[k] for k in ['deployment_allowed', 'answer_generation_allowed', 'display_allowed'])
        route_ok = (case['case_id'] != 'clarification_route' or result['decision'] == 'clarify') and (
            case['case_id'] != 'excluded_route' or result['decision'] == 'refer_out_of_scope')
        records.append({'case_id': case['case_id'], 'category': case['category'],
                        'passed': observed == case['expected_preview_components'] and component_ids_ok and reason_ok and flags_ok and route_ok,
                        'expected_preview_components': case['expected_preview_components'],
                        'observed_preview_components': observed, 'expected_reason_found': reason_ok,
                        'expected_preview_component_ids': case['expected_preview_component_ids'],
                        'observed_preview_component_ids': observed_ids,
                        'verification': result})
    groups = {}
    for name in sorted({r['category'] for r in records}):
        group = [r for r in records if r['category'] == name]
        successes = sum(r['passed'] for r in group)
        groups[name] = {'passed': successes, 'total': len(group), 'rate': successes / len(group),
                        'wilson_95_interval': wilson(successes, len(group))}
    metrics = {'version': verifier.policy['version'], 'as_of': verifier.as_of.isoformat(),
        'provenance': 'AI-authored, inspected development software fixtures; not independent human/legal gold.',
        'passed': sum(r['passed'] for r in records), 'total': len(records), 'groups': groups,
        'decisions': dict(Counter(r['verification']['decision'] for r in records)),
        'interval_meaning': 'Descriptive binomial intervals on dependent hand-authored development controls; not real-world legal accuracy or confidence.',
        'legal_answer_accuracy_measured': False, 'independent_human_evaluation': False,
        'live_llm_called': False, 'canonical_sources_modified': False,
        'answer_generation_allowed': False, 'deployment_allowed': False}
    return fixtures, records, metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    # A new evaluation directory preserves earlier reports.
    args.output.mkdir(parents=True, exist_ok=False)
    fixtures, results, metrics = evaluate(EvidenceVerifier(as_of=AS_OF))
    for name, value in [('development_cases.json', fixtures), ('development_results.json', results), ('metrics.json', metrics)]:
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(metrics, indent=2))
    return int(metrics['passed'] != metrics['total'])


if __name__ == '__main__':
    raise SystemExit(main())
