"""Explicit denominators, calibration and family-cluster development intervals."""
from __future__ import annotations
import math
from collections import Counter, defaultdict
import numpy as np
from evaluation_common import PRIMARY, SCOPE


def rate(records, numerator, denominator=lambda r: 1, *, repeats=2000, seed=20261017):
    groups = defaultdict(lambda: [0.0, 0.0])
    for row in records:
        n, d = numerator(row), denominator(row)
        if not 0 <= n <= d:
            raise ValueError('Invalid metric contribution')
        groups[row['family_id']][0] += n
        groups[row['family_id']][1] += d
    values = np.asarray([v for v in groups.values() if v[1] > 0], dtype=float)
    if not len(values):
        return {'numerator': 0, 'denominator': 0, 'value': None, 'families': 0,
                'family_cluster_bootstrap_95': None, 'interval_note': 'No eligible observations'}
    n, d = values.sum(axis=0)
    interval = None
    if len(values) >= 2 and repeats:
        rng = np.random.default_rng(seed)
        samples = values[rng.integers(0, len(values), size=(repeats, len(values)))].sum(axis=1)
        ratios = samples[:, 0] / samples[:, 1]
        interval = [float(x) for x in np.quantile(ratios, [.025, .975])]
    boundary = n == 0 or n == d
    return {'numerator': float(n), 'denominator': float(d), 'value': float(n / d), 'families': len(values),
        'family_cluster_bootstrap_95': interval,
        'interval_note': 'Descriptive grouped development interval; constant outcomes give a degenerate interval and cannot rule out unseen failures.'
                         if boundary else 'Descriptive grouped development interval; does not measure AI bias or establish independence.'}


def head(records, name, labels, bins=10):
    labeled = [r for r in records if r['expected']['expected_' + name] is not None]
    if not labeled:
        return {'count': 0, 'accuracy': None, 'macro_f1': None, 'per_class': {}, 'confusion_matrix': None, 'calibration': None}
    matrix = [[0 for _ in labels] for _ in labels]
    calibration = [[] for _ in range(bins)]
    brier, nll = [], []
    for row in labeled:
        p = row['actual']['classification']
        target, predicted = row['expected']['expected_' + name], p['predicted_' + name]
        if target not in labels or predicted not in labels:
            raise ValueError('Unknown classification label')
        matrix[labels.index(target)][labels.index(predicted)] += 1
        probs = p[name + '_probabilities']
        if set(probs) != set(labels) or any(type(x) not in {int, float} or not math.isfinite(x) or not 0 <= x <= 1 for x in probs.values()) or abs(sum(probs.values()) - 1) > 1e-6:
            raise ValueError('Invalid probability distribution')
        confidence = p[name + '_confidence']
        if not math.isfinite(confidence) or abs(confidence - probs[predicted]) > 1e-9:
            raise ValueError('Label confidence differs from predicted-label probability')
        calibration[min(int(confidence * bins), bins - 1)].append((confidence, target == predicted))
        brier.append(sum((probs[label] - int(label == target)) ** 2 for label in labels))
        nll.append(-math.log(max(probs[target], 1e-15)))
    classes = {}
    f1s = []
    for i, label in enumerate(labels):
        tp = matrix[i][i]; support = sum(matrix[i]); predicted_count = sum(row[i] for row in matrix)
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else None
        f1 = 2 * tp / (support + predicted_count) if support + predicted_count else None
        classes[label] = {'support': support, 'predicted_count': predicted_count,
                          'precision': precision, 'recall': recall, 'f1': f1}
        if support: f1s.append(f1)
    bin_rows = []
    ece = 0.0
    for i, values in enumerate(calibration):
        confidence = sum(v[0] for v in values) / len(values) if values else None
        accuracy = sum(v[1] for v in values) / len(values) if values else None
        if values: ece += len(values) / len(labeled) * abs(confidence - accuracy)
        bin_rows.append({'lower': i / bins, 'upper': (i + 1) / bins, 'count': len(values),
                         'mean_confidence': confidence, 'observed_accuracy': accuracy})
    return {'count': len(labeled), 'accuracy': sum(matrix[i][i] for i in range(len(labels))) / len(labeled),
        'macro_f1': sum(f1s) / len(f1s), 'macro_f1_labels': [k for k, v in classes.items() if v['support']],
        'per_class': classes, 'confusion_matrix': {'labels': labels, 'true_rows_predicted_columns': matrix},
        'calibration': {'ece': ece, 'multiclass_brier': sum(brier) / len(brier), 'negative_log_likelihood': sum(nll) / len(nll),
            'bins': bin_rows, 'meaning': 'Classifier label calibration on inspected development cases, not legal correctness.'}}


