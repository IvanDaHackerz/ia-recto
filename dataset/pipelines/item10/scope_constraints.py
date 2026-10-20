"""Transparent scope constraints from the project's taxonomy, never legal-answer rules.

These constraints are development code informed by error analysis. They are not
learned probabilities, independently validated labels, or final-test evidence.
"""
from __future__ import annotations
import re
import unicodedata

def scope_text(text):
    """Small declared spelling aliases for rule matching; retain original input."""
    from typing_repair import matching_text
    t=matching_text(unicodedata.normalize('NFKC',text)).casefold()
    aliases={'goverment':'government','governmnt':'government','salry':'salary',
        'salries':'salaries','employe':'employee','employr':'employer',
        'servce':'service','delayd':'delayed','mncipal':'municipal','pnson':'pension'}
    return re.sub(r'\b(?:'+ '|'.join(aliases) +r')\b',lambda m:aliases[m.group()],t)

EXCLUDED=[
 ('labor.seafarers',r'\bseaf[a-z]*r\b'),
 ('labor.ofw',r'\bofw\b|\boverseas\s+(?:employ\w*|recruit\w*|work\w*|job|contract)|\b(?:employ\w*|recruit\w*|work\w*)\s+(?:abroad|overseas)|\brecruitment\s+agency\b.{0,60}\bdeployment\b'),
 ('labor.government_employment',r'\b(?:government|govt|municipal)\s+(?:employ\w*|work\w*|job)|\b(?:employ\w*|work\w*)\s+(?:by|for|at|in)\s+(?:a |the )?(?:government|municipal|city\s+hall)|\bempleyad[oa]\b.{0,45}\b(?:municipal|government|govt)\b|\bcivil\s+service\b'),
 ('labor.kasambahay',r'\bkasambahay\b|\b(?:household|domestic)\s+(?:employ\w*|work\w*)'),
 ('labor.union_cba',r'\bcba\b|\bcollective.bargain\w*|\bbargaining\s+unit\b|\bunion\b.{0,65}\brepresentation\b|\bunion\s+(?:election|representation|officer|dues|bargain\w*)'),
 ('labor.workers_compensation',r'\bdisability\b|\b(?:workers?|employees?).?\s+compensation\b|\b(?:workplace|work.related)\s+(?:injury|illness)\b.{0,65}\b(?:ec|compensation|benefits?)\b'),
 ('labor.occupational_safety',r'\b(?:osh|osha)\b|\boccupational\s+safety\b|\b(?:factory|workplace)\b.{0,45}\b(?:ventilation|chemical|compliance|safety.standard)|\bemployees?\b.{0,50}\bdangerous\s+chemicals?\b'),
 ('labor.retirement_pension',r'\bpension\b|\b(?:sss|gsis)\b|\bretirement\s+(?:pay|benefit|comput\w*)'),
 ('labor.pending_case',r'\bpending\b.{0,40}\b(?:case|nlrc|proceeding|court)|\b(?:case|proceeding)\b.{0,25}\bpending\b|\bnlrc\b.{0,40}\b(?:hearing|arguments?)\b'),
 ('labor.case_outcome_prediction',r'\b(?:will|can)\s+i\s+win\b|\bi\x27ll\s+win\b|\b(?:predict|chance\w*|odds|whether|sure)\b.{0,45}\b(?:win|success)|\bpredict\b.{0,50}\b(?:result|outcome|decision|appeal|case)\b|\b(?:sigurad\w*|masasabi|malaman)\b.{0,55}\b(?:mananalo|panalo)\b|\b(?:mananalo|panalo)\b.{0,45}\b(?:kaso|case|appeal)\b'),
 ('consumer.banking_credit',r'\bcredit.card\b|\b(?:loan|lending|banking)\b|\b(?:bank|bnko)\w*\b.{0,50}\b(?:fee|charge|frozen|freeze|account|interest|deduct\w*)'),
 ('consumer.insurance',r'\binsur\w*\b'),
 ('consumer.investments',r'\b(?:invest|invests|invested|investing|investments?|investors?|mag-invest|nag-invest|maginvest|naginvest)\b|\bsecurit(?:y|ies)\s+(?:broker|trading|account|complaint)'),
 ('consumer.telecommunications',r'\b(?:telecom\w*|telco)\b|\b(?:mobile|phone|internet|broadband)\s+(?:plan|provider|bill|subscription|service)|\b(?:mobile|phone)\b.{0,35}\b(?:plan|bill|data.charge)'),
 ('consumer.data_privacy',r'\bprivacy\b|\bpersonal\s+(?:data|information)\b|\b(?:post\w*|pinost|expos\w*|publish\w*|leak\w*|share\w*)\b.{0,50}\b(?:id|identity|address|phone.number|data|information)\b|\b(?:id|identity|address|data)\b.{0,35}\b(?:public|pinost|posted|exposed|leaked)|\b(?:inilabas|nilabas|ibinunyag|isinapubliko|ikinakalat|kinakalat|ibinahagi|ipinost)\b.{0,60}\b(?:address|tirahan|id|identity|numero|phone.number|data|information)\b.{0,55}\b(?:online|public\w*|facebook|social.media|walang\s+pahintulot|without\s+(?:consent|permission))\b'),
 ('consumer.medical_malpractice',r'\b(?:malpractice|doctor|physician|surgeon|patient|medical.negligence|medical.service|medical.care|medical.treatment|hospital)\b'),
 ('consumer.real_estate',r'\b(?:condo\w*|real.estate|housing.developer|housing.adjudication|subdivision|landlord|tenant)\b|\bdeveloper\b.{0,45}\b(?:house|turnover|layout|purchase|unit)'),
 ('consumer.transportation',r'\b(?:airline|flight|passenger|bus.operator|transport.operator|transport.regulat\w*)\b'),
 ('consumer.utility_billing',r'\b(?:water|electricity|electric)\b.{0,35}\b(?:bill|billing|utility|meter|provider)|\butility\s+(?:bill|provider|charge)'),
 ('consumer.criminal_online_fraud',r'\b(?:criminal|cyberfraud|cybercrime)\b|\b(?:fake|fraud\w*|scam\w*)\b.{0,65}\b(?:store|seller|page|investigation|police)|\b(?:seller|store|page)\b.{0,45}\b(?:disappear\w*|vanish\w*)'),
]
PATTERNS=[(topic,re.compile(pattern,re.I)) for topic,pattern in EXCLUDED]
# Explicit concerns beyond the legal MVP. Background employment/payment words
# do not turn a reported assault, family matter or recipe into a wage claim.
OUTSIDE_PATTERNS=[
 ('outside.personal_safety',r'\b(?:i|we|he|she|my friend)\s+(?:also\s+)?(?:got|was|were|am being|are being|is being|have been|had been)\s+(?:stabbed|shot|assaulted|robbed|attacked)\b|\b(?:someone|stranger|employer|boss)\s+(?:stabbed|shot|robbed|attacked)\s+(?:me|us)\b|\b(?:sinaksak|nasaksak|binaril|binugbog|hinoldap)\s+(?:ako|kami|siya)\b|\bmay\s+nanaksak\s+sa\s+(?:akin|amin)\b|\b(?:threaten\w*\s+to\s+(?:stab|shoot|kill|hurt)|kill|hurt)\s+(?:me|us)\b'),
 ('outside.theft',r'\b(?:someone|stranger|neighbor)\s+(?:also\s+)?stole\s+my\b|\bmy\s+(?:phone|wallet|bag|car|bicycle)\s+(?:was|got)\s+stolen\b|\b(?:nanakaw|ninakaw)\b'),
 ('outside.family',r'\b(?:divorce|annulment|inheritance|probate)\b|\bcustody\b.{0,30}\b(?:child|children|anak)\b|\b(?:child|children|anak)\b.{0,30}\bcustody\b'),
 ('outside.general_information',r'\bweather\b|\brecipe\b|\b(?:how\s+(?:do|can|should)\s+(?:i|we)|help\s+me)\s+(?:cook|bake)\b|\b(?:basketball|football|soccer)\s+(?:game|score|match)\b|\b(?:homework|algebra)\b|\bmy\s+(?:dog|cat|pet)\s+(?:died|is sick)\b'),
 ('outside.personal_travel',r'\bvisa\b.{0,45}\b(?:vacation|touris\w*|holiday\s+trip)\b'),
 ('outside.programming',r'\b(?:write|debug|implement|explain)\b.{0,45}\b(?:python|javascript|sql|programming|source.code|algorithm)\b'),
]
MINIMUM=re.compile(r'\b(?:minimum|minimun|min)\s+wage\b',re.I)
AMOUNT=re.compile(r'\b(?:exact|amount|rate|peso|magkano|how.much|today|current|ngayon\w*|mismo)\b',re.I)
LABOR=re.compile(r'\b(?:wage\w*|salar\w*|sahod|sweldo|suweldo|pay\w*|paid|unpaid|unpayed|overtime|thirteenth|13th|holiday|rest.?day|day.off|break|shift|briefing|waiting.time|notice|probation\w*|redundan\w*|terminat\w*|dismiss\w*|resign\w*|fired|coe|contract|kontrata|job.terms|final.pay)\b',re.I)
PRIVATE=re.compile(r'\b(?:private|pribado)\b',re.I)
RETAIL=re.compile(r'\b(?:retail\w*|seller|store|shop\w*|groc\w*|supermarket|mall|tindahan|appliance|kettle|ketle|blender|vacuum|electric.fan|phone|handset|rice.cooker|keyboard|folding.table|extension.cord|consumer.product|household.product|laundry|sukli|cashier|repair.service|online.platform)\b',re.I)
CONSUMER_ISSUE=re.compile(r'\b(?:warr?ant\w*|warant\w*|refund|repair|replac\w*|defect\w*|faulty|unsafe|buy|bought|purchas\w*|sold|order|deliver\w*|sira|binili|nabili|kakabili|sukli|paid|service|clothes|bayad|magbayad|charge\w*|fee|quote|price|ads|advert\w*|demonstrat\w*|recalled|complaint|reklamo|transaction|coins|change|candy)\b|\bayaw\s+(?:umandar|gumana)\b',re.I)

