"""Run the pinned offline system on question text only, then score expectations."""
from __future__ import annotations
import argparse
import copy
import csv
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from evaluation_common import ROOT, HERE, ContractError, digest, jsonl, normalize, read, rows, save, sha, validate_cases, verify_packet


def prepare(output, protocol=None):
    from create_cases import create
    protocol = copy.deepcopy(protocol or read(HERE / 'protocol.json'))
    if protocol['role'] != 'development' or protocol['formal_final_evaluation_allowed']:
        raise ContractError('This runner executes development only. Independent final acceptance is not authorized by this protocol.')
    output = Path(output)
    parent = ROOT / protocol['parent_evaluation'] if protocol.get('parent_evaluation') else None
    if parent:
        verify_packet(parent)
        if sha(parent / 'cases.jsonl') != protocol['frozen_cases_sha256']:
            raise ContractError('Parent case hash differs from frozen repair cases')
        if protocol['screening_targets'] != read(parent / 'protocol.json')['screening_targets']:
            raise ContractError('Repair must retain the parent screening targets')
        cases = rows(parent / 'cases.jsonl')
    else:
        cases = create()
    eligible = {r['provision_id'] for r in rows(ROOT / protocol['retrieval'] / 'records.jsonl')}
    validate_cases(cases, eligible_ids=eligible)
    output.mkdir(parents=True, exist_ok=False)
    source_names = sorted({c['source_path'] for c in cases} | {'dataset/pipelines/item10/evaluation_policy.json'})
    save(output / 'protocol.json', protocol)
    if parent:
        # Preserve bytes as well as cases/expectations; no new gold or cases.
        (output / 'cases.jsonl').write_bytes((parent / 'cases.jsonl').read_bytes())
    else:
        jsonl(output / 'cases.jsonl', cases)
    save(output / 'case_manifest.json', {'case_count': len(cases), 'suite_counts': dict(Counter(c['suite'] for c in cases)),
        'families': len({c['family_id'] for c in cases}), 'role': 'development',
        'new_ai_system_questions': sum(c['suite'] == 'system' for c in cases),
        'new_training_questions': 0, 'independent_human_questions': 0,
        'parent_evaluation': protocol.get('parent_evaluation'),
        'reused_frozen_cases': bool(parent),
        'new_questions_in_this_revision': 0 if parent else sum(c['suite'] == 'system' for c in cases),
        'source_sha256': {name: sha(ROOT / name) for name in source_names}})
    save(output / 'split_membership.json', {'development': [c['case_id'] for c in cases], 'independent_final': [],
        'families': {f: [c['case_id'] for c in cases if c['family_id'] == f] for f in sorted({c['family_id'] for c in cases})},
        'note': 'Previously inspected material and new AI cases remain development. No random relabeling as an untouched test.'})
    # Written before constructing the runtime or observing any predictions.
    save(output / 'protocol_freeze.json', {'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'prepared_before_inference', 'protocol_sha256': sha(output / 'protocol.json'),
        'cases_sha256': sha(output / 'cases.jsonl'), 'case_manifest_sha256': sha(output / 'case_manifest.json'),
        'split_membership_sha256': sha(output / 'split_membership.json'),
        'runtime_source_sha256': {p.name: sha(p) for p in HERE.iterdir() if p.is_file()},
        'no_predictions_observed_by_this_run': True})
    return output


