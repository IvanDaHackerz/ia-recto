"""Metric, provenance, freeze and review-boundary software tests; no human gold."""
from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import runner
from answer_evaluation import evaluate_answers
from create_cases import base, concern, create, system_cases
from evaluation_common import ROOT, HERE, PRIMARY, ContractError, digest, read, save, validate_cases
from evaluation_metrics import head, rate, screening_gates, summarize_group

PROTOCOL = read(HERE / 'protocol.json')


def case(cid='A', primary='labor', scope='fully_supported'):
    return base(cid, 'general', cid, 'A private employment wage question ' + cid, 'en', primary, scope,
                ['labor'] if primary == 'labor' else [], primary == 'out_of_scope', 'source.jsonl', cid)


def observation(primary='labor', scope='fully_supported', route='retrieve_supported_evidence'):
    p = {'predicted_primary': primary, 'predicted_scope': scope, 'routing_action': route, 'reason': 'test',
        'primary_confidence': 1.0, 'scope_confidence': 1.0,
        'primary_probabilities': {c: float(c == primary) for c in PRIMARY},
        'scope_probabilities': {c: float(c == scope) for c in ['fully_supported', 'partially_supported', 'unsupported']},
        'component_evidence': [], 'substantive_answer_admitted': route in {'retrieve_supported_evidence', 'retrieve_supported_components'}}
    return {'classification': p, 'components': [], 'excerpt_verification': None,
            'current_drafting_allowed': False, 'current_decision': 'insufficient_evidence', 'live_flags_off': True}


def record(c=None, a=None):
    c, a = c or case(), a or observation()
    return {'case_id': c['case_id'], 'family_id': c['family_id'], 'suite': c['suite'], 'language': c['language'],
            'variation': c['variation'], 'expected': c, 'actual': a, 'assessment': runner.assess(c, a), 'seconds': .01}


def answer_and_review():
    c = case()
    draft = {'schema_version': '1.0', 'question_text': c['question_text'], 'claims': [{
        'claim_id': 'claim1', 'component_id': 'concern_001', 'kind': 'paraphrase', 'text': 'Software test claim',
        'evidence': [{'chunk_id': 'testchunk', 'provision_id': 'testprovision', 'document_id': 'testdoc',
                      'start': 0, 'end': 4, 'quote': 'test'}]}]}
    answer = {'case_id': c['case_id'], 'origin': 'software_fixture', 'provider': 'test', 'model': 'test',
              'prompt_sha256': '0' * 64, 'generated_at': '2026-10-17T00:00:00+00:00', 'draft': draft}
    review = {'case_id': c['case_id'], 'answer_sha256': digest(answer), 'question_sha256': digest(c['question_text']),
        'protocol_sha256': '1' * 64, 'review_kind': 'software_fixture', 'reviewer_id': 'simulation',
        'credential_reference': 'Invented software fixture, no actual reviewer', 'jurisdiction': 'PH',
        'license_attested': True, 'reviewed_on': '2026-10-17', 'current_applicability_checked': True,
        'answer_relevant': True, 'coverage_complete': True, 'clear': True,
        'claim_findings': [{'claim_id': 'claim1', 'supported': True, 'qualifications_preserved': True,
                           'sources_relevant': True, 'rationale': 'Simulated test finding only'}]}
    return c, answer, review