def employment_issue(text):
    """A work relationship plus a scoped issue, never pay/notice alone.

    This identifies general employment information, not private-sector status.
    Excluded worker categories still take precedence in constraint().
    """
    t=scope_text(text)
    actor=re.search(r'\b(?:employer|company|boss|hr|kumpanya|trabaho|job|staff|supervisor)\b|\b(?:i|we|employees?)\s+(?:work|worked|are\s+required|must|have\s+to)\b',t)
    issue=LABOR.search(t) or re.search(r'\b(?:project.based|regulari[sz]\w*|lampas\s+\d+\s+oras|tinanggal)\b',t)
    intrinsic=re.search(r'\b(?:wages?|salar\w*|sahod|sweldo|suweldo|thirteenth.month|13th.month|overtime|certificate.of.employment|final.pay)\b',t)
    return bool(actor and issue or intrinsic)

def employment_background(text):
    """An actor introduction has no independent service/product complaint.

    A hospital/insurer can be an employer. Mentioning the industry in a job
    introduction does not assert medical negligence or an insurance dispute.
    """
    t=scope_text(text)
    intro=re.search(r"^(?:i\s+(?:am|work|am employed)|i'm|my\s+(?:private\s+)?(?:company|employer)|(?:ofw|seaf\w*r|kasambahay)\s+ako)\b",t)
    return bool(intro and not employment_issue(t) and not ISSUE_ACTION.search(t))

