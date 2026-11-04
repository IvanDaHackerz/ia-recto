"""Helpful application responses without changing learned labels or legal approvals."""
from __future__ import annotations
import copy
import re
from .source_issues import issue_for

VERSION = 'conversational-guidance-v1.3.0'
EMPLOYMENT_TYPE = re.compile(r'\b(?:private|pribado|government|gobyerno|gobierno|govt|municipal|civil.service|kasambahay|household|domestic.worker|ofw|overseas|seaf\w*r)\b', re.I)
LABOR_ISSUE = re.compile(r'\b(?:salary|salaries|wages?|sahod|sweldo|overtime|holiday.pay|13th.month|thirteenth.month|working.hours|hours.of.work|fired|dismiss\w*|terminat\w*)\b', re.I)
GENERAL_SCOPE = ('The labor sources below concern private-sector employment. Your employment type has not been confirmed, '
                 'so this is general information, not a finding that these rules apply to your job.')
EMPLOYMENT_FOLLOW_UP = 'Is your employment with a private company, government, a household, an overseas employer, or as a seafarer?'
SEARCH_ALIASES = [(r'\bsira\b', 'defective'), (r'\b(?:binili|nabili)\b', 'bought'),
                  (r'\bpalitan\b', 'replace'), (r'\bayaw\b', 'refuses'),
                  (r'\bgarantiya\b', 'warranty')]


def prepare_situation_context(packet, verifier):
    """Keep an explicit same-scenario follow-up with its factual background.

    This application search grouping preserves the classifier's routing and
    original components for inspection. It only reuses retrieved canonical
    candidates and recomputes their gates for the combined question.
    """
    result = packet.get('result')
    if not result or result['excluded_components'] or len(result['components']) != 2:
        return
    first, follow = result['components']
    question = result['question_text']
    if first['allowed_domain'] != follow['allowed_domain']:
        return
    if re.search(r'\b(?:separately|unrelated|another\s+(?:issue|concern|purchase)|hiwalay|bukod)\b', question, re.I):
        return
    if re.match(r'^(?:what|how|why|can|does|is|are|do|should)\b', first['query'], re.I):
        return
    if not re.match(r'^(?:(?:does|is|would|can|should)\s+(?:this|that|it|being)\b|(?:what|how)\s+does\s+(?:this|that|it)\b)', follow['query'], re.I):
        return
    from dataset.pipelines.item11.query_relevance import source_relevance
    domain = first['allowed_domain']
    hits = {h['chunk_id']: h for c in (first, follow) for h in c['candidates']
            if source_relevance(question, domain, h) > 0 and not verifier.check_candidate(h, domain)}
    if not hits:
        return
    grouped = {**copy.deepcopy(first), 'query': question,
               'candidates': sorted(hits.values(), key=lambda h: (source_relevance(question, domain, h), h['score']), reverse=True)[:5],
               'retrieval_reason': 'same_situation_follow_up'}
    grouped['evidence_gates'] = [verifier.source_gate(question, grouped, h, result['mode']) for h in grouped['candidates']]
    grouped['evidence_ready'] = any(g['passed'] for g in grouped['evidence_gates'])
    packet['situation_context'] = {'reason': 'same_situation_follow_up',
        'original_components': [{'component_id': c['component_id'], 'query': c['query']} for c in (first, follow)]}
    result['components'] = [grouped]
    result['all_supported_components_evidence_ready'] = grouped['evidence_ready']
    result['offline_drafting_allowed'] = grouped['evidence_ready']
    result['decision'] = 'evidence_ready' if grouped['evidence_ready'] else 'insufficient_evidence'


