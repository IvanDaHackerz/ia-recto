"""Offline evidence gates and structured claim checking. No LLM or network calls.

All decisions are development candidates. Recorded excerpts prove provenance,
not relevance or current law. Current guidance additionally needs bounded,
operator-managed legal reviews; a draft cannot approve itself.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'dataset/pipelines/item11'))
sys.path.insert(0, str(ROOT / 'dataset/pipelines/item10'))
import joblib
from common import curate, eligibility, sha, sources
from retrieval import LegalRetriever
from contracts import ContractError, DRAFT_SCHEMA, REVIEW_STORE_SCHEMA, strict_json, validate


def digest(value):
    """Hash a JSON value, including exact Unicode text and evidence offsets."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def iso_date(value):
    result = date.fromisoformat(value)
    if result.isoformat() != value:
        raise ValueError('Use YYYY-MM-DD')
    return result


class EvidenceVerifier:
    def __init__(self, *, review_store=None, as_of=None, allow_test_reviews=False):
        self.policy = strict_json(HERE / 'policy.json')
        self.policy_hash = digest(self.policy)
        self._fixed_as_of = iso_date(as_of) if as_of is not None else None
        self.as_of = self._fixed_as_of or date.today()
        self.fixture_mode = allow_test_reviews is True
        self.retriever = LegalRetriever(ROOT / self.policy['retrieval'])
        self.source = sources()
        records, _ = curate(self.source)
        if records != self.retriever.records:
            raise ValueError('Index is not the current curated source view')
        self.records = {r['chunk_id']: r for r in records}
        self.chunks = {r['chunk_id']: r for r in self.source['chunks']}
        classifier = ROOT / self.policy['classifier']
        self.parent_checksums = strict_json(classifier / 'artifact_checksums.json')
        for name, expected in self.parent_checksums.items():
            if sha(classifier / name) != expected:
                raise ValueError('Classifier artifact changed: ' + name)
        for name in ['classifier_runtime.py', 'clause_classifier.py', 'logical_clause_model.py',
                     'scope_constraints.py', 'typing_repair.py', 'typing_vocabulary.py', 'referral_routing.py', 'semantic_encoder.py']:
            if sha(ROOT / 'dataset/pipelines/item10' / name) != self.parent_checksums[name]:
                raise ValueError('Classifier runtime changed: ' + name)
        # joblib is executable serialization: only load this pinned, verified project artifact.
        self.bundle = joblib.load(classifier / 'classifier.joblib')
        store = strict_json(HERE / 'trusted_reviews.json') if review_store is None else review_store
        self._load_reviews(store)
        # Check these bindings on every public request as well as construction.
        # A long-lived offline evaluator must stop after any source/runtime change.
        index_dir = ROOT / self.policy['retrieval']
        self.integrity_files = {
            ROOT / name: value for name, value in {
                **self.source['source_sha256'], **self.source['raw_source_sha256']}.items()}
        self.integrity_files.update({classifier / name: value for name, value in self.parent_checksums.items()})
        self.integrity_files.update({index_dir / name: value for name, value in
                                     strict_json(index_dir / 'index_checksums.json').items()})
        extra = [index_dir / name for name in ['index_manifest.json', 'index_checksums.json']]
        extra += [classifier / 'artifact_checksums.json', ROOT / 'models/embedding_backbone_manifest.json']
        extra += [ROOT / 'dataset/pipelines/item11' / name for name in self.retriever.manifest['runtime_source_sha256']]
        extra += [ROOT / 'dataset/pipelines/item10' / name for name in
                  ['classifier_runtime.py', 'clause_classifier.py', 'logical_clause_model.py',
                   'scope_constraints.py', 'typing_repair.py', 'typing_vocabulary.py', 'referral_routing.py', 'semantic_encoder.py']]
        extra += [HERE / name for name in ['verification.py', 'contracts.py', 'policy.json']]
        if review_store is None:
            extra.append(HERE / 'trusted_reviews.json')
        self.integrity_files.update({path: sha(path) for path in extra})
        self._review_snapshot_sha256 = digest(self.reviews)

    def _begin_request(self):
        self.as_of = self._fixed_as_of or date.today()
        for path, expected in self.integrity_files.items():
            if not path.is_file() or sha(path) != expected:
                raise ValueError('Artifact changed since verifier construction; reload/rebuild: ' + path.as_posix())
        if digest(self.reviews) != self._review_snapshot_sha256:
            raise ValueError('Review store changed since verifier construction; reload it explicitly')

    def _load_reviews(self, store):
        store = copy.deepcopy(store)
        validate(store, REVIEW_STORE_SCHEMA)
        all_reviews = store['source_reviews'] + store['claim_reviews']
        if len({r['review_id'] for r in all_reviews}) != len(all_reviews):
            raise ContractError('Duplicate review_id')
        if not self.fixture_mode and any(r['review_kind'] == 'software_fixture' for r in all_reviews):
            raise ContractError('Software fixtures are forbidden in the normal runtime')
        for r in all_reviews:
            iso_date(r['reviewed_on'])
            iso_date(r['valid_through'])
        self.reviews = store

    def _base(self, question, mode):
        return {'schema_version': '1.0', 'verifier_version': self.policy['version'],
                'question_text': question, 'question_sha256': digest(question),
                'mode': mode, 'as_of': self.as_of.isoformat(),
                'classifier_version': Path(self.policy['classifier']).name,
                'index_version': self.retriever.manifest['index_version'],
                'policy_sha256': self.policy_hash, 'review_store_sha256': digest(self.reviews),
                'software_fixture_mode': self.fixture_mode,
                'answer_generation_allowed': False, 'deployment_allowed': False,
                'display_allowed': False,
                'confidence_meaning': 'Classifier label probabilities and retrieval ranking only; no legal-correctness probability.'}

    def required_related(self, record):
        required = set(self.policy['required_related_documents'].get(record['document_id'], []))
        if record['document_id'] == 'LAB_IRR_1989' and re.search(
                r'\b(?:termination|book\s+(?:vi|6|six))\b',
                json.dumps(record['source_hierarchy']) + ' ' + (record['heading'] or ''), re.I):
            required.add('DOLE_DO_147_15')
        return sorted(required)

    def conditions_hash(self, record):
        return digest({k: record[k] for k in ['freshness_rule', 'conditions', 'legal_relationships',
                                             'status_as_of', 'retrieval_use_policy', 'legal_status']})

    def related_hash(self, record):
        return digest({doc: self.source['raw_source_sha256'][self.source['documents'][doc]['raw_local_path']]
                       for doc in self.required_related(record)})

    def review_binding(self, question, component):
        return {'question_sha256': digest(question),
                'component_sha256': digest({'query': component['query'], 'allowed_domain': component['allowed_domain']}),
                'index_version': self.retriever.manifest['index_version'], 'policy_sha256': self.policy_hash}

    def _review_problems(self, review):
        start, end = iso_date(review['reviewed_on']), iso_date(review['valid_through'])
        reasons = []
        if start > self.as_of:
            reasons.append('review_date_in_future')
        if end < start or self.as_of > end:
            reasons.append('review_expired_or_invalid_interval')
        if (end - start).days > self.policy['maximum_review_days']:
            reasons.append('review_interval_exceeds_policy')
        return reasons

    def check_candidate(self, hit, allowed_domain):
        """Reconcile every canonical field on a retrieved hit, ignoring ranking values.

        This diagnostic API does not grant permission. Normal preflight recomputes
        retrieval rather than accepting caller-supplied hits or routing decisions.
        """
        if type(hit) is not dict or hit.get('chunk_id') not in self.records:
            return ['unknown_or_ineligible_chunk']
        r = self.records[hit['chunk_id']]
        problems = []
        fields = ['chunk_id', 'provision_id', 'document_id', 'citation_display', 'heading', 'display_text',
                  'normalized_char_start', 'normalized_char_end', 'source_locator', 'former_locator_labels',
                  'parent_provision_id', 'parent_text', 'document_title', 'official_source_url', 'retrieval_url',
                  'raw_local_path', 'domains', 'supported_topics', 'legal_status', 'status_family',
                  'status_as_of', 'freshness_rule', 'conditions', 'legal_relationships', 'quality_flags',
                  'review_status', 'extraction_method']
        problems.extend('candidate_metadata_mismatch:' + key for key in fields if key not in hit or digest(hit[key]) != digest(r[key]))
        if allowed_domain not in r['domains']:
            problems.append('candidate_domain_mismatch')
        c = self.chunks[r['chunk_id']]
        p = self.source['provisions'][r['provision_id']]
        d = self.source['documents'][r['document_id']]
        problems.extend(eligibility(c, p, d, self.source))
        a, b = r['normalized_char_start'], r['normalized_char_end']
        if r['parent_text'][a:b] != r['display_text']:
            problems.append('stored_chunk_offset_mismatch')
        if iso_date(r['status_as_of']) > self.as_of:
            problems.append('source_status_date_in_future')
        return problems

    def source_gate(self, question, component, hit, mode):
        if mode not in {'current_guidance', 'recorded_excerpt'}:
            raise ContractError('Unknown verification mode')
        if type(hit) is not dict or hit.get('chunk_id') not in self.records:
            raise ContractError('Unknown or ineligible source candidate')
        r = self.records[hit['chunk_id']]
        problems = self.check_candidate(hit, component['allowed_domain'])
        required = self.required_related(r)
        eligible_docs = {v['document_id'] for v in self.records.values()}
        unavailable = sorted(set(required) - eligible_docs)
        # Recorded-source inspection may show an exact excerpt while disclosing
        # unresolved dependencies. It never presents a verified legal answer.
        if mode == 'current_guidance':
            problems.extend('related_authority_unavailable:' + doc for doc in unavailable)
            match = {**self.review_binding(question, component), 'document_id': r['document_id'],
                     'raw_source_sha256': self.source['raw_source_sha256'][r['raw_local_path']],
                     'conditions_sha256': self.conditions_hash(r), 'related_sources_sha256': self.related_hash(r)}
            reviews = [v for v in self.reviews['source_reviews'] if all(v[k] == val for k, val in match.items())]
            valid = [v for v in reviews if not self._review_problems(v)]
            if not valid:
                problems.append('scoped_currentness_review_missing')
                for v in reviews:
                    problems.extend(self._review_problems(v))
            review_ids = [v['review_id'] for v in valid]
        else:
            review_ids = []
        return {'chunk_id': r['chunk_id'], 'passed': not problems, 'reasons': sorted(set(problems)),
                'source_review_ids': review_ids, 'required_related_documents': required,
                'unavailable_related_documents': unavailable,
                'status_as_of': r['status_as_of'], 'freshness_rule': r['freshness_rule'],
                'currentness_reviewed': mode == 'current_guidance' and bool(review_ids) and not problems,
                'recorded_excerpt_only': mode == 'recorded_excerpt'}

    def preflight(self, question, mode='current_guidance'):
        if type(question) is not str or not question.strip() or len(question) > 10000:
            raise ContractError('Question must be non-empty text of at most 10000 characters')
        if mode not in {'current_guidance', 'recorded_excerpt'}:
            raise ContractError('Unknown verification mode')
        self._begin_request()
        result = self._base(question, mode)
        pipeline = self.retriever.retrieve_question(question, self.bundle,
                                                    method=self.policy['retrieval_method'], top_k=self.policy['top_k'])
        p = pipeline['classification']
        result['routing'] = {k: p.get(k) for k in ['routing_action', 'reason', 'clarification_question',
                            'predicted_primary', 'predicted_scope', 'primary_confidence', 'scope_confidence']}
        result['excluded_components'] = copy.deepcopy(p.get('excluded_components', []))
        # Only directory identifiers are passed through. No old/unverified contacts.
        result['referral_ids'] = p.get('referral_ids', [])
        result['components'] = []
        for i, response in enumerate(pipeline['components'], 1):
            component = {'component_id': f'concern_{i:03d}', 'query': response['query'],
                         'allowed_domain': response['allowed_domain'], 'retrieval_status': response['status'],
                         'retrieval_reason': response['reason'], 'candidates': copy.deepcopy(response['hits'])}
            component['evidence_gates'] = [self.source_gate(question, component, h, mode) for h in response['hits']]
            component['evidence_ready'] = any(g['passed'] for g in component['evidence_gates'])
            result['components'].append(component)
        ready = sum(c['evidence_ready'] for c in result['components'])
        result['offline_drafting_allowed'] = ready > 0
        result['all_supported_components_evidence_ready'] = bool(result['components']) and ready == len(result['components'])
        if p['routing_action'] == 'clarify':
            result['decision'] = 'clarify'
        elif p['routing_action'] == 'refer_out_of_scope':
            result['decision'] = 'refer_out_of_scope'
        else:
            result['decision'] = 'evidence_ready' if ready else 'insufficient_evidence'
        return result

    def _claim(self, question, component, claim, mode):
        problems = []
        allowed = {h['chunk_id']: h for h in component['candidates']}
        gates = {g['chunk_id']: g for g in component['evidence_gates']}
        citations = []
        checks = {'citation_identity': True, 'quote_match': True, 'source_gate': True,
                  'full_context': True, 'claim_support': False}
        seen = set()
        for evidence in claim['evidence']:
            cid = evidence['chunk_id']
            if cid in seen:
                problems.append('duplicate_evidence')
            seen.add(cid)
            r = self.records.get(cid)
            if r is None:
                problems.append('unknown_or_ineligible_citation')
                checks['citation_identity'] = False
                checks['quote_match'] = False
                checks['source_gate'] = False
                checks['full_context'] = False
                continue
            if cid not in allowed:
                problems.append('citation_not_retrieved_for_component')
                checks['citation_identity'] = False
            if evidence['provision_id'] != r['provision_id'] or evidence['document_id'] != r['document_id']:
                problems.append('citation_identity_mismatch')
                checks['citation_identity'] = False
            start, end = evidence['start'], evidence['end']
            if not 0 <= start < end <= len(r['parent_text']) or r['parent_text'][start:end] != evidence['quote']:
                problems.append('quote_or_offset_mismatch')
                checks['quote_match'] = False
            # Keep the entire provision, including exceptions, definitions and provisos.
            # Reviewed paraphrases can summarize it; neither kind may hide evidence context.
            if start != 0 or end != len(r['parent_text']):
                problems.append('incomplete_source_context')
                checks['full_context'] = False
            gate = gates.get(cid)
            if gate is None or not gate['passed']:
                problems.extend(gate['reasons'] if gate else ['source_not_in_component'])
                checks['source_gate'] = False
            citations.append({k: copy.deepcopy(r[k]) for k in ['chunk_id', 'provision_id', 'document_id',
                'citation_display', 'document_title', 'source_locator', 'official_source_url',
                'former_locator_labels', 'status_as_of', 'freshness_rule', 'legal_relationships']})
        if claim['kind'] == 'source_excerpt':
            if len(claim['evidence']) != 1 or claim['text'] != claim['evidence'][0]['quote']:
                problems.append('excerpt_text_mismatch')
            elif checks['quote_match'] and checks['full_context']:
                checks['claim_support'] = True  # Identity only, not legal entailment.
        if mode == 'recorded_excerpt' and claim['kind'] != 'source_excerpt':
            problems.append('paraphrase_not_allowed_in_excerpt_mode')
        review_ids = []
        if mode == 'current_guidance':
            match = {**self.review_binding(question, component),
                     'claim_sha256': digest({'kind': claim['kind'], 'text': claim['text']}),
                     'evidence_sha256': digest(claim['evidence'])}
            reviews = [v for v in self.reviews['claim_reviews'] if all(v[k] == val for k, val in match.items())]
            valid = [v for v in reviews if not self._review_problems(v)]
            if not valid:
                problems.append('claim_support_and_coverage_review_missing')
                for v in reviews:
                    problems.extend(self._review_problems(v))
            else:
                review_ids = [v['review_id'] for v in valid]
                checks['claim_support'] = True
        elif claim['kind'] == 'paraphrase':
            checks['claim_support'] = False
        problems = sorted(set(problems))
        return {'claim_id': claim['claim_id'], 'component_id': claim['component_id'],
                'passed': not problems, 'reasons': problems, 'checks': checks,
                'review_ids': review_ids, 'citations': citations,
                'support_meaning': 'Exact recorded text only' if mode == 'recorded_excerpt' else 'Scoped trusted review; not a calibrated model confidence'}

    def verify(self, question, draft, mode='current_guidance'):
        # Never use routing, claims of approval or confidence supplied by a draft.
        pre = self.preflight(question, mode)
        result = self._base(question, mode)
        result.update(routing=pre['routing'], excluded_components=pre['excluded_components'],
                      referral_ids=pre['referral_ids'], claim_results=[], components=[],
                      offline_preview_allowed=False, preview=[], legal_support_verified=False,
                      legal_support_review_recorded=False)
        try:
            validate(draft, DRAFT_SCHEMA)
            if draft['question_text'] != question:
                raise ContractError('Draft question differs from the original question')
            ids = [c['claim_id'] for c in draft['claims']]
            if len(ids) != len(set(ids)):
                raise ContractError('Duplicate claim_id')
        except (ContractError, TypeError, ValueError) as error:
            result.update(decision='draft_rejected', contract_errors=[str(error)],
                          coverage={'supported_components': len(pre['components']), 'components_with_preview': 0,
                                    'meaning': 'No legal coverage established'})
            return result
        if pre['decision'] in {'clarify', 'refer_out_of_scope'}:
            result['decision'] = pre['decision']
            result['coverage'] = {'supported_components': 0, 'components_with_preview': 0, 'meaning': 'No legal coverage established'}
            return result
        components = {c['component_id']: c for c in pre['components']}
        unknown = [c for c in draft['claims'] if c['component_id'] not in components]
        if unknown:
            # An excluded/unknown concern is a global contract/routing violation.
            result.update(decision='draft_rejected', contract_errors=['unknown_or_excluded_component'],
                          coverage={'supported_components': len(components), 'components_with_preview': 0,
                                    'meaning': 'No legal coverage established'})
            return result
        for claim in draft['claims']:
            result['claim_results'].append(self._claim(question, components[claim['component_id']], claim, mode))
        for cid, component in components.items():
            checked = [c for c in result['claim_results'] if c['component_id'] == cid]
            passed = bool(checked) and all(c['passed'] for c in checked)
            reasons = sorted({r for c in checked for r in c['reasons']})
            if not checked:
                reasons.append('missing_component_claims')
            if not component['candidates']:
                reasons.append('no_eligible_retrieval_evidence')
            result['components'].append({'component_id': cid, 'query': component['query'],
                'allowed_domain': component['allowed_domain'], 'passed': passed, 'reasons': reasons,
                'withheld_as_unit': not passed})
            if passed:
                for claim in [c for c in draft['claims'] if c['component_id'] == cid]:
                    checked_claim = next(c for c in checked if c['claim_id'] == claim['claim_id'])
                    result['preview'].append({'component_id': cid, 'claim_id': claim['claim_id'], 'kind': claim['kind'],
                        'text': claim['text'], 'citations': checked_claim['citations']})
        accepted = sum(c['passed'] for c in result['components'])
        result['coverage'] = {'supported_components': len(components), 'components_with_preview': accepted,
            'excluded_components': len(pre['excluded_components']),
            'meaning': 'Provenance coverage only; relevance and legal sufficiency unverified' if mode == 'recorded_excerpt'
                       else 'Concern coverage explicitly recorded in scoped trusted reviews'}
        result['offline_preview_allowed'] = accepted > 0
        if accepted == 0:
            result['decision'] = 'insufficient_evidence'
        elif accepted < len(components) or pre['excluded_components']:
            result['decision'] = 'partial_candidate'
        else:
            result['decision'] = 'recorded_excerpt_candidate' if mode == 'recorded_excerpt' else 'reviewed_answer_candidate'
        result['legal_support_review_recorded'] = mode == 'current_guidance' and accepted > 0
        result['legal_support_verified'] = result['legal_support_review_recorded'] and not self.fixture_mode
        result['disclosures'] = [
            'Offline development preview. Live answer generation, user display and deployment remain disabled.',
            'Recorded status dates are not proof that the law is current today.',
        ]
        if mode == 'recorded_excerpt':
            result['disclosures'].append('Exact stored excerpts only. Relevance, present applicability and completeness of an answer have not been verified.')
        if pre['excluded_components'] or accepted < len(components):
            result['disclosures'].append('Some concerns are withheld. No conclusion is provided for those concerns.')
        if self.fixture_mode:
            result['disclosures'].append('Software fixture reviews are simulated test data, not human or legal-professional approvals.')
        return result

    def excerpt_draft(self, question, preflight):
        """Prepare diagnostic full-provision quotations, not substantive legal answers."""
        if preflight['question_text'] != question or preflight['mode'] != 'recorded_excerpt':
            raise ContractError('Excerpt templates require matching recorded-excerpt preflight')
        claims = []
        for component in preflight['components']:
            ready = {g['chunk_id'] for g in component['evidence_gates'] if g['passed']}
            hit = next((h for h in component['candidates'] if h['chunk_id'] in ready), None)
            if hit is None:
                continue
            claims.append({'claim_id': 'excerpt_' + component['component_id'], 'component_id': component['component_id'],
                'kind': 'source_excerpt', 'text': hit['parent_text'], 'evidence': [{
                    'chunk_id': hit['chunk_id'], 'provision_id': hit['provision_id'], 'document_id': hit['document_id'],
                    'start': 0, 'end': len(hit['parent_text']), 'quote': hit['parent_text']}]})
        return {'schema_version': '1.0', 'question_text': question, 'claims': claims}