ISSUE_ACTION=re.compile(r'\b(?:refus\w*|denied|withheld|owe\w*|unpaid|not\s+paid|complaint|reklamo|dispute|defect\w*|sira|warranty|refund|bill\w*|charge\w*|leak\w*|posted|changed|sinunod|walang)\b',re.I)

def literal_concern_text(text):
    """Ignore quoted demonstration text only when explicitly introduced as such."""
    if re.search(r'\b(?:training|example|hypothetical|fictional|quoted|phrase|sample)\b',text,re.I):
        return re.sub(r'"[^"\n]*"|“[^”\n]*”|`[^`\n]*`', ' passage ', text)
    return text

def negated_scope_statement(text):
    """An explicit non-concern is background, not an excluded issue to learn."""
    return bool(re.fullmatch(r"(?:this|it|my (?:question|concern|case|issue))\s+(?:is\s+not|isn't|does\s+not\s+(?:concern|involve))\s+(?:about\s+)?(?:a\s+|an\s+)?(?:insurance|banking|bank|loan|government|privacy|criminal|medical|family)(?:\s+[a-z-]+){0,4}[.! ]*",text.strip(),re.I)
        or re.fullmatch(r"(?:i|we)\s+(?:did\s+not|didn't|never)\s+(?:buy|purchase|order)\s+(?:(?:a|an|the|any)\s+)?(?:[a-z-]+\s+){0,3}(?:handset|phone|product|item|goods)[.! ]*",text.strip(),re.I))

def historical_background(text):
    """Explicit historical/unrelated facts, without a request about that event."""
    historic=re.search(r'\b(?:\d+|one|two|three|ten|many|several)\s+years?\s+ago\b|\bunrelated\b',text,re.I)
    request=re.search(r'\b(?:what|how|why|claim|compensation|sue|complaint|concern|issue|help|need|gusto|paano|ano)\b',text,re.I)
    return bool(historic and not request)

