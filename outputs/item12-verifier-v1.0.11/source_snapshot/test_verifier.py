"""Software assertions against the real pinned classifier, index and source contracts."""
from __future__ import annotations

import copy
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import verification
from contracts import ContractError, DRAFT_SCHEMA, PREFLIGHT_SCHEMA, RESULT_SCHEMA, strict_json, validate
from development_cases import (ARTICLE_83, ARTICLE_81, AS_OF, CLARIFY, EXCLUDED, FINAL_PAY,
                               LABOR, MIXED, PARTIAL, PRICE, excerpt, fixture_verifier, software_reviews)
from evaluate_verifier import evaluate, reasons
from verification import EvidenceVerifier, HERE, ROOT, digest


class VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = EvidenceVerifier(as_of=AS_OF)
        cls.labor = excerpt(cls.v, LABOR, preferred={'labor': ARTICLE_83})
        cls.price = excerpt(cls.v, PRICE, preferred={'consumer': ARTICLE_81})
        cls.store = software_reviews(cls.v, LABOR, cls.labor)

    def test_development_controls_and_adversarial_cases(self):
        _, results, metrics = evaluate(self.v)
        self.assertEqual(metrics['passed'], metrics['total'], [r['case_id'] for r in results if not r['passed']])
        self.assertGreaterEqual(metrics['groups']['valid_excerpt_control']['passed'], 4)
        self.assertGreaterEqual(metrics['groups']['adversarial']['passed'], 40)

    def test_exact_quote_keeps_provisos_and_locators(self):
        result = self.v.verify(PRICE, self.price, 'recorded_excerpt')
        self.assertTrue(result['offline_preview_allowed'])
        self.assertIn('Provided, further', result['preview'][0]['text'])
        citation = result['preview'][0]['citations'][0]
        self.assertEqual(citation['provision_id'], 'RA_7394_1992__art_81')
        self.assertTrue(citation['source_locator'])
        self.assertIn('Exact stored excerpts only', ' '.join(result['disclosures']))
        self.assertFalse(result['legal_support_verified'])

    def test_default_current_guidance_never_treats_recent_dates_as_approval(self):
        pre = self.v.preflight(LABOR)
        self.assertFalse(pre['offline_drafting_allowed'])
        self.assertTrue(all('scoped_currentness_review_missing' in g['reasons'] for c in pre['components'] for g in c['evidence_gates']))

    def test_software_review_gates_are_operable_but_explicitly_simulated(self):
        runtime = fixture_verifier(self.v, self.store)
        result = runtime.verify(LABOR, self.labor)
        self.assertEqual(result['decision'], 'reviewed_answer_candidate')
        self.assertTrue(result['software_fixture_mode'])
        self.assertTrue(result['legal_support_review_recorded'])
        self.assertFalse(result['legal_support_verified'])
        self.assertIn('simulated test data', ' '.join(result['disclosures']))

    def test_normal_runtime_refuses_software_reviews(self):
        clone = copy.copy(self.v)
        with self.assertRaisesRegex(ContractError, 'forbidden'):
            clone._load_reviews(self.store)

    def test_false_approval_findings_are_rejected_by_contract(self):
        changed = copy.deepcopy(self.store)
        changed['claim_reviews'][0]['qualifications_preserved'] = False
        with self.assertRaises(ContractError):
            fixture_verifier(self.v, changed)

    def test_duplicate_review_ids_are_rejected(self):
        changed = copy.deepcopy(self.store)
        changed['claim_reviews'][0]['review_id'] = changed['source_reviews'][0]['review_id']
        with self.assertRaisesRegex(ContractError, 'Duplicate review_id'):
            fixture_verifier(self.v, changed)

    def test_reviews_cannot_be_unscoped(self):
        changed = copy.deepcopy(self.store)
        del changed['source_reviews'][0]['component_sha256']
        with self.assertRaises(ContractError):
            fixture_verifier(self.v, changed)

    def test_invalid_review_dates_are_rejected(self):
        changed = copy.deepcopy(self.store)
        changed['source_reviews'][0]['reviewed_on'] = '2026-02-30'
        with self.assertRaises(ValueError):
            fixture_verifier(self.v, changed)

    def test_no_review_file_was_fabricated(self):
        self.assertEqual(strict_json(HERE / 'trusted_reviews.json'), {'schema_version': '1.0', 'source_reviews': [], 'claim_reviews': []})

    def test_known_missing_modifier_blocks_current_guidance(self):
        record = next(r for r in self.v.records.values() if r['document_id'] == 'PD_851_1975')
        component = {'query': 'thirteenth month coverage', 'allowed_domain': 'labor'}
        gate = self.v.source_gate('Thirteenth month coverage', component, record, 'current_guidance')
        self.assertIn('related_authority_unavailable:MO_28_1986', gate['reasons'])
        self.assertFalse(gate['passed'])

    def test_related_authority_policy_requires_implementing_rules(self):
        for doc, dependency in [('RA_10909_2016', 'DTI_DAO_16_03'), ('RA_10396_2013', 'DOLE_DO_249_25'),
                                ('RA_11967_2023', 'DTI_JAO_24_03')]:
            record = next(r for r in self.v.records.values() if r['document_id'] == doc)
            self.assertIn(dependency, self.v.required_related(record))

    def test_termination_irr_requires_later_order(self):
        records = [r for r in self.v.records.values() if r['document_id'] == 'LAB_IRR_1989' and
                   r['source_hierarchy']['book'] == 'BOOK SIX Post Employment']
        self.assertTrue(records)
        self.assertTrue(all('DOLE_DO_147_15' in self.v.required_related(r) for r in records))

    def test_forged_candidate_metadata_is_detected(self):
        hit = self.v.preflight(PRICE, 'recorded_excerpt')['components'][0]['candidates'][0]
        for field, value in [('citation_display', 'Fabricated law'), ('source_locator', {}), ('official_source_url', 'https://example.invalid'),
                             ('status_as_of', '2099-01-01'), ('parent_text', 'forged text'), ('provision_id', 'wrong'),
                             ('normalized_char_start', False)]:
            with self.subTest(field=field):
                changed = copy.deepcopy(hit)
                changed[field] = value
                self.assertIn('candidate_metadata_mismatch:' + field, self.v.check_candidate(changed, 'consumer'))

    def test_candidate_domain_and_eligibility_are_rechecked(self):
        hit = self.v.preflight(PRICE, 'recorded_excerpt')['components'][0]['candidates'][0]
        self.assertIn('candidate_domain_mismatch', self.v.check_candidate(hit, 'labor'))
        ineligible = next(c for c in self.v.source['chunks'] if c['chunk_id'] not in self.v.records)
        self.assertEqual(self.v.check_candidate(ineligible, 'labor'), ['unknown_or_ineligible_chunk'])

    def test_ranking_score_is_not_a_permission_signal(self):
        hit = self.v.preflight(PRICE, 'recorded_excerpt')['components'][0]['candidates'][0]
        hit.update(score=1e300, semantic_similarity=1.0, answer_generation_allowed=True)
        self.assertEqual(self.v.check_candidate(hit, 'consumer'), [])
        gate = self.v.source_gate(PRICE, {'query': PRICE, 'allowed_domain': 'consumer'}, hit, 'current_guidance')
        self.assertFalse(gate['passed'])

    def test_future_recorded_source_date_is_blocked(self):
        clone = copy.copy(self.v)
        clone.as_of = verification.iso_date('2026-09-28')
        hit = self.v.preflight(PRICE, 'recorded_excerpt')['components'][0]['candidates'][0]
        self.assertIn('source_status_date_in_future', clone.check_candidate(hit, 'consumer'))

    def test_real_classifier_routes_are_preserved(self):
        for question, decision in [(CLARIFY, 'clarify'), (EXCLUDED, 'refer_out_of_scope')]:
            pre = self.v.preflight(question)
            self.assertEqual(pre['decision'], decision)
            self.assertEqual(pre['components'], [])
        self.assertEqual(self.v.preflight(FINAL_PAY)['components'][0]['candidates'], [])

    def test_supported_and_excluded_concerns_stay_separate(self):
        pre = self.v.preflight(PARTIAL, 'recorded_excerpt')
        self.assertEqual(len(pre['components']), 1)
        self.assertNotIn('seafarer', pre['components'][0]['query'])
        self.assertTrue(pre['excluded_components'])
        self.assertNotIn('phone', json.dumps(pre))

    def test_one_failed_claim_withholds_its_whole_component(self):
        d = excerpt(self.v, MIXED)
        extra = copy.deepcopy(d['claims'][0])
        extra.update(claim_id='bad_additional_claim', text='Unfounded conclusion')
        d['claims'].append(extra)
        result = self.v.verify(MIXED, d, 'recorded_excerpt')
        self.assertEqual(result['coverage']['components_with_preview'], 1)
        self.assertEqual({c['component_id'] for c in result['preview']}, {'concern_002'})

    def test_output_contracts_and_confidence_separation(self):
        pre = self.v.preflight(PRICE, 'recorded_excerpt')
        result = self.v.verify(PRICE, self.price, 'recorded_excerpt')
        validate(pre, PREFLIGHT_SCHEMA)
        validate(result, RESULT_SCHEMA)
        self.assertIn('primary_confidence', result['routing'])
        self.assertIn('no legal-correctness probability', result['confidence_meaning'])
        self.assertNotIn('answer_confidence', result)

    def test_all_outputs_keep_live_flags_off(self):
        for question in [LABOR, PRICE, MIXED, PARTIAL, CLARIFY, EXCLUDED, FINAL_PAY]:
            for mode in ['current_guidance', 'recorded_excerpt']:
                pre = self.v.preflight(question, mode)
                self.assertFalse(any(pre[k] for k in ['deployment_allowed', 'answer_generation_allowed', 'display_allowed']))

    def test_invalid_input_types_fail_closed(self):
        for question in ['', ' ', None, False, [], 'x' * 10001]:
            with self.assertRaises(ContractError):
                self.v.preflight(question)
        with self.assertRaises(ContractError):
            self.v.preflight(PRICE, 'unknown')
        for draft in [None, [], False, {'claims': []}]:
            self.assertEqual(self.v.verify(PRICE, draft)['decision'], 'draft_rejected')

    def test_duplicate_keys_and_nonfinite_json_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
            path = Path(directory) / 'bad.json'
            for payload in ['{"claims": [], "claims": []}', '{"number": NaN}', '{"number": Infinity}',
                            '{"number":1e1000}', '{"number":-1e1000}']:
                path.write_text(payload)
                with self.assertRaises(ContractError):
                    strict_json(path)

    def test_finite_json_numbers_remain_valid(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
            path = Path(directory) / 'finite.json'
            path.write_text('{"number":1e2}', encoding='utf-8')
            self.assertEqual(strict_json(path), {'number': 100.0})

    def test_source_helper_rejects_unknown_modes_and_sources(self):
        comp = self.v.preflight(PRICE, 'recorded_excerpt')['components'][0]
        with self.assertRaisesRegex(ContractError, 'Unknown verification mode'):
            self.v.source_gate(PRICE, comp, comp['candidates'][0], 'misspelled_mode')
        with self.assertRaisesRegex(ContractError, 'Unknown or ineligible'):
            self.v.source_gate(PRICE, comp, {'chunk_id': 'FAKE'}, 'current_guidance')

    def test_default_date_updates_and_expired_reviews_stop_passing(self):
        clone = fixture_verifier(self.v, self.store)
        clone._fixed_as_of = None  # Same clock behavior as a default constructor.
        with patch.object(verification, 'date') as clock:
            clock.fromisoformat.side_effect = date.fromisoformat
            clock.today.return_value = date(2026, 10, 17)
            self.assertTrue(clone.verify(LABOR, self.labor)['offline_preview_allowed'])
            clock.today.return_value = date(2026, 10, 25)
            result = clone.verify(LABOR, self.labor)
        self.assertEqual(result['as_of'], '2026-10-25')
        self.assertFalse(result['offline_preview_allowed'])
        self.assertIn('review_expired_or_invalid_interval', reasons(result))

    def test_explicit_historical_date_remains_reproducible(self):
        clone = fixture_verifier(self.v, self.store)
        with patch.object(verification, 'date') as clock:
            clock.fromisoformat.side_effect = date.fromisoformat
            clock.today.return_value = date(2026, 10, 25)
            result = clone.verify(LABOR, self.labor)
            clock.today.assert_not_called()
        self.assertEqual(result['as_of'], AS_OF)
        self.assertTrue(result['offline_preview_allowed'])

    def test_changed_file_is_detected_even_with_preserved_timestamp(self):
        clone = copy.copy(self.v)
        clone.integrity_files = dict(self.v.integrity_files)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
            path = Path(directory) / 'artifact.json'
            path.write_text('before', encoding='utf-8')
            original_stat = path.stat()
            clone.integrity_files[path] = verification.sha(path)
            self.assertTrue(clone.preflight(PRICE, 'recorded_excerpt')['offline_drafting_allowed'])
            path.write_text('after!', encoding='utf-8')
            os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
            with self.assertRaisesRegex(ValueError, 'Artifact changed since'):
                clone.preflight(PRICE, 'recorded_excerpt')

    def test_deleted_file_stops_subsequent_requests(self):
        clone = copy.copy(self.v)
        clone.integrity_files = dict(self.v.integrity_files)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
            path = Path(directory) / 'artifact.json'
            path.write_text('content', encoding='utf-8')
            clone.integrity_files[path] = verification.sha(path)
            path.unlink()
            with self.assertRaisesRegex(ValueError, 'Artifact changed since'):
                clone.preflight(PRICE, 'recorded_excerpt')

    def test_request_rechecks_source_index_runtime_and_model_hashes(self):
        targets = [ROOT / 'dataset/canonical_sources/manifests/legal_status_review.csv',
                   ROOT / self.v.policy['retrieval'] / 'records.jsonl',
                   ROOT / self.v.policy['classifier'] / 'classifier.joblib',
                   ROOT / 'dataset/pipelines/item11/retrieval.py', HERE / 'policy.json']
        original_sha = verification.sha
        for target in targets:
            self.assertIn(target, self.v.integrity_files)
            with self.subTest(target=target.name), patch.object(verification, 'sha', side_effect=lambda p: '0' * 64 if p == target else original_sha(p)):
                with self.assertRaisesRegex(ValueError, 'Artifact changed since'):
                    self.v.preflight(PRICE, 'recorded_excerpt')

    def test_mutated_review_store_stops_subsequent_requests(self):
        clone = copy.copy(self.v)
        clone.reviews = copy.deepcopy(self.v.reviews)
        clone.reviews['source_reviews'].append({'approved': True})
        with self.assertRaisesRegex(ValueError, 'Review store changed since'):
            clone.preflight(PRICE, 'recorded_excerpt')

    def test_claim_review_expiration_is_checked_separately(self):
        changed = copy.deepcopy(self.store)
        changed['claim_reviews'][0]['valid_through'] = '2026-10-16'
        result = fixture_verifier(self.v, changed).verify(LABOR, self.labor)
        self.assertFalse(result['offline_preview_allowed'])
        self.assertIn('review_expired_or_invalid_interval', reasons(result))
        self.assertIn('claim_support_and_coverage_review_missing', reasons(result))

    def test_bm25_verification_works_with_network_and_semantics_disabled(self):
        with patch.object(socket, 'create_connection', side_effect=AssertionError('Network access forbidden')), \
             patch.object(self.v.retriever, 'semantic_scores', side_effect=AssertionError('Semantic inference forbidden')):
            result = self.v.verify(PRICE, self.price, 'recorded_excerpt')
        self.assertTrue(result['offline_preview_allowed'])

    def test_classifier_checksum_failure_precedes_deserialization(self):
        original_sha = verification.sha
        def altered(path):
            return '0' * 64 if Path(path).name == 'classifier.joblib' else original_sha(path)
        with patch.object(verification, 'sha', side_effect=altered), patch.object(verification.joblib, 'load') as load:
            with self.assertRaisesRegex(ValueError, 'Classifier artifact changed'):
                EvidenceVerifier(as_of=AS_OF)
            load.assert_not_called()

    def test_retrieval_source_hash_failure_stops_constructor(self):
        import retrieval
        original_sha = retrieval.sha
        def altered(path):
            return '0' * 64 if Path(path).name == 'legal_status_review.csv' else original_sha(path)
        with patch.object(retrieval, 'sha', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'Source changed'):
                EvidenceVerifier(as_of=AS_OF)

    def test_cli_runs_outside_repository_and_rejects_fixture_reviews(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
            path = Path(directory) / 'reviews.json'
            path.write_text(json.dumps(self.store), encoding='utf-8')
            command = [sys.executable, str(HERE / 'verification.py'), '--query', PRICE]
            run = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['decision'], 'insufficient_evidence')
            rejected = subprocess.run(command + ['--review-store', str(path)], cwd=directory, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(rejected.returncode, 2)
            self.assertIn('Software fixtures are forbidden', rejected.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
