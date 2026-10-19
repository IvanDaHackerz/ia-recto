"""AI-authored software fixtures, never independent human or legal review data."""
from __future__ import annotations

import copy
from verification import digest

AS_OF = '2026-10-17'
LABOR = 'I work for a private company. Can my employer require more than eight hours a day?'
PRICE = 'The shop charged me more than the price tag.'
MIXED = 'I work for a private company and I was not paid overtime. A store charged me more than the price tag.'
PARTIAL = 'A store refuses my warranty. I have a complaint about my seafarer deployment.'
FINAL_PAY = 'When must my private employer release my final pay and certificate of employment?'
CLARIFY = 'My salary is late.'
EXCLUDED = 'My bank charged a fee.'
ARTICLE_83 = 'LAB_CODE_2022__art_83__chunk_0001'
ARTICLE_87 = 'LAB_CODE_2022__art_87__chunk_0001'
ARTICLE_81 = 'RA_7394_1992__art_81__chunk_0001'


def excerpt(verifier, question, *, preferred=None):
    pre = verifier.preflight(question, 'recorded_excerpt')
    draft = verifier.excerpt_draft(question, pre)
    for claim in draft['claims']:
        component = next(c for c in pre['components'] if c['component_id'] == claim['component_id'])
        cid = (preferred or {}).get(component['allowed_domain'])
        if cid:
            hit = next(h for h in component['candidates'] if h['chunk_id'] == cid)
            claim['text'] = hit['parent_text']
            claim['evidence'] = [{k: hit[k] for k in ['chunk_id', 'provision_id', 'document_id']} |
                                 {'start': 0, 'end': len(hit['parent_text']), 'quote': hit['parent_text']}]
    return draft


def software_reviews(verifier, question, draft):
    """Simulate an operator review to exercise gates. These findings are invented.

    A normal verifier/CLI rejects this store. It does not update trusted_reviews.
    """
    pre = verifier.preflight(question, 'recorded_excerpt')
    components = {c['component_id']: c for c in pre['components']}
    store = {'schema_version': '1.0', 'source_reviews': [], 'claim_reviews': []}
    seen = set()
    for claim in draft['claims']:
        comp = components[claim['component_id']]
        base = {**verifier.review_binding(question, comp),
                'review_kind': 'software_fixture', 'reviewer': 'AI-authored software fixture; no human reviewer',
                'reviewed_on': AS_OF, 'valid_through': '2026-10-24',
                'rationale': 'Simulated approval for testing control flow only; not a factual legal finding.'}
        for evidence in claim['evidence']:
            r = verifier.records[evidence['chunk_id']]
            key = (comp['component_id'], r['document_id'])
            if key in seen:
                continue
            seen.add(key)
            store['source_reviews'].append({**base, 'review_id': 'fixture_source_' + str(len(seen)),
                'document_id': r['document_id'], 'raw_source_sha256': verifier.source['raw_source_sha256'][r['raw_local_path']],
                'conditions_sha256': verifier.conditions_hash(r), 'related_sources_sha256': verifier.related_hash(r),
                'currentness_checked': True, 'conditions_resolved': True, 'relationships_checked': True,
                'evidence_urls': [r['official_source_url']]})
        store['claim_reviews'].append({**base, 'review_id': 'fixture_claim_' + claim['claim_id'],
            'claim_sha256': digest({'kind': claim['kind'], 'text': claim['text']}),
            'evidence_sha256': digest(claim['evidence']), 'supports_claim': True,
            'relevant_to_concern': True, 'qualifications_preserved': True, 'covers_concern': True})
    return store


def fixture_verifier(verifier, store):
    """Share read-only loaded artifacts, validate the isolated test review store."""
    clone = copy.copy(verifier)
    clone.fixture_mode = True
    clone._load_reviews(store)
    clone._review_snapshot_sha256 = digest(clone.reviews)
    return clone