def summarize_group(records, protocol, intervals=True):
    repeats = protocol['bootstrap_replicates'] if intervals else 0
    opts = {'repeats': repeats, 'seed': protocol['bootstrap_seed']}
    classified = [r for r in records if r['expected']['expected_primary'] is not None]
    clarifications = [r for r in records if r['expected']['expected_route'] == 'clarify']
    judged = [r for r in records if r['assessment']['retrieval'] is not None]
    negative = [r for r in records if r['assessment']['negative_control_correct'] is not None]
    partially = [r for r in classified if r['expected']['expected_scope'] == 'partially_supported']
    unsupported = [r for r in classified if r['expected']['expected_scope'] == 'unsupported']
    supported = [r for r in classified if r['expected']['expected_scope'] != 'unsupported']
    return {'cases': len(records), 'families': len({r['family_id'] for r in records}),
        'primary': head(records, 'primary', PRIMARY, protocol['ece_bins']),
        'scope': head(records, 'scope', SCOPE, protocol['ece_bins']),
        'primary_accuracy': rate(classified, lambda r: int(r['assessment']['primary_correct']), **opts),
        'scope_accuracy': rate(classified, lambda r: int(r['assessment']['scope_correct']), **opts),
        'partial_support_recall': rate(partially, lambda r: int(r['actual']['classification']['predicted_scope'] == 'partially_supported'), **opts),
        'decisive_coverage': rate(classified, lambda r: int(r['actual']['classification']['routing_action'] != 'clarify'), **opts),
        'route_match': rate(records, lambda r: int(r['assessment']['route_correct']), **opts),
        'clarification_success': rate(clarifications, lambda r: int(r['assessment']['clarification_correct']), **opts),
        'unsupported_routing_admission': rate(unsupported, lambda r: int(r['actual']['classification']['substantive_answer_admitted']), **opts),
        'supported_routing_deferral': rate(supported, lambda r: int(r['actual']['classification']['routing_action'] == 'clarify'), **opts),
        'known_relevant_hit_at_1': rate(judged, lambda r: int(r['assessment']['retrieval']['hit_at_1']), **opts),
        'known_relevant_hit_at_5': rate(judged, lambda r: int(r['assessment']['retrieval']['hit_at_5']), **opts),
        'known_relevant_mrr_at_5': rate(judged, lambda r: r['assessment']['retrieval']['mrr_at_5'], **opts),
        'known_relevant_recall_at_5': rate(judged, lambda r: r['assessment']['retrieval']['known_relevant_recall_at_5'], **opts),
        'negative_candidate_leakage': rate(negative, lambda r: int(not r['assessment']['negative_control_correct']), **opts),
        'explicit_concern_match': rate(records, lambda r: sum(c['passed'] for c in r['assessment']['concern_checks']),
                                       lambda r: len(r['assessment']['concern_checks']), **opts),
        'quote_integrity': rate(records, lambda r: sum(r['assessment']['quote_checks']), lambda r: len(r['assessment']['quote_checks']), **opts),
        'current_guidance_candidate_coverage': rate(records, lambda r: int(r['actual']['current_drafting_allowed']), **opts),
        'error_counts': dict(Counter(issue for r in records for issue in r['assessment']['issues'])),
        'classification_routes': dict(Counter(r['actual']['classification']['routing_action'] for r in records)),
        'current_decisions': dict(Counter(r['actual']['current_decision'] for r in records))}