def main():
    # Windows console defaults can corrupt quotation/citation punctuation when
    # redirected. The CLI contract is UTF-8 on every platform.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', required=True)
    parser.add_argument('--mode', choices=['current_guidance', 'recorded_excerpt'], default='current_guidance')
    parser.add_argument('--draft', type=Path, help='Untrusted structured draft JSON')
    parser.add_argument('--excerpt-template', action='store_true', help='Offline exact-quote preview only')
    parser.add_argument('--review-store', type=Path, help='Operator-managed legal review file, never an LLM input')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        verifier = EvidenceVerifier(review_store=strict_json(args.review_store) if args.review_store else None)
        if args.excerpt_template and (args.mode != 'recorded_excerpt' or args.draft):
            parser.error('--excerpt-template requires --mode recorded_excerpt and no --draft')
        if args.excerpt_template:
            pre = verifier.preflight(args.query, args.mode)
            draft = verifier.excerpt_draft(args.query, pre)
            result = {'draft': draft, 'verification': verifier.verify(args.query, draft, args.mode) if draft['claims'] else pre}
        elif args.draft:
            result = verifier.verify(args.query, strict_json(args.draft), args.mode)
        else:
            result = verifier.preflight(args.query, args.mode)
        encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output:
            # CLI results are reviewable artifacts; never overwrite an earlier run.
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(encoded)
        else:
            print(encoded, end='')
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'decision': 'integrity_or_contract_error', 'error': str(error),
                          'answer_generation_allowed': False, 'deployment_allowed': False, 'display_allowed': False}), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