def verify_freeze(output):
    output = Path(output)
    frozen = read(output / 'protocol_freeze.json')
    for name in ['protocol', 'cases', 'case_manifest', 'split_membership']:
        filename = name + ('.jsonl' if name == 'cases' else '.json')
        if sha(output / filename) != frozen[name + '_sha256']:
            raise ValueError('Evaluation inputs changed after freeze: ' + filename)
    for name, expected in frozen['runtime_source_sha256'].items():
        if sha(HERE / name) != expected:
            raise ValueError('Evaluation code changed after freeze: ' + name)
    for name, expected in read(output / 'case_manifest.json')['source_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('Evaluation source changed after freeze: ' + name)


def execute_question(verifier, question):
    """The only input to inference is the original question, never its labels/IDs."""
    from classifier_runtime import predict_records
    prediction = predict_records(verifier.bundle, [{'question_text': question}])[0]
    recorded = verifier.preflight(question, 'recorded_excerpt')
    current = verifier.preflight(question, 'current_guidance')
    if any(recorded['routing'][k] != prediction[k] for k in ['predicted_primary', 'predicted_scope', 'routing_action']):
        raise ValueError('Classifier and verifier integration disagree')
    draft = verifier.excerpt_draft(question, recorded)
    post = verifier.verify(question, draft, 'recorded_excerpt') if draft['claims'] else None
    components = []
    for c in recorded['components']:
        components.append({'component_id': c['component_id'], 'query': c['query'], 'domain': c['allowed_domain'],
            'retrieval_status': c['retrieval_status'], 'evidence_ready': c['evidence_ready'],
            'candidates': [{k: h[k] for k in ['chunk_id', 'provision_id', 'document_id', 'score',
                'citation_display', 'source_locator', 'normalized_char_start', 'normalized_char_end']} for h in c['candidates']]})
    return {'classification': prediction, 'components': components,
        'recorded_decision': recorded['decision'], 'recorded_excluded_components': recorded['excluded_components'],
        'current_decision': current['decision'], 'current_drafting_allowed': current['offline_drafting_allowed'],
        'current_source_gate_reasons': sorted({reason for c in current['components'] for g in c['evidence_gates'] for reason in g['reasons']}),
        'excerpt_draft': draft if draft['claims'] else None, 'excerpt_verification': post,
        'answer_generation_allowed': False, 'deployment_allowed': False,
        'live_flags_off': all(not r[k] for r in [recorded, current] + ([post] if post else [])
                             for k in ['answer_generation_allowed', 'deployment_allowed', 'display_allowed'])}


def relevant_ranks(case, observation):
    expected = set(case['relevant_ids'])
    if not expected:
        return None
    # Ranking resets per supported component; duplicate provisions count once
    # toward known-relevant coverage. No oracle domain/IDs enter inference.
    ranks = [rank for c in observation['components'] for rank, h in enumerate(c['candidates'], 1) if h['provision_id'] in expected]
    found = {h['provision_id'] for c in observation['components'] for h in c['candidates'] if h['provision_id'] in expected}
    return {'hit_at_1': 1 in ranks, 'hit_at_5': bool(ranks), 'mrr_at_5': 1 / min(ranks) if ranks else 0.0,
            'known_relevant_recall_at_5': len(found) / len(expected), 'known_relevant_ids_found': sorted(found)}


def judge_concerns(case, observation):
    checks = []
    reliable = [c for c in observation['classification'].get('component_evidence', []) if c['atomic_evidence_strength'] >= .5]
    for expected in case['concerns']:
        def anchored(text):
            text = ' ' + normalize(text) + ' '
            return any(' ' + normalize(anchor) + ' ' in text for anchor in expected['anchors'])
        if expected['domain'] == 'excluded':
            matched = [c for c in reliable if c['category'] == 'excluded' and anchored(c['text'])]
            leaked = [c for c in observation['components'] if anchored(c['query'])]
            passed = bool(matched) and not leaked
            checks.append({'domain': 'excluded', 'anchors': expected['anchors'], 'passed': passed,
                           'matched_count': len(matched), 'leaked_count': len(leaked)})
        else:
            matched = [c for c in observation['components'] if c['domain'] == expected['domain'] and anchored(c['query'])]
            found = {h['provision_id'] for c in matched for h in c['candidates']}
            has_evidence = any(c['candidates'] for c in matched)
            evidence_ok = not has_evidence if expected['evidence_gap'] else bool(found & set(expected['relevant_ids'])) if expected['relevant_ids'] else has_evidence
            checks.append({'domain': expected['domain'], 'anchors': expected['anchors'],
                'passed': bool(matched) and evidence_ok, 'matched_count': len(matched),
                'evidence_gap_expected': expected['evidence_gap'], 'retrieved_ids': sorted(found)})
    return checks


def assess(case, actual):
    p = actual['classification']
    labeled = case['expected_primary'] is not None
    primary_ok = p['predicted_primary'] == case['expected_primary'] if labeled else None
    scope_ok = p['predicted_scope'] == case['expected_scope'] if labeled else None
    route_ok = p['routing_action'] == case['expected_route']
    clarification_ok = route_ok and (case['expected_clarification_reason'] is None or p['reason'] == case['expected_clarification_reason'])
    domains = sorted({c['domain'] for c in actual['components']})
    domain_ok = domains == case['expected_domains'] if case['expected_route'] != 'clarify' else not domains
    has_excluded = any(c['category'] == 'excluded' and c['atomic_evidence_strength'] >= .5
                       for c in p.get('component_evidence', []))
    excluded_ok = has_excluded == case['expected_excluded'] if labeled else None
    relevance = relevant_ranks(case, actual)
    concerns = judge_concerns(case, actual)
    negative_ok = not any(c['candidates'] for c in actual['components']) if case['retrieval_judgment'] == 'no_candidates' else None
    post = actual['excerpt_verification']
    quotation_checks = [c['passed'] for c in post['claim_results']] if post else []
    issues = []
    if labeled and not primary_ok: issues.append('primary_label_mismatch')
    if labeled and not scope_ok: issues.append('scope_label_mismatch')
    if not route_ok: issues.append('routing_mismatch')
    if case['expected_route'] == 'clarify' and not clarification_ok: issues.append('clarification_relevance_mismatch')
    if not domain_ok: issues.append('supported_domain_coverage_mismatch')
    if excluded_ok is False: issues.append('excluded_concern_identification_mismatch')
    if relevance is not None and not relevance['hit_at_5']: issues.append('known_relevant_provision_missed')
    if negative_ok is False: issues.append('negative_control_candidate_leak')
    if concerns and not all(c['passed'] for c in concerns): issues.append('explicit_concern_expectation_mismatch')
    if quotation_checks and not all(quotation_checks): issues.append('quote_integrity_failure')
    if not actual['live_flags_off']: issues.append('live_permission_leak')
    return {'primary_correct': primary_ok, 'scope_correct': scope_ok, 'route_correct': route_ok,
        'clarification_correct': clarification_ok if case['expected_route'] == 'clarify' else None,
        'domain_coverage_correct': domain_ok, 'excluded_identification_correct': excluded_ok,
        'retrieval': relevance, 'negative_control_correct': negative_ok,
        'concern_checks': concerns, 'quote_checks': quotation_checks, 'issues': issues}


def run(output):
    output = Path(output)
    if (output / 'predictions.jsonl').exists() or (output / 'execution_started.json').exists():
        raise ValueError('This run was already started; prepare a new version, preserving earlier results')
    verify_freeze(output)
    protocol, cases = read(output / 'protocol.json'), rows(output / 'cases.jsonl')
    validate_cases(cases)
    verify_packet(ROOT / protocol['verifier'], runtime=True)
    from verification import EvidenceVerifier
    verifier = EvidenceVerifier(as_of=protocol['as_of'])
    if verifier.policy['classifier'] != protocol['classifier'] or verifier.policy['retrieval'] != protocol['retrieval']:
        raise ValueError('Runtime versions differ from protocol')
    save(output / 'execution_started.json', {'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'freeze_sha256': sha(output / 'protocol_freeze.json'), 'role': 'development'})
    results = []
    with (output / 'predictions.jsonl').open('x', encoding='utf-8') as stream:
        for i, case in enumerate(cases, 1):
            start = time.perf_counter()
            actual = execute_question(verifier, case['question_text'])
            row = {'case_id': case['case_id'], 'suite': case['suite'], 'family_id': case['family_id'],
                'language': case['language'], 'variation': case['variation'], 'expected': case,
                'actual': actual, 'assessment': assess(case, actual), 'seconds': time.perf_counter() - start}
            stream.write(__import__('json').dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
            results.append(row)
            if i % 25 == 0:
                print(f'Evaluated {i}/{len(cases)} development cases', flush=True)
    verify_freeze(output)
    from evaluation_metrics import summarize
    metrics = summarize(results, protocol)
    save(output / 'metrics.json', metrics)
    jsonl(output / 'error_log.jsonl', [r for r in results if r['assessment']['issues']])
    with (output / 'results.csv').open('x', encoding='utf-8-sig', newline='') as stream:
        fields = ['case_id', 'suite', 'family_id', 'language', 'variation', 'question_text', 'expected_primary', 'actual_primary',
            'expected_scope', 'actual_scope', 'expected_route', 'actual_route', 'primary_confidence', 'scope_confidence',
            'known_hit_at_5', 'current_decision', 'excerpt_decision', 'issues']
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for r in results:
            p, e, a = r['actual']['classification'], r['expected'], r['assessment']
            values = [r['case_id'], r['suite'], r['family_id'], r['language'], r['variation'],
                e['question_text'], e['expected_primary'], p['predicted_primary'], e['expected_scope'], p['predicted_scope'],
                e['expected_route'], p['routing_action'], p['primary_confidence'], p['scope_confidence'],
                a['retrieval']['hit_at_5'] if a['retrieval'] else '', r['actual']['current_decision'],
                r['actual']['excerpt_verification']['decision'] if r['actual']['excerpt_verification'] else 'not_run_no_claims',
                '|'.join(a['issues'])]
            writer.writerow(dict(zip(fields, [safe_csv(value) for value in values])))
    return results, metrics


def safe_csv(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--prepare-only', action='store_true')
    modes.add_argument('--run-prepared', action='store_true')
    args = parser.parse_args()
    if not args.run_prepared: prepare(args.output)
    if not args.prepare_only: run(args.output)