def cases(verifier):
    labor = excerpt(verifier, LABOR, preferred={'labor': ARTICLE_83})
    price = excerpt(verifier, PRICE, preferred={'consumer': ARTICLE_81})
    mixed = excerpt(verifier, MIXED, preferred={'labor': ARTICLE_87, 'consumer': ARTICLE_81})
    partial = excerpt(verifier, PARTIAL)
    result = []

    def add(name, question, draft, expected, *, category='adversarial', mode='recorded_excerpt', reviews=None, reason=None, expected_ids=None):
        result.append({'case_id': name, 'provenance': 'AI-authored development software fixture',
                       'category': category, 'question_text': question, 'mode': mode,
                       'draft': copy.deepcopy(draft), 'software_reviews': copy.deepcopy(reviews),
                       'expected_preview_components': expected,
                       'expected_preview_component_ids': expected_ids if expected_ids is not None else [f'concern_{i:03d}' for i in range(1, expected + 1)],
                       'expected_reason': reason})

    for name, q, d, n in [('valid_labor_excerpt', LABOR, labor, 1), ('valid_consumer_excerpt', PRICE, price, 1),
                           ('valid_mixed_excerpts', MIXED, mixed, 2), ('valid_partial_excerpt', PARTIAL, partial, 1)]:
        add(name, q, d, n, category='valid_excerpt_control')
    store = software_reviews(verifier, LABOR, labor)
    add('simulated_reviewed_excerpt', LABOR, labor, 1, category='simulated_review_control', mode='current_guidance', reviews=store)
    paraphrase = copy.deepcopy(labor)
    paraphrase['claims'][0].update(kind='paraphrase', text='The stored provision gives an eight-hour normal working day and contains specific rules for covered health personnel.')
    para_store = software_reviews(verifier, LABOR, paraphrase)
    add('simulated_reviewed_paraphrase', LABOR, paraphrase, 1, category='simulated_review_control', mode='current_guidance', reviews=para_store)
    add('real_current_guidance_gate', LABOR, labor, 0, category='real_currentness_gate', mode='current_guidance', reason='scoped_currentness_review_missing')
    add('source_review_without_claim_review', LABOR, labor, 0, mode='current_guidance',
        reviews={**store, 'claim_reviews': []}, reason='claim_support_and_coverage_review_missing')
    add('claim_review_without_source_review', LABOR, labor, 0, mode='current_guidance',
        reviews={**store, 'source_reviews': []}, reason='scoped_currentness_review_missing')

    def mutate(name, operation, reason, *, source=labor, question=LABOR, expected=0, expected_ids=None):
        d = copy.deepcopy(source)
        operation(d)
        add(name, question, d, expected, reason=reason, expected_ids=expected_ids)

    mutate('invented_citation', lambda d: d['claims'][0]['evidence'][0].update(chunk_id='FAKE__art_999__chunk_0001'), 'unknown_or_ineligible_citation')
    mutate('wrong_document', lambda d: d['claims'][0]['evidence'][0].update(document_id='RA_7394_1992'), 'citation_identity_mismatch')
    mutate('wrong_provision', lambda d: d['claims'][0]['evidence'][0].update(provision_id='LAB_CODE_2022__art_87'), 'citation_identity_mismatch')
    mutate('altered_quote', lambda d: d['claims'][0]['evidence'][0].update(quote=d['claims'][0]['text'].replace('eight (8)', 'twelve (12)', 1)), 'quote_or_offset_mismatch')
    mutate('wrong_offsets', lambda d: d['claims'][0]['evidence'][0].update(start=1), 'quote_or_offset_mismatch')
    mutate('out_of_bounds', lambda d: d['claims'][0]['evidence'][0].update(end=999999), 'quote_or_offset_mismatch')
    mutate('boolean_offset', lambda d: d['claims'][0]['evidence'][0].update(start=False), '$.claims[0].evidence[0].start: expected integer')
    mutate('fractional_offset', lambda d: d['claims'][0]['evidence'][0].update(end=1.5), '$.claims[0].evidence[0].end: expected integer')

    def truncate(d):
        e = d['claims'][0]['evidence'][0]
        end = e['quote'].index('Health personnel')
        e.update(end=end, quote=e['quote'][:end])
        d['claims'][0]['text'] = e['quote']
    mutate('removed_qualifications', truncate, 'incomplete_source_context')
    mutate('changed_claim_numbers', lambda d: d['claims'][0].update(text='The law permits twelve normal working hours every day.'), 'excerpt_text_mismatch')
    mutate('invented_remedy', lambda d: d['claims'][0].update(kind='paraphrase', text='Your employer must pay you one million pesos automatically.'), 'paraphrase_not_allowed_in_excerpt_mode')
    mutate('negated_claim', lambda d: d['claims'][0].update(kind='paraphrase', text='Normal working hours shall not be limited to eight hours.'), 'paraphrase_not_allowed_in_excerpt_mode')
    mutate('unsupported_legal_conclusion', lambda d: d['claims'][0].update(kind='paraphrase', text='You will certainly win in court.'), 'paraphrase_not_allowed_in_excerpt_mode')
    add('unreviewed_paraphrase_current_mode', LABOR, paraphrase, 0, mode='current_guidance', reviews={**para_store, 'claim_reviews': []}, reason='claim_support_and_coverage_review_missing')

    # A real, eligible citation from the wrong concern must not pass.
    def unrelated(d):
        e = copy.deepcopy(price['claims'][0]['evidence'][0])
        d['claims'][0].update(text=e['quote'], evidence=[e])
    mutate('cross_domain_citation', unrelated, 'citation_not_retrieved_for_component')
    mutate('unknown_component', lambda d: d['claims'][0].update(component_id='concern_999'), 'unknown_or_excluded_component')
    mutate('draft_self_approval', lambda d: d.update(approved=True), "$: unexpected fields ['approved']")
    mutate('unchecked_answer_text', lambda d: d.update(answer_text='You definitely win.'), "$: unexpected fields ['answer_text']")
    mutate('forged_citation_label', lambda d: d['claims'][0]['evidence'][0].update(citation_display='Article 999'), "$.claims[0].evidence[0]: unexpected fields ['citation_display']")
    mutate('changed_original_question', lambda d: d.update(question_text=PRICE), 'Draft question differs from the original question')
    mutate('duplicate_claim', lambda d: d['claims'].append(copy.deepcopy(d['claims'][0])), 'Duplicate claim_id')
    mutate('empty_draft', lambda d: d.update(claims=[]), '$.claims: invalid array length')
    mutate('duplicate_evidence', lambda d: d['claims'][0]['evidence'].append(copy.deepcopy(d['claims'][0]['evidence'][0])), 'duplicate_evidence')
    mutate('missing_mixed_component', lambda d: d['claims'].pop(), 'missing_component_claims', source=mixed, question=MIXED, expected=1)
    mutate('bad_mixed_component', lambda d: d['claims'][0].update(text='Fabricated rule'), 'excerpt_text_mismatch', source=mixed, question=MIXED, expected=1, expected_ids=['concern_002'])
    def bad_sibling(d):
        c = copy.deepcopy(d['claims'][0])
        c.update(claim_id='invalid_second_claim', text='Additional unsupported conclusion')
        d['claims'].append(c)
    mutate('bad_sibling_withholds_whole_concern', bad_sibling, 'excerpt_text_mismatch')
    mutate('claim_on_excluded_concern', lambda d: d['claims'][0].update(component_id='excluded_001'), 'unknown_or_excluded_component', source=partial, question=PARTIAL)

    # These modifications preserve valid JSON while invalidating review bindings.
    for name, field, value, reason in [
        ('expired_review', 'valid_through', '2026-10-16', 'review_expired_or_invalid_interval'),
        ('future_review', 'reviewed_on', '2026-10-18', 'review_date_in_future'),
        ('overlong_review', 'valid_through', '2027-10-17', 'review_interval_exceeds_policy'),
        ('wrong_source_hash', 'raw_source_sha256', '0' * 64, 'scoped_currentness_review_missing'),
        ('wrong_condition_hash', 'conditions_sha256', '0' * 64, 'scoped_currentness_review_missing'),
        ('wrong_relationship_hash', 'related_sources_sha256', '0' * 64, 'scoped_currentness_review_missing'),
        ('wrong_question_binding', 'question_sha256', '0' * 64, 'scoped_currentness_review_missing'),
        ('wrong_policy_binding', 'policy_sha256', '0' * 64, 'scoped_currentness_review_missing'),
        ('wrong_component_binding', 'component_sha256', '0' * 64, 'scoped_currentness_review_missing'),
        ('wrong_index_binding', 'index_version', 'other-index', 'scoped_currentness_review_missing'),
    ]:
        changed = copy.deepcopy(store)
        changed['source_reviews'][0][field] = value
        add(name, LABOR, labor, 0, mode='current_guidance', reviews=changed, reason=reason)
    changed = copy.deepcopy(labor)
    changed['claims'][0].update(kind='paraphrase', text='No overtime pay is required.')
    add('changed_claim_invalidates_review', LABOR, changed, 0, mode='current_guidance', reviews=store, reason='claim_support_and_coverage_review_missing')

    for name, q, reason in [('final_pay_gap', FINAL_PAY, 'no_eligible_retrieval_evidence'),
                             ('clarification_route', CLARIFY, None), ('excluded_route', EXCLUDED, None)]:
        d = copy.deepcopy(labor)
        d['question_text'] = q
        add(name, q, d, 0, category='routing_or_corpus_gap', reason=reason)
    return result