TOPIC_CONTEXT = {
    'labor.wages_payment': 'Your concern is about payment for work already done. The details to compare with the recorded rules are the agreed payday, the period worked, and any reason given for withholding or deducting pay.',
    'labor.hours_of_work': 'Your question is about which activities count toward working time. What matters for reading these passages is what the employer requires you to do, when you do it, and whether you are free to use that time for yourself.',
    'labor.rest_days': 'Your concern is about the scheduled rest period and any work required during it. Check the actual schedule and whether your question concerns the time off, payment for work, or both.',
    'labor.overtime_pay': 'Your concern is about work beyond your ordinary hours. The relevant facts include the hours actually worked, the type of day, and your employment coverage; a salary label alone does not supply all those facts.',
    'labor.holiday_premium_pay': 'Your question concerns holiday or special-day pay. Identify the type of day, whether work was performed, and the coverage conditions before applying a quoted rate to your situation.',
    'labor.thirteenth_month_pay': 'Your concern is about thirteenth-month pay. Your work arrangement, basic salary earned, and period of employment are the details to compare with the supplied coverage and computation provisions.',
    'labor.employment_contracts': 'Your question concerns the employment arrangement described in your contract and actual work. Compare the work, hiring circumstances, and any stated standards with the source conditions rather than treating a contract label as a complete answer.',
    'labor.termination_due_process': 'Your concern is about the reason for ending employment and the process followed. Keep the stated reason, notices received, and opportunity to respond separate when reading the relevant provisions.',
    'labor.final_pay_coe': 'Your question concerns final pay or a certificate of employment. Distinguish the date employment ended from the date a certificate was requested; the documents and events are different.',
    'labor.complaint_referral': 'You are asking how to seek assistance with an employment concern. The nature of the dispute matters when choosing a process; a referral does not itself decide the merits of the complaint.',
    'consumer.general_framework': 'You are asking about the general consumer-law framework. A broad policy provision supplies context; a specific remedy still needs a provision addressing the transaction and its conditions.',
    'consumer.defective_products': 'Your concern is about whether the item delivered works or matches what was sold. The description of the problem, the promised features, and the seller’s response are the facts to compare with the product provisions.',
    'consumer.warranties': 'Your concern is about a warranty promise or claim. Keep the warranty terms, proof of purchase, item, and the seller’s response together when checking what the supplied warranty provision actually covers.',
    'consumer.repair_replace_refund': 'You are asking about a remedy for a purchase problem. The defect or mismatch and any repair already attempted matter; the available passage must support the conditions for the particular remedy you want.',
    'consumer.deceptive_unfair_sales': 'Your concern is about what was represented before you paid and what was disclosed afterward. Compare the actual representation and omitted term with the supplied sales-practice rule without assuming the allegation is already proven.',
    'consumer.misleading_advertising': 'Your question concerns a difference between an advertisement and the product or offer received. Keep a copy of the claimed feature or promotion so it can be compared with the actual terms and item.',
    'consumer.price_tags': 'Your concern is the difference between the displayed price and the amount charged. Check that the tag and receipt refer to the same item and size when comparing the situation with the price provision.',
    'consumer.product_safety': 'Your concern is about a product’s behavior during use and a possible safety issue. Distinguish what happened, any harm reported, and the item’s ordinary use; the project cannot inspect the product or establish its safety from a message.',
    'consumer.service_complaints': 'Your concern is about the service agreed and the work actually performed. The agreed scope, authorization for changes, payment, and business’s response help distinguish the service issue from an employment-payment dispute.',
    'consumer.online_transactions': 'Your question concerns an online purchase. The seller’s role, order description, delivery history, and messages matter when comparing your transaction with the recorded online-consumer provisions.',
    'consumer.complaint_referral': 'You want assistance with a consumer complaint. Keep the order or receipt, the problem, and the seller’s response together so the complaint can be described accurately; a referral is not a decision granting a remedy.',
}


def situation_paragraphs(result, quotes, verifier):
    """Source-topic reading help, not a replacement legal determination."""
    paragraphs = []
    for component in (result or {}).get('components', []):
        quote = next((q for q in quotes if q['component_id'] == component['component_id']), None)
        record = verifier.records.get(quote['chunk_id'], {}) if quote else {}
        topics = record.get('supported_topics', [])
        priorities = [('labor.overtime_pay', r'\b(?:overtime|ot)\b'),
                      ('labor.thirteenth_month_pay', r'\b(?:13th|thirteenth)\b'),
                      ('labor.final_pay_coe', r'\b(?:final.pay|coe|certificate.of.employment)\b'),
                      ('consumer.warranties', r'\bwarrant\w*\b'),
                      ('consumer.price_tags', r'\b(?:price.tag|displayed.price|shelf.label)\b')]
        preferred = [topic for topic, pattern in priorities if topic in topics and re.search(pattern, component['query'], re.I)]
        topics = preferred + [t for t in topics if t not in preferred]
        text = next((TOPIC_CONTEXT[t] for t in topics if t in TOPIC_CONTEXT), None)
        if text and text not in paragraphs:
            paragraphs.append(text)
    return paragraphs


