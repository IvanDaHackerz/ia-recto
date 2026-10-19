"""Assemble disclosed development cases without querying any model predictions."""
from __future__ import annotations
from evaluation_common import ROOT, HERE, read, rows, validate_cases

DEV = 'dataset/processed/item10/ai_reviewed_eval_v1.0.0'
IR = 'outputs/item11-retrieval-v1.2.3/benchmark_queries.jsonl'
ART87 = 'LAB_CODE_2022__art_87'
WAGE_PAYMENT = 'LAB_IRR_1989__rule_viii_payment_of_wages__section_3'
ART81 = 'RA_7394_1992__art_81'
WARRANTY = ['RA_7394_1992__art_68', 'RA_7394_1992__art_72']


def route(primary):
    return {'labor': 'retrieve_supported_evidence', 'consumer': 'retrieve_supported_evidence',
            'mixed': 'retrieve_supported_components', 'out_of_scope': 'refer_out_of_scope', None: 'clarify'}[primary]


def base(cid, suite, family, question, lang, primary, scope, domains, excluded, path, rid):
    return {'case_id': cid, 'suite': suite, 'family_id': family, 'question_text': question,
        'language': lang, 'variation': 'clear_wording', 'origin': 'ai_authored', 'role': 'development',
        'source_path': path, 'source_record_id': rid, 'expected_primary': primary, 'expected_scope': scope,
        'expected_route': route(primary), 'expected_clarification_reason': None,
        'expected_domains': sorted(domains), 'expected_excluded': excluded, 'topic_ids': [],
        'relevant_ids': [], 'retrieval_judgment': 'unjudged', 'concerns': []}


def concern(domain, anchors, ids=(), gap=False):
    return {'domain': domain, 'anchors': anchors, 'relevant_ids': list(ids), 'evidence_gap': gap}


def system_cases():
    # Three variants stay in one family. Expectations are authored from scope
    # and existing provision judgments before any inference, not from predictions.
    families = [
        ('mixed', 'fully_supported', ['labor', 'consumer'], False,
         [concern('labor', ['overtime'], [ART87]), concern('consumer', ['price tag'], [ART81])], [
            'My private employer did not pay overtime. A shop charged more than the price tag.',
            'Private employee ako, unpaid ang overtime. Sa shop naman, mas mahal ang singil kaysa price tag.',
            'private employe here overtime unpayed. shop charged more than price tag.']),
        ('mixed', 'partially_supported', ['labor'], True,
         [concern('labor', ['salary', 'wages', 'sahod'], [WAGE_PAYMENT]), concern('excluded', ['seafarer'])], [
            'My private employer delays my salary. Separately, I have a complaint about seafarer deployment.',
            'Private employee ako, delayed ang sahod. Hiwalay na concern ko ang seafarer deployment.',
            'private employe salary delayed. separate concern about seafarer deployment.']),
        ('mixed', 'partially_supported', ['consumer'], True,
         [concern('consumer', ['warranty'], WARRANTY), concern('excluded', ['address', 'privacy'])], [
            'A retail shop refuses my product warranty. Separately, it published my home address online.',
            'Ayaw ng retail shop sa product warranty ko. Hiwalay na issue, inilabas nila home address ko online.',
            'retail shop refuses product warranty. separately published my home address online.']),
        ('mixed', 'fully_supported', ['labor', 'consumer'], False,
         [concern('labor', ['final pay', 'coe'], gap=True), concern('consumer', ['price tag'], [ART81])], [
            'When must my private employer release final pay and COE? A store also charged more than the price tag.',
            'Private employee ako, kailan ang final pay at COE? Sa store naman, mas mataas ang singil kaysa price tag.',
            'private employe final pay and coe when? store charged more than price tag.']),
        (None, None, [], False, [], [
            'My salary is late. A shop also refuses my product refund.',
            'Late ang salary ko. Ayaw din ng shop magbigay ng product refund.',
            'my salary late. shop also refuses product refund.']),
        ('mixed', 'partially_supported', ['labor'], True,
         [concern('labor', ['wages', 'salary', 'sahod'], [WAGE_PAYMENT]), concern('excluded', ['government'])], [
            'My private employer delayed my wages. My spouse has a separate unpaid salary complaint against a government employer.',
            'Private employer ko delayed ang sahod. Hiwalay ang unpaid salary ng spouse ko na government employee.',
            'private employer wages delayed. spouse has separate unpaid salary from government employer.']),
        ('out_of_scope', 'unsupported', [], True, [concern('excluded', ['bank']), concern('excluded', ['insurance'])], [
            'My bank charged a credit card fee. Separately, my insurance claim was denied.',
            'May credit card fee ang bank ko. Hiwalay na issue, denied ang insurance claim ko.',
            'bank charged credit card fee. separately insurance claim denied.']),
        ('labor', 'fully_supported', ['labor'], False, [concern('labor', ['final pay', 'coe'], gap=True)], [
            'When must my private employer give final pay and COE?',
            'Private employee ako. Kailan dapat ibigay ang final pay at COE?',
            'private employe final pay and coe when should employer give?']),
    ]
    result = []
    for i, (primary, scope, domains, excluded, concerns, questions) in enumerate(families, 1):
        for j, question in enumerate(questions, 1):
            cid = f'SYS_{i:02d}_{j}'
            row = base(cid, 'system', f'system:SYS_{i:02d}', question, 'en_tl' if j == 2 else 'en',
                       primary, scope, domains, excluded, 'dataset/pipelines/item13/create_cases.py', cid)
            row.update(variation=['clear_wording', 'taglish', 'informal_typing'][j - 1], concerns=concerns)
            if primary is None:
                row['expected_clarification_reason'] = 'employment_category_missing'
            result.append(row)
    return result


