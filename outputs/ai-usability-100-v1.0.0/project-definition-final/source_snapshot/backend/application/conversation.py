"""Helpful application responses without changing learned labels or legal approvals."""
from __future__ import annotations
import copy
import re
from .source_issues import issue_for

VERSION = 'conversational-guidance-v1.1.0'
EMPLOYMENT_TYPE = re.compile(r'\b(?:private|pribado|government|gobyerno|gobierno|govt|municipal|civil.service|kasambahay|household|domestic.worker|ofw|overseas|seaf\w*r)\b', re.I)
LABOR_ISSUE = re.compile(r'\b(?:salary|salaries|wages?|sahod|sweldo|overtime|holiday.pay|13th.month|thirteenth.month|working.hours|hours.of.work|fired|dismiss\w*|terminat\w*)\b', re.I)
GENERAL_SCOPE = ('The labor sources below concern private-sector employment. Your employment type has not been confirmed, '
                 'so this is general information, not a finding that these rules apply to your job.')
EMPLOYMENT_FOLLOW_UP = 'Is your employment with a private company, government, a household, an overseas employer, or as a seafarer?'
SEARCH_ALIASES = [(r'\bsira\b', 'defective'), (r'\b(?:binili|nabili)\b', 'bought'),
                  (r'\bpalitan\b', 'replace'), (r'\bayaw\b', 'refuses'),
                  (r'\bgarantiya\b', 'warranty')]


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
    from dataset.pipelines.item11.query_relevance import relevant_excerpt
    quotes = []
    for component in (result or {}).get('components', []):
        gates = {g['chunk_id']: g for g in component['evidence_gates']}
        for hit in component['candidates']:
            gate = gates.get(hit['chunk_id'])
            if (not gate or set(gate['reasons']) - {'scoped_currentness_review_missing'}
                    or issue_for(hit) or verifier.check_candidate(hit, component['allowed_domain'])):
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
    generated = (explanation['status'] == 'generated' and explanation.get('citations_checked') and explanation.get('automated_support_checked')
                 or explanation['status'] == 'verified' and explanation.get('legal_support_verified'))
    if generated:
        response.update(kind='ai_explanation', heading='AI explanation', ai_generated=True)
    elif not result or route.get('routing_action') == 'clarify':
        follow = (packet.get('clarification_follow_up') or {}).get('question') or route.get('clarification_question') or (packet.get('normalization') or {}).get('clarification_question')
        response['paragraphs'] = ['I need one more detail to choose the right sources. This project covers selected Philippine private-sector employment and ordinary consumer-purchase concerns.']
        response['follow_up'] = follow or 'What happened, who was involved, and what would you like help with?'
    elif route.get('routing_action') == 'refer_out_of_scope':
        response.update(kind='referral', heading='Where this concern fits', paragraphs=[
            'This concern falls outside this project’s selected private-sector labor and ordinary consumer topics. The classifier is identifying a scope limit; it is not deciding whether you have legal rights or a valid complaint.',
            'Any assistance contacts listed below are recorded directory entries. Check with the agency about whether it handles your concern.'])
    else:
        quotes = eligible_quotes(verifier, result)
        response.update(kind='recorded_sources' if quotes else 'source_limit', heading='What I found', quotes=quotes)
        if quotes:
            response['heading'] = 'Recorded source passages'
            response['paragraphs'] = ['These passages were selected by local topic matching. They are source excerpts, not an explanation or a decision about your situation. Open each reference for its complete text, conditions and exceptions.']
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
            response['paragraphs'].append('The AI draft did not clear the source checks, so I’m showing the recorded material instead of treating that draft as reliable.')
        elif reason == 'source_review_required':
            response['paragraphs'].append('AI explanations are not configured in this running server. The local source response remains available.')
    if context:
        response['follow_up'] = context['follow_up']
        response['follow_up_options'] = [
            {'label': label, 'question_text': prefix + ' ' + question} for label, prefix in [
                ('Private company', 'Private employee ako.'), ('Government', 'Government employee ako.'),
                ('Household', 'Kasambahay ako.'), ('Overseas / OFW', 'OFW ako.'), ('Seafarer', 'Seafarer ako.')]]
    return response