def prepare_general_information(packet, question, inspect):
    """Retrieve under an explicit scope assumption; retain original predictions.

    The original input and its classifier result remain available. Only an
    independently rechecked, coherent hypothetical private-employment query can
    supply sources. Explicit excluded categories and unresolved fragments stay
    subject to the existing classifier/verifier rules.
    """
    result = packet.get('result')
    if not result:
        return
    from scope_constraints import scope_text
    matching_question = scope_text(question)
    route = result['routing']
    has_type = bool(EMPLOYMENT_TYPE.search(matching_question))
    if (route['routing_action'] == 'clarify' and not has_type and LABOR_ISSUE.search(matching_question)
            and route['reason'] in {'employment_category_missing', 'low_confidence'}):
        contextual_query = 'Private employee ako. ' + question
        candidate = inspect(contextual_query)['result'] if len(contextual_query) <= 8000 else None
        if (candidate and candidate['routing']['routing_action'] in {'retrieve_supported_evidence', 'retrieve_supported_components'}
                and any(c['allowed_domain'] == 'labor' for c in candidate['components'])):
            context = {'mode': 'conditional_private_employment', 'note': GENERAL_SCOPE,
                       'follow_up': EMPLOYMENT_FOLLOW_UP, 'original_routing': copy.deepcopy(route),
                       'retrieval_question_text': contextual_query, 'classification_is_conditional': True}
            candidate['question_text'] = question
            candidate['general_information_context'] = GENERAL_SCOPE
            packet['result'] = result = candidate
            packet['guidance_context'] = context
            packet['clarification_follow_up'] = None
    if (not has_type and 'guidance_context' not in packet
            and result['routing']['routing_action'] in {'retrieve_supported_evidence', 'retrieve_supported_components'}
            and any(c['allowed_domain'] == 'labor' for c in result['components'])):
        packet['guidance_context'] = {'mode': 'general_private_employment', 'note': GENERAL_SCOPE,
            'follow_up': EMPLOYMENT_FOLLOW_UP, 'classification_is_conditional': False,
            'original_routing': copy.deepcopy(route)}
        result['general_information_context'] = GENERAL_SCOPE
    # A source-search vocabulary repair is not a factual rewrite of the question.
    # It runs only for an already admitted, wholly consumer query with no hits.
    if (result['routing']['routing_action'] == 'retrieve_supported_evidence'
            and result['routing']['predicted_primary'] == 'consumer'
            and result['components'] and not result['excluded_components']
            and all(c['allowed_domain'] == 'consumer' and not c['candidates'] for c in result['components'])):
        expanded = question
        for pattern, replacement in SEARCH_ALIASES:
            expanded = re.sub(pattern, replacement, expanded, flags=re.I)
        if expanded != question:
            candidate = inspect(expanded)['result'] if len(expanded) <= 8000 else None
            if (candidate and candidate['routing']['routing_action'] == 'retrieve_supported_evidence'
                    and candidate['routing']['predicted_primary'] == 'consumer'
                    and candidate['routing']['predicted_scope'] == result['routing']['predicted_scope']
                    # Equivalent aliases may expose multiple consumer predicates.
                    # Domain, coverage and exclusion checks still all apply.
                    and not candidate['excluded_components']
                    and all(c['allowed_domain'] == 'consumer' for c in candidate['components'])
                    and any(c['candidates'] for c in candidate['components'])):
                candidate['question_text'] = question
                # Preserve the original classifier labels/probabilities; only the
                # additional search wording and resulting source candidates differ.
                candidate['routing'] = copy.deepcopy(result['routing'])
                packet['result'] = candidate
                packet['search_help'] = {'query': expanded, 'reason': 'equivalent_consumer_search_terms', 'changes_user_facts': False}


def eligible_quotes(verifier, result):
    from dataset.pipelines.item11.query_relevance import relevant_excerpt, source_relevance
    quotes = []
    for component in (result or {}).get('components', []):
        gates = {g['chunk_id']: g for g in component['evidence_gates']}
        for hit in component['candidates']:
            gate = gates.get(hit['chunk_id'])
            if (not gate or set(gate['reasons']) - {'scoped_currentness_review_missing'}
                    or issue_for(hit) or verifier.check_candidate(hit, component['allowed_domain'])
                    or source_relevance(component['query'], component['allowed_domain'], hit) <= 0):
                continue
            text = hit['parent_text']
            quote = relevant_excerpt(component['query'], component['allowed_domain'], hit)
            if not quote:
                continue
            if any(q['quote']==quote for q in quotes):
                break
            quotes.append({'component_id': component['component_id'], 'chunk_id': hit['chunk_id'],
                'citation_display': hit.get('citation_label', hit['citation_display']), 'quote': quote,
                'complete_provision': quote == text})
            break
        if len(quotes) == 3:
            break
    return quotes