class EvaluationTests(unittest.TestCase):
    def test_case_inventory_and_provenance(self):
        cases = create()
        self.assertEqual(len(cases), 291)
        self.assertEqual(len(system_cases()), 24)
        self.assertTrue(all(c['origin'] == 'ai_authored' and c['role'] == 'development' for c in cases))
        self.assertEqual(sum(c['expected_primary'] is None for c in cases), 23)

    def test_variants_are_grouped(self):
        cases = system_cases()
        self.assertEqual(len({c['family_id'] for c in cases}), 8)
        self.assertTrue(all(sum(x['family_id'] == c['family_id'] for x in cases) == 3 for c in cases))

    def test_duplicate_case_and_question_rejected(self):
        c = case()
        with self.assertRaises(ContractError): validate_cases([c, copy.deepcopy(c)])
        duplicate = copy.deepcopy(c); duplicate['case_id'] = 'B'
        with self.assertRaises(ContractError): validate_cases([c, duplicate])

    def test_development_cannot_be_relabelled_final(self):
        c = case(); c['role'] = 'final'
        with self.assertRaises(ContractError): validate_cases([c])
        c = case(); c['origin'] = 'independent_human_written'
        with self.assertRaises(ContractError): validate_cases([c])

    def test_absent_relevance_ids_rejected(self):
        c = case(); c.update(retrieval_judgment='known_relevant', relevant_ids=['missing'])
        with self.assertRaises(ContractError): validate_cases([c], eligible_ids=[])

    def test_unjudged_cases_do_not_become_retrieval_failures(self):
        c, a = case(), observation()
        self.assertIsNone(runner.relevant_ranks(c, a))
        self.assertNotIn('known_relevant_provision_missed', runner.assess(c, a)['issues'])

    def test_known_relevant_ranks_and_partial_recall(self):
        c, a = case(), observation()
        c.update(retrieval_judgment='known_relevant', relevant_ids=['p1', 'p2'])
        a['components'] = [{'candidates': [{'provision_id': 'unknown'}, {'provision_id': 'p1'}]}]
        r = runner.relevant_ranks(c, a)
        self.assertFalse(r['hit_at_1']); self.assertTrue(r['hit_at_5'])
        self.assertEqual(r['mrr_at_5'], .5); self.assertEqual(r['known_relevant_recall_at_5'], .5)

    def test_no_candidates_control_detects_leak(self):
        c, a = case(), observation(); c['retrieval_judgment'] = 'no_candidates'
        a['components'] = [{'domain': 'labor', 'candidates': [{'provision_id': 'p1'}]}]
        self.assertFalse(runner.assess(c, a)['negative_control_correct'])

    def test_excluded_concern_leak_is_detected(self):
        c, a = case(), observation()
        c['concerns'] = [concern('excluded', ['bank'])]
        a['classification']['component_evidence'] = [{'category': 'excluded', 'text': 'bank fee', 'atomic_evidence_strength': 1}]
        a['components'] = [{'domain': 'consumer', 'query': 'bank fee', 'candidates': []}]
        self.assertFalse(runner.judge_concerns(c, a)[0]['passed'])

    def test_anchors_use_whole_normalized_words(self):
        c, a = case(), observation(); c['concerns'] = [concern('excluded', ['bank'])]
        a['classification']['component_evidence'] = [{'category': 'excluded', 'text': 'bankruptcy issue', 'atomic_evidence_strength': 1}]
        self.assertFalse(runner.judge_concerns(c, a)[0]['passed'])

    def test_corpus_gap_is_distinct_from_exclusion(self):
        c, a = case(), observation(); c['concerns'] = [concern('labor', ['final pay'], gap=True)]
        a['components'] = [{'domain': 'labor', 'query': 'private employer final pay', 'candidates': []}]
        self.assertTrue(runner.judge_concerns(c, a)[0]['passed'])
        a['components'][0]['candidates'] = [{'provision_id': 'irrelevant'}]
        self.assertFalse(runner.judge_concerns(c, a)[0]['passed'])

    def test_zero_denominator_is_unavailable(self):
        result = rate([], lambda r: 1)
        self.assertIsNone(result['value']); self.assertIsNone(result['family_cluster_bootstrap_95'])

    def test_family_bootstrap_groups_all_variants(self):
        records = [{'family_id': 'a', 'ok': 1}] * 3 + [{'family_id': 'b', 'ok': 0}]
        result = rate(records, lambda r: r['ok'], repeats=1000, seed=1)
        self.assertEqual(result['value'], .75); self.assertEqual(result['families'], 2)
        self.assertEqual(result['family_cluster_bootstrap_95'], [0.0, 1.0])
        self.assertEqual(result, rate(records, lambda r: r['ok'], repeats=1000, seed=1))

    def test_perfect_development_interval_has_boundary_caveat(self):
        r = rate([{'family_id': 'a'}, {'family_id': 'b'}], lambda r: 1)
        self.assertEqual(r['family_cluster_bootstrap_95'], [1.0, 1.0])
        self.assertIn('cannot rule out unseen failures', r['interval_note'])

    def test_classification_counts_abstentions(self):
        a = record()
        b = record(case('B'), observation(primary='consumer', route='clarify'))
        result = head([a, b], 'primary', PRIMARY)
        self.assertEqual(result['count'], 2); self.assertEqual(result['accuracy'], .5)

    def test_calibration_high_confidence_wrong(self):
        r = record(case(), observation(primary='consumer'))
        result = head([r], 'primary', PRIMARY)
        self.assertEqual(result['calibration']['ece'], 1.0)
        self.assertEqual(result['calibration']['multiclass_brier'], 2.0)

    def test_calibration_probability_one_bin_and_empty_bins(self):
        result = head([record()], 'primary', PRIMARY)
        self.assertEqual(result['calibration']['bins'][-1]['count'], 1)
        self.assertIsNone(result['calibration']['bins'][0]['mean_confidence'])
        self.assertEqual(result['calibration']['ece'], 0)

    def test_invalid_probabilities_and_confidence_rejected(self):
        for value in [float('nan'), -1, 2]:
            r = record(); r['actual']['classification']['primary_probabilities']['labor'] = value
            with self.assertRaises(ValueError): head([r], 'primary', PRIMARY)
        r = record(); r['actual']['classification']['primary_confidence'] = .2
        with self.assertRaises(ValueError): head([r], 'primary', PRIMARY)

    def test_always_clarifying_cannot_pass_coverage_screen(self):
        data = [record(case('A'), observation(route='clarify')), record(case('B'), observation(route='clarify'))]
        summary = summarize_group(data, PROTOCOL, intervals=False)
        gate = next(g for g in screening_gates(summary, PROTOCOL) if g['metric'] == 'decisive_coverage')
        self.assertFalse(gate['passed']); self.assertEqual(gate['value'], 0.0)

    def test_csv_cells_preserve_text_without_formula_execution(self):
        for text in ['=SUM(1,2)', ' +HYPERLINK("url")', '-expression', '@name']:
            self.assertEqual(runner.safe_csv(text), "'" + text)
        self.assertEqual(runner.safe_csv('ordinary question'), 'ordinary question')
        self.assertEqual(runner.safe_csv(.8), .8)

    def test_freeze_precedes_inference_and_detects_changed_cases(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            output = Path(folder) / 'run'
            with patch.object(runner, 'execute_question', side_effect=AssertionError('No inference while preparing')):
                runner.prepare(output)
            runner.verify_freeze(output)
            with (output / 'cases.jsonl').open('a', encoding='utf-8') as stream: stream.write('\n')
            with self.assertRaisesRegex(ValueError, 'inputs changed'): runner.verify_freeze(output)

    def test_final_protocol_is_blocked_before_output_creation(self):
        protocol = copy.deepcopy(PROTOCOL); protocol['role'] = 'final'
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            output = Path(folder) / 'final'
            with self.assertRaises(ContractError): runner.prepare(output, protocol)
            self.assertFalse(output.exists())

    def test_repair_reuses_exact_parent_case_bytes(self):
        if not PROTOCOL.get('parent_evaluation'):
            self.skipTest('No repair parent configured')
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            output = Path(folder) / 'repair'
            runner.prepare(output)
            self.assertEqual((output / 'cases.jsonl').read_bytes(),
                             (ROOT / PROTOCOL['parent_evaluation'] / 'cases.jsonl').read_bytes())
            self.assertEqual(read(output / 'case_manifest.json')['new_questions_in_this_revision'], 0)

    def test_repair_rejects_changed_targets(self):
        if not PROTOCOL.get('parent_evaluation'):
            self.skipTest('No repair parent configured')
        protocol = copy.deepcopy(PROTOCOL)
        protocol['screening_targets']['explicit_concern_match_min'] = .5
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            output = Path(folder) / 'repair'
            with self.assertRaisesRegex(ContractError, 'screening targets'):
                runner.prepare(output, protocol)
            self.assertFalse(output.exists())

    def test_repair_rejects_different_case_binding(self):
        if not PROTOCOL.get('parent_evaluation'):
            self.skipTest('No repair parent configured')
        protocol = copy.deepcopy(PROTOCOL); protocol['frozen_cases_sha256'] = '0' * 64
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            output = Path(folder) / 'repair'
            with self.assertRaisesRegex(ContractError, 'case hash'):
                runner.prepare(output, protocol)
            self.assertFalse(output.exists())

    def test_started_runs_cannot_be_reused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            path = Path(folder); save(path / 'execution_started.json', {})
            with self.assertRaisesRegex(ValueError, 'already started'): runner.run(path)

    def test_runtime_receives_question_only(self):
        question = 'A store charged more than the price tag.'
        p = observation()['classification']
        runtime = Mock(); runtime.bundle = object()
        pre = {'routing': {k: p[k] for k in ['predicted_primary', 'predicted_scope', 'routing_action']},
            'components': [], 'excluded_components': [], 'decision': 'insufficient_evidence', 'offline_drafting_allowed': False,
            'answer_generation_allowed': False, 'deployment_allowed': False, 'display_allowed': False}
        runtime.preflight.return_value = pre; runtime.excerpt_draft.return_value = {'claims': []}
        with patch('classifier_runtime.predict_records', return_value=[p]) as predict:
            runner.execute_question(runtime, question)
        self.assertEqual(predict.call_args.args[1], [{'question_text': question}])
        self.assertEqual(runtime.preflight.call_args_list[0].args, (question, 'recorded_excerpt'))

    def test_empty_answer_scoring_is_not_perfect(self):
        result = evaluate_answers([case()], [], [], '1' * 64, as_of='2026-10-17')
        self.assertEqual(result['status'], 'not_measured'); self.assertIsNone(result['unsupported_claim_rate'])

    def test_normal_answer_scoring_rejects_software_fixtures(self):
        c, a, r = answer_and_review()
        with self.assertRaisesRegex(ContractError, 'fixtures are forbidden'):
            evaluate_answers([c], [a], [r], '1' * 64, as_of='2026-10-17')

    def test_answer_score_records_failures_and_keeps_live_flags_off(self):
        c, a, r = answer_and_review(); r['claim_findings'][0]['supported'] = False
        result = evaluate_answers([c], [a], [r], '1' * 64, as_of='2026-10-17', allow_test_reviews=True)
        self.assertEqual(result['unsupported_claim_rate']['value'], 1.0)
        self.assertEqual(result['reviewed_answer_quality_rate']['value'], 0.0)
        self.assertFalse(result['answer_generation_allowed']); self.assertTrue(result['software_fixture_mode'])

    def test_answer_reviews_require_exact_bindings(self):
        for field in ['answer_sha256', 'question_sha256', 'protocol_sha256']:
            c, a, r = answer_and_review(); r[field] = '2' * 64
            with self.assertRaisesRegex(ContractError, 'binding mismatch'):
                evaluate_answers([c], [a], [r], '1' * 64, as_of='2026-10-17', allow_test_reviews=True)

    def test_answer_review_cannot_omit_or_duplicate_claims(self):
        for duplicate in [False, True]:
            c, a, r = answer_and_review()
            r['claim_findings'] = r['claim_findings'] * 2 if duplicate else []
            with self.assertRaises(ContractError):
                evaluate_answers([c], [a], [r], '1' * 64, as_of='2026-10-17', allow_test_reviews=True)

    def test_answer_review_cannot_be_future_dated(self):
        c, a, r = answer_and_review(); r['reviewed_on'] = '2026-10-18'
        with self.assertRaises(ContractError):
            evaluate_answers([c], [a], [r], '1' * 64, as_of='2026-10-17', allow_test_reviews=True)

    def test_changed_answer_question_is_rejected(self):
        c, a, r = answer_and_review(); a['draft']['question_text'] = 'different question'
        with self.assertRaises(ContractError):
            evaluate_answers([c], [a], [r], '1' * 64, as_of='2026-10-17', allow_test_reviews=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