def create():
    result = []
    for suite, filename in [('general', 'evaluation_questions.jsonl'), ('typing', 'typing_questions.jsonl')]:
        path = DEV + '/' + filename
        for r in rows(ROOT / path):
            primary, scope = r.get('primary_label'), r.get('scope_label')
            topics = r['supported_topic_ids'] + r['excluded_topic_ids']
            domains = {t.split('.')[0] for t in r['supported_topic_ids']}
            case = base(r['question_id'], suite, suite + ':' + r['scenario_family_id'], r['question_text'],
                        r['language_style'], primary, scope, domains, bool(r['excluded_topic_ids']), path, r['question_id'])
            case.update(topic_ids=topics, variation=r.get('variation_type', 'clear_wording'))
            if primary is None:
                case['expected_clarification_reason'] = {'TYPE_G17': 'employment_category_missing',
                    'TYPE_G18': 'refund_transaction_missing', 'TYPE_G19': 'contract_relationship_missing',
                    'TYPE_G20': 'charge_context_missing'}[r['scenario_family_id']]
            result.append(case)
    for r in rows(ROOT / IR):
        positive = bool(r['relevant_provision_ids'])
        supported = positive or r['expected_status'] == 'no_eligible_evidence'
        primary, scope = (r['domain'], 'fully_supported') if supported else ('out_of_scope', 'unsupported')
        case = base(r['query_id'], 'retrieval', 'retrieval:' + r['scenario_family_id'], r['question_text'],
                    r['language_style'], primary, scope, [r['domain']] if supported else [], not supported, IR, r['query_id'])
        case.update(relevant_ids=r['relevant_provision_ids'], retrieval_judgment='known_relevant' if positive else 'no_candidates',
                    topic_ids=r.get('topic_ids') or [])
        result.append(case)
    result.extend(system_cases())
    eligible = {r['provision_id'] for r in rows(ROOT / 'outputs/item11-retrieval-v1.2.3/records.jsonl')}
    validate_cases(result, eligible)
    return result


if __name__ == '__main__':
    import json
    from collections import Counter
    cases = create()
    print(json.dumps({'cases': len(cases), 'suites': dict(Counter(c['suite'] for c in cases)),
                      'role': 'AI-authored development only; no inference performed'}))