def response_for(packet, verifier, question):
    """Every completed analysis gets useful prose, including non-LLM responses."""
    explanation = packet['explanation']
    result = packet.get('result')
    route = (result or {}).get('routing', {})
    context = packet.get('guidance_context')
    response = {'version': VERSION, 'kind': 'clarification', 'heading': 'Let’s work out the concern',
                'paragraphs': [], 'follow_up': None, 'follow_up_options': [], 'quotes': [], 'ai_generated': False}
    if packet.get('safety_notice'):
        return {**response, 'kind': 'safety', 'heading': 'Your immediate safety comes first',
                'paragraphs': ['The immediate safety concern takes priority. Follow the emergency information shown here; this project cannot assess an injury or investigate an assault.']}
    generated = (explanation['status'] in {'generated','partially_generated'} and explanation.get('citations_checked') and explanation.get('automated_support_checked')
                 or explanation['status'] == 'verified' and explanation.get('legal_support_verified'))
    if generated:
        partial=explanation['status']=='partially_generated'
        response.update(kind='partial_ai_explanation' if partial else 'ai_explanation',
                        heading='AI explanation for supported parts' if partial else 'AI explanation',ai_generated=True)
        if partial:
            answered = {c.get('component_id') for c in explanation.get('claims', [])}
            response['quotes'] = [q for q in eligible_quotes(verifier, result) if q['component_id'] not in answered]
    elif not result or route.get('routing_action') == 'clarify':
        follow = (packet.get('clarification_follow_up') or {}).get('question') or route.get('clarification_question') or (packet.get('normalization') or {}).get('clarification_question')
        response['paragraphs'] = ['I need one more detail to choose the right sources. This project covers selected Philippine private-sector employment and ordinary consumer-purchase concerns.']
        response['follow_up'] = follow or 'What happened, who was involved, and what would you like help with?'
        if (not re.search(r'\b(?:private|pribado|contractor)\b', question, re.I)
                and re.search(r'\b(?:employee|empleyad[oa]|employed|nagtatrabaho)\b.{0,65}\b(?:city.treasurer|city.hall|municipal.office|munisipyo)\b', question, re.I)):
            response['paragraphs'] = ['You described an employment concern involving a city or municipal office. Before using private-sector labor sources, I need to confirm whether this is government employment. Government employment is outside this project’s selected labor module.']
            response['follow_up'] = 'Is this a government-employed position, or are you employed by a private company assigned to that office?'
    elif route.get('routing_action') == 'refer_out_of_scope':
        response.update(kind='referral', heading='Where this concern fits', paragraphs=[
            'This concern falls outside this project’s selected private-sector labor and ordinary consumer topics. The classifier is identifying a scope limit; it is not deciding whether you have legal rights or a valid complaint.',
            'Any assistance contacts listed below are recorded directory entries. Check with the agency about whether it handles your concern.'])
    else:
        quotes = eligible_quotes(verifier, result)
        response.update(kind='recorded_sources' if quotes else 'source_limit', heading='What I found', quotes=quotes)
        if quotes:
            response['heading'] = 'About your question'
            response['paragraphs'] = situation_paragraphs(result, quotes, verifier) or ['I found recorded material for the concern you described. Compare the facts in your question with the passage’s conditions; the quotation alone does not settle how the rule applies to you.']
        else:
            response['paragraphs'] = ['I understand this as a concern within the project’s topics, but the available records are not sufficient for a supported legal explanation. That is a source limitation, not a conclusion that you have no rights.']
        reason = explanation['reason']
        failure = explanation.get('failure_code')
        if reason == 'local_only':
            response['paragraphs'].append('AI is off for this question. This response uses local analysis and recorded sources.')
        elif reason == 'provider_unavailable':
            detail = ('The server’s API key was not accepted.' if failure == 'provider_auth_failed' else
                      'The local daily AI-use limit was reached.' if failure == 'daily_provider_limit' else
                      'The AI service could not complete its response.')
            response['paragraphs'].append(detail + ' You can still inspect the recorded sources and try AI again later.')
        elif reason in {'citation_validation_failed', 'claim_support_failed', 'support_check_unavailable', 'no_supported_explanation'}:
            response['paragraphs'].append('I could not confirm a source-supported AI explanation for this question. The recorded material remains available below.')
        if not quotes:
            response['paragraphs'].append('Rewording a clear question will not add a missing legal source. You can inspect the library or the assistance contacts below for the next place to check.')
        elif reason == 'source_review_required':
            response['paragraphs'].append('AI explanations are not configured in this running server. The local source response remains available.')
    if context:
        response['follow_up'] = context['follow_up']
        response['follow_up_options'] = [
            {'label': label, 'question_text': prefix + ' ' + question} for label, prefix in [
                ('Private company', 'Private employee ako.'), ('Government', 'Government employee ako.'),
                ('Household', 'Kasambahay ako.'), ('Overseas / OFW', 'OFW ako.'), ('Seafarer', 'Seafarer ako.')]]
    return response
