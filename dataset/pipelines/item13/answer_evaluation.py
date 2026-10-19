"""Score externally supplied drafts/reviews offline; never generate or self-approve answers."""
from __future__ import annotations
import argparse
from datetime import date, datetime
from evaluation_common import ContractError, HASH, ID, TEXT, digest, obj, read, rows, save, validate
from evaluation_metrics import rate
from contracts import DRAFT_SCHEMA

ANSWER_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema', **obj({
    'case_id': ID, 'origin': {'enum': ['llm_draft', 'software_fixture']},
    'provider': ID, 'model': ID, 'prompt_sha256': HASH, 'generated_at': TEXT, 'draft': DRAFT_SCHEMA})}
FINDING_SCHEMA = obj({'claim_id': ID, 'supported': {'type': 'boolean'},
    'qualifications_preserved': {'type': 'boolean'}, 'sources_relevant': {'type': 'boolean'}, 'rationale': TEXT})
ANSWER_REVIEW_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema', **obj({
    'case_id': ID, 'answer_sha256': HASH, 'question_sha256': HASH, 'protocol_sha256': HASH,
    'review_kind': {'enum': ['licensed_legal_professional', 'software_fixture']},
    'reviewer_id': ID, 'credential_reference': TEXT, 'jurisdiction': {'const': 'PH'},
    'license_attested': {'type': 'boolean', 'const': True}, 'reviewed_on': TEXT,
    'current_applicability_checked': {'type': 'boolean', 'const': True},
    'answer_relevant': {'type': 'boolean'}, 'coverage_complete': {'type': 'boolean'},
    'clear': {'type': 'boolean'}, 'claim_findings': {'type': 'array', 'minItems': 1, 'items': FINDING_SCHEMA}})}


def evaluate_answers(cases, answers, reviews, protocol_sha256, *, as_of, allow_test_reviews=False):
    case_map = {c['case_id']: c for c in cases}
    answer_map, review_map = {}, {}
    for answer in answers:
        validate(answer, ANSWER_SCHEMA)
        cid = answer['case_id']
        if cid not in case_map or cid in answer_map:
            raise ContractError('Unknown or duplicate answer case_id')
        if answer['origin'] == 'software_fixture' and not allow_test_reviews:
            raise ContractError('Software answer fixtures are forbidden in normal scoring')
        generated = datetime.fromisoformat(answer['generated_at'])
        if generated.tzinfo is None or generated.date() > date.fromisoformat(as_of):
            raise ContractError('Answer timestamp must have a timezone and cannot be in the future')
        if answer['draft']['question_text'] != case_map[cid]['question_text']:
            raise ContractError('Draft question does not match evaluation case')
        claims = [c['claim_id'] for c in answer['draft']['claims']]
        if len(claims) != len(set(claims)):
            raise ContractError('Duplicate draft claim IDs')
        answer_map[cid] = answer
    for review in reviews:
        validate(review, ANSWER_REVIEW_SCHEMA)
        cid = review['case_id']
        if cid not in answer_map or cid in review_map:
            raise ContractError('Unknown or duplicate reviewed answer')
        if review['review_kind'] == 'software_fixture' and not allow_test_reviews:
            raise ContractError('Software review fixtures are forbidden in normal scoring')
        if (review['answer_sha256'] != digest(answer_map[cid]) or review['question_sha256'] != digest(case_map[cid]['question_text'])
                or review['protocol_sha256'] != protocol_sha256):
            raise ContractError('Answer review binding mismatch')
        reviewed_on = date.fromisoformat(review['reviewed_on'])
        if reviewed_on.isoformat() != review['reviewed_on'] or reviewed_on > date.fromisoformat(as_of):
            raise ContractError('Invalid or future review date')
        if reviewed_on < datetime.fromisoformat(answer_map[cid]['generated_at']).date():
            raise ContractError('Review predates the answer')
        expected_ids = {c['claim_id'] for c in answer_map[cid]['draft']['claims']}
        findings = [c['claim_id'] for c in review['claim_findings']]
        if len(findings) != len(set(findings)) or set(findings) != expected_ids:
            raise ContractError('Every claim must be reviewed exactly once')
        review_map[cid] = review
    judged = [{'case_id': cid, 'family_id': case_map[cid]['family_id'], 'review': review}
              for cid, review in review_map.items()]
    if judged:
        unsupported = rate(judged, lambda r: sum(not c['supported'] for c in r['review']['claim_findings']),
                           lambda r: len(r['review']['claim_findings']))
        qualifications = rate(judged, lambda r: sum(not c['qualifications_preserved'] for c in r['review']['claim_findings']),
                              lambda r: len(r['review']['claim_findings']))
        quality = rate(judged, lambda r: int(r['review']['answer_relevant'] and r['review']['coverage_complete'] and
            all(c['supported'] and c['qualifications_preserved'] and c['sources_relevant'] for c in r['review']['claim_findings'])))
    else:
        unsupported = qualifications = quality = None
    return {'status': 'reviewed_external_drafts' if judged else 'not_measured',
        'answers_supplied': len(answers), 'answers_reviewed': len(judged), 'unreviewed_case_ids': sorted(set(answer_map) - set(review_map)),
        'unsupported_claim_rate': unsupported, 'missing_qualification_rate': qualifications,
        'reviewed_answer_quality_rate': quality, 'false_decline_rate': None,
        'false_decline_unavailable_reason': 'Needs independently adjudicated current-answerability labels for answered and declined questions.',
        'scoring_meaning': 'Raw supplied drafts assessed against separately supplied operator review judgments; does not override Item 12 source/display gates.',
        'software_fixture_mode': allow_test_reviews, 'reviewer_identity_authenticated': False,
        'license_attestation_is_not_machine_authentication': True,
        'live_llm_calls': 0, 'answer_generation_allowed': False, 'deployment_allowed': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases', required=True); p.add_argument('--answers', required=True)
    p.add_argument('--reviews', required=True); p.add_argument('--protocol', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    from pathlib import Path
    from evaluation_common import sha
    if Path(args.output).exists(): raise ValueError('Use a new answer-scoring output file')
    protocol = read(args.protocol)
    save(args.output, evaluate_answers(rows(args.cases), rows(args.answers), rows(args.reviews),
                                       sha(args.protocol), as_of=protocol['as_of']))
