"""Known recorded-text discrepancies: exclude from generation, preserve originals.

This is an AI-inspected safety hold, not a legal/source-currentness approval.
The recorded IRR passage says 'worked'; DOLE/BWC's FAQ describes 'unworked'.
Compare page 12 (PDF page index 11) of the government-hosted BWC reference.
No reference text is added to the canonical corpus or sent to the provider.
"""

HOLIDAY_PROVISION='LAB_IRR_1989__rule_iv_holidays_with_pay__section_3'
ISSUES={HOLIDAY_PROVISION:{
    'kind':'recorded_wording_discrepancy',
    'recorded_parent_sha256':'fd053d94686fdaef138aeeed3c2d0a081e5cce450c373a6f7cec423742d2a900',
    'comparison_url':'https://cda.gov.ph/wp-content/uploads/2019/07/coopsday-DOLE-BWC-FAQs-on-Labor-Standards.pdf',
    'checked_on':'2026-10-19','independent_legal_review_completed':False,
    'message':'This passage has a worked/unworked wording discrepancy. It is excluded from AI explanations pending source review.'}}

# The stored second paragraph jumps from regular/casual status into an unrelated
# reinstatement/separation-pay clause. Preserve that record, but do not quote or
# paraphrase it as approved evidence. Other indexed editions remain searchable.
ISSUES['LAB_IRR_1989__article_280']={
    'kind':'recorded_text_continuity_issue',
    'checked_on':'2026-10-21','independent_legal_review_completed':False,
    'message':'This recorded employment-status passage has a discontinuous paragraph and is excluded from explanations pending source-text review.'}

# Its special scheduling sentence uses an unresolved "his choice" pronoun.
# Repeated generation changed the actor or omitted the monthly qualification.
# Preserve the complete source for inspection; do not approve its paraphrase.
RELIGIOUS_SCHEDULING_PROVISION='LAB_IRR_1989__rule_iii_weekly_rest_periods__section_4'
ISSUES[RELIGIOUS_SCHEDULING_PROVISION]={
    'kind':'recorded_interpretation_ambiguity',
    'recorded_parent_sha256':'d7896a283b0c5bfd86d8ecb5026f74b744470204ddd20dbf9bcaf1401f63090e',
    'checked_on':'2026-10-31','independent_legal_review_completed':False,
    'message':'This special religious-rest scheduling passage has an ambiguous choice/qualification. It is excluded from AI explanations pending interpretation review; its complete recorded text remains inspectable.'}

def issue_for(source):
    # Hold every chunk of the provision until an explicit reviewed resolution;
    # replacing its bytes cannot silently remove the restriction.
    return ISSUES.get(source.get('provision_id'))