def constraint(text):
    t=scope_text(literal_concern_text(text))
    if negated_scope_statement(t):return None
    # General-information vocabulary is not the intent of an otherwise explicit
    # wage/product complaint (e.g. weather radio, damaged recipe book).
    complaint=bool((PRIVATE.search(t) and LABOR.search(t) and re.search(r'\b(?:employ\w*|company|restaurant|work\w*|job)\b',t))
        or (RETAIL.search(t) and re.search(r'\b(?:refund|replac\w*|defect\w*|damaged|faulty|unsafe|warr?ant\w*|deduct\w*|sukli|overcharg\w*|price|charge\w*)\b',t)))
    for topic,pattern in OUTSIDE_PATTERNS:
        if topic=='outside.general_information' and complaint:continue
        for match in re.finditer(pattern,t,re.I):
            prefix=t[max(0,match.start()-20):match.start()]
            if re.search(r'\b(?:not|never|hindi)\s+$',prefix):continue
            return ('excluded',topic)
    if re.search(r'\b(?:delet\w*|remov\w*|retention|retain\w*|kept)\b.{0,45}\b(?:id\s+(?:document|photo|copy|card)|personal\s+(?:data|information)|home\s+address)\b',t):
        return ('excluded','consumer.data_privacy')
    for topic,pattern in PATTERNS:
        match=pattern.search(t)
        if match:
            # A negated category is not evidence of that category.
            preceding=t[max(0,match.start()-24):match.start()]
            if re.search(r'\b(?:not|hindi|never)\s+(?:(?:a|an|the|ako|sa|nila|niya|ko|namin)\s+){0,2}$',preceding):continue
            if topic=='consumer.telecommunications' and re.search(r'\b(?:bought|purchas\w*|binili)\b',t) and re.search(r'\b(?:not|hindi)\s+(?:(?:a|an|the|yung)\s+)?(?:service|phone|mobile|internet)\s+plan\b',t) and not re.search(r'\b(?:bill\w*|subscription|provider|telco)\b',t):continue
            # An industry noun can describe an employer, rather than a service
            # dispute. Keep separate claims, policies and financial issues.
            if topic in {'consumer.insurance','consumer.medical_malpractice','consumer.banking_credit'} and employment_issue(t):
                intro=re.search(r'\b(?:my|our)\s+employer\s+is\s+(?:a|an|the)\s+$',preceding)
                if intro and not re.search(r'\b(?:claim|coverage|policy|patient|treatment|account|interest|loan|fee|charge\w*)\b',t[match.end():]):continue
            if topic=='consumer.utility_billing' and RETAIL.search(t) and re.search(r'\b(?:sold|bought|purchas\w*)\b',t) and not re.search(r'\b(?:bill\w*|utility|provider|reading)\b',t):continue
            return ('excluded',topic)
    if MINIMUM.search(t) and AMOUNT.search(t):return ('excluded','labor.regional_minimum_wage_amounts')
    if MINIMUM.search(t):return ('labor','general_minimum_wage_framework')
    if re.search(r'\bsena\b',t):return ('labor','explicit_sena_procedure_context')
    if employment_issue(t):return ('labor','employment_relationship_and_scoped_issue')
    if PRIVATE.search(t) and (LABOR.search(t) or re.search(r'\buniform\s+fee\b',t)) and re.search(r'\b(?:employ\w*|company|job|trabaho|workers?|workplace)\b',t):return ('labor','explicit_private_employment_context')
    # Work duties/schedules plus a private workplace establish employment;
    # the word "private shop" by itself still does not establish it.
    private_workplace=PRIVATE.search(t) and re.search(r'\b(?:office|warehouse|restaurant|shop)\b',t)
    work_duty=re.search(r'\b(?:meal\s+break|briefing|after\s+shift)\b',t) and re.search(r'\b(?:duty|required|require\w*|shift|trabaho|work\w*)\b',t)
    own_rest_day=re.search(r'\brest\s+day\b.{0,12}\b(?:ko|namin|my|our)\b|\b(?:my|our)\b.{0,15}\brest\s+day\b',t)
    changed_rest_day=own_rest_day and re.search(r'\b(?:pinalitan|changed|assigned|scheduled|shifted)\b',t)
    if private_workplace and (work_duty or changed_rest_day) and not re.search(r'\b(?:customer|diner|buyer)\b',t):return ('labor','explicit_private_workplace_duty')
    # The complete product-label concept is unambiguous even when a nearby
    # compressed token (e.g. product/predict) cannot be safely expanded.
    if re.search(r'\bnet\s+quantity\b',t) and re.search(r'\blabel(?:ing|ling)?\b',t):
        return ('consumer','explicit_product_label_quantity')
    if RETAIL.search(t) and CONSUMER_ISSUE.search(t):return ('consumer','explicit_ordinary_retail_context')
    if re.search(r'\b(?:bought|purchased|binili|nabili|kakabili)\b',t) and re.search(r'\b(?:defect\w*|broken|faulty|sira|delikado|matutulis|unsafe|not.work\w*|ayaw\s+(?:umandar|gumana))\b',t):
        return ('consumer','purchased_product_defect_or_safety')
    # Service-quality defects belong to the ordinary consumer framework after
    # regulated-service exclusions above. A generic provider alone is insufficient.
    if re.search(r'\bservice\s+(?:provider|supplier)\b',t) and re.search(r'\b(?:defect\w*|flawed|faulty|poor.quality|improper)\s+(?:work|service\w*)\b',t):
        return ('consumer','explicit_service_quality_defect')
    return None