def screening_gates(summary, protocol):
    t = protocol['screening_targets']
    values = [
        ('primary_macro_f1', summary['primary']['macro_f1'], t['primary_macro_f1_min'], 'min'),
        ('scope_macro_f1', summary['scope']['macro_f1'], t['scope_macro_f1_min'], 'min'),
        ('partial_support_recall', summary['partial_support_recall']['value'], t['partially_supported_recall_min'], 'min'),
        ('out_of_scope_recall', summary['primary']['per_class'].get('out_of_scope', {}).get('recall'), t['out_of_scope_recall_min'], 'min'),
        ('unsupported_routing_admission', summary['unsupported_routing_admission']['value'], t['unsupported_routing_admission_max'], 'max'),
        ('decisive_coverage', summary['decisive_coverage']['value'], t['decisive_coverage_min'], 'min'),
        ('clarification_success', summary['clarification_success']['value'], t['clarification_success_min'], 'min'),
        ('retrieval_hit_at_5', summary['known_relevant_hit_at_5']['value'], t['retrieval_hit_at_5_min'], 'min'),
        ('negative_candidate_leakage', summary['negative_candidate_leakage']['value'], t['negative_candidate_leakage_max'], 'max'),
        ('quote_integrity', summary['quote_integrity']['value'], t['quote_integrity_min'], 'min'),
        ('explicit_concern_match', summary['explicit_concern_match']['value'], t['explicit_concern_match_min'], 'min')]
    return [{'metric': name, 'value': value, 'target': target, 'direction': direction,
             'passed': value is not None and (value >= target if direction == 'min' else value <= target)}
            for name, value, target, direction in values]


def summarize(records, protocol):
    if not records:
        raise ValueError('No completed predictions')
    overall = summarize_group(records, protocol)
    strata = {}
    for field in ['suite', 'language', 'variation']:
        strata[field] = {value: summarize_group([r for r in records if r[field] == value], protocol, intervals=field != 'variation')
                         for value in sorted({r[field] for r in records})}
    strata['topic'] = {value: summarize_group([r for r in records if value in r['expected']['topic_ids']], protocol, intervals=False)
                       for value in sorted({t for r in records for t in r['expected']['topic_ids']})}
    times = [r['seconds'] for r in records]
    return {'version': protocol['version'], 'role': 'inspected_AI_development_evaluation',
        'overall': overall, 'strata': strata, 'screening_gates': screening_gates(overall, protocol),
        'cases_with_any_issue': sum(bool(r['assessment']['issues']) for r in records),
        'latency_seconds': {'median': float(np.median(times)), 'p95': float(np.quantile(times, .95)),
                            'meaning': 'Local combined classification/preflight/excerpt verification with hash checks, excluding initialization and all LLM/network time.'},
        'generated_answers': {'status': 'not_measured', 'actual_llm_answers': 0, 'legal_answer_accuracy': None,
            'unsupported_claim_rate': None, 'false_decline_rate_on_verified_answerable_questions': None,
            'reason': 'No connected LLM drafter, no actual reviewed answers and no verified-current answerability judgments. Excerpt provenance is separate.'},
        'interpretation': ['All labeled questions are in classification denominators, including routing deferrals.',
            'General/typing retrieval relevance is unjudged; availability is not support correctness.',
            'Known-relevant retrieval labels are partial AI development judgments.',
            'Family bootstrap describes this development sample; no fresh holdout or population accuracy claim.',
            'Current guidance coverage of zero is reported as a limitation, never perfect answer accuracy.',
            'Supported routing deferrals are not legally adjudicated false declines.'],
        'independent_human_evaluation_completed': False, 'licensed_legal_review_completed': False,
        'answer_generation_allowed': False, 'deployment_allowed': False}
