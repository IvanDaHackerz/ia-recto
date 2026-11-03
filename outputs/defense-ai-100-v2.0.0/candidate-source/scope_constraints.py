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
 ('labor.government_employment',r'\b(?:government|govt|municipal)\s+(?:employ\w*|work\w*|job|salary|wage\w*)|\b(?:employ\w*|work\w*)\s+(?:by|for|at|in)\s+(?:a |the )?(?:government|municipal|city\s+hall)|\bempleyad[oa]\b.{0,45}\b(?:municipal|government|govt)\b|\bpublic\s+(?:school\s+teacher|hospital\s+(?:nurse|employee|worker))\b|\bcivil\s+service\b'),
 ('labor.kasambahay',r'\bkasambahay\b|\b(?:household|domestic)\s+(?:employ\w*|work\w*|helper|maid|nanny|housekeeper)\b|\blive[- ](?:in|out)\s+(?:helper|maid|nanny|housekeeper)\b|\b(?:helper|maid|nanny|housekeeper|yaya)\b.{0,65}\b(?:family.home|private.home|household|bahay\s+ng\s+(?:isang\s+)?pamilya)\b'),
 ('labor.union_cba',r'\bcba\b|\bcollective.bargain\w*|\bbargaining\s+unit\b|\bunion\b.{0,65}\brepresentation\b|\bunion\s+(?:election|representation|officer|dues|bargain\w*)'),
 ('labor.workers_compensation',r'\bdisability\b|\b(?:workers?|employees?).?\s+compensation\b|\b(?:workplace|work.related)\s+(?:injury|illness)\b.{0,65}\b(?:ec|compensation|benefits?)\b'),
 ('labor.occupational_safety',r'\b(?:osh|osha)\b|\boccupational\s+safety\b|\b(?:factory|workplace)\b.{0,45}\b(?:ventilation|chemical|compliance|safety.standard)|\bemployees?\b.{0,50}\bdangerous\s+chemicals?\b'),
 ('labor.retirement_pension',r'\bpension\b|\b(?:sss|gsis)\b|\bretirement\s+(?:pay|benefit|comput\w*)'),
 ('labor.pending_case',r'\bpending\b.{0,40}\b(?:case|nlrc|proceeding|court)|\b(?:case|proceeding)\b.{0,25}\bpending\b|\bnlrc\b.{0,40}\b(?:hearing|arguments?)\b'),
 ('labor.case_outcome_prediction',r'\b(?:will|can)\s+i\s+win\b|\bi\x27ll\s+win\b|\b(?:predict|chance\w*|odds|whether|sure)\b.{0,45}\b(?:win|success)|\bpredict\b.{0,50}\b(?:result|outcome|decision|appeal|case)\b|\b(?:sigurad\w*|masasabi|malaman)\b.{0,55}\b(?:mananalo|panalo)\b|\b(?:mananalo|panalo)\b.{0,45}\b(?:kaso|case|appeal)\b'),
 ('consumer.banking_credit',r'\bcredit.card\b|\b(?:loan|lending|banking)\b|\b(?:bank|bnko)\w*\b.{0,50}\b(?:fee|charge|frozen|freeze|account|interest|deduct\w*)'),
 ('consumer.insurance',r'\binsur\w*\b'),
 ('consumer.investments',r'\b(?:invest|invests|invested|investing|investments?|investors?|mag-invest|nag-invest|maginvest|naginvest)\b|\bsecurit(?:y|ies)\s+(?:broker|trading|account|complaint)'),
 ('consumer.telecommunications',r'\b(?:telecom\w*|telco)\b|\b(?:mobile|phone|internet|broadband)\s+(?:plan|provider|bill|subscription|service|network)|\b(?:mobile|phone)\b.{0,35}\b(?:plan|bill|data[ -](?:charge|plan))'),
 ('consumer.data_privacy',r'\bprivacy\b|\bpersonal\s+(?:data|information)\b|\b(?:post\w*|pinost|expos\w*|publish\w*|leak\w*|share\w*)\b[^.!?;\n]{0,50}\b(?:id|identity|address|phone.number|(?:my|our|personal|private|sensitive|customer|user)\s+(?:data|information))\b|\b(?:id|identity|address|data)\b[^.!?;\n]{0,35}\b(?:public|pinost|posted|exposed|leaked)|\b(?:inilabas|nilabas|ibinunyag|isinapubliko|ikinakalat|kinakalat|ibinahagi|ipinost)\b[^.!?;\n]{0,60}\b(?:address|tirahan|id|identity|numero|phone.number|data|information)\b[^.!?;\n]{0,55}\b(?:online|public\w*|facebook|social.media|walang\s+pahintulot|without\s+(?:consent|permission))\b'),
 ('consumer.medical_malpractice',r'\b(?:malpractice|doctor|physician|surgeon|patient|medical.negligence|medical.service|medical.care|medical.treatment|hospital)\b'),
 ('consumer.real_estate',r'\b(?:condo\w*|real.estate|housing.developer|housing.adjudication|subdivision|landlord|tenant)\b|\bdeveloper\b.{0,45}\b(?:house|turnover|layout|purchase|unit)'),
 ('consumer.transportation',r'\b(?:airline|flight|passenger|bus.operator|transport.operator|transport.regulat\w*)\b'),
 ('consumer.utility_billing',r'\b(?:water|electricity|electric)\b.{0,35}\b(?:bill|billing|utility|meter|provider)|\butility\s+(?:bill|provider|charge)'),
 ('consumer.criminal_online_fraud',r'\b(?:criminal|cyberfraud|cybercrime)\b|\b(?:fake|fraud\w*|scam\w*)\b.{0,65}\b(?:store|seller|page|investigation|police)|\b(?:seller|store|page)\b.{0,45}\b(?:disappear\w*|vanish\w*)'),
]
PATTERNS=[(topic,re.compile(pattern,re.I)) for topic,pattern in EXCLUDED]
# Local descriptions of the employment relationship, rather than a requirement
# that people know the taxonomy's English category name.
PUBLIC_EMPLOYMENT=re.compile(r'\b(?:empleyad[oa]|nagtatrabaho|nagtratrabaho|employee|worker|work|working|employed)\b.{0,25}\b(?:sa|ng|for|at|in|by)\s+(?:(?:isang|the|a|local)\s+){0,2}(?:munisipyo|munisipalidad|municipio|municipality|gobyerno|gobierno|barangay|city.hall|municipal.hall|lgu)\b',re.I)
HOUSEHOLD_EMPLOYMENT=re.compile(r'\b(?:stay|live)[ -](?:in|out)\s+(?:yaya|helper|maid|nanny|housekeeper)\b|\b(?:yaya|helper|maid|nanny|housekeeper)\b(?=\s+(?:ako|for|of|ng|sa|looking|caring|employed|working|hired|who|at)\b).{0,70}\b(?:family|pamilya|bahay\s+nila|bahay\s+niya)\b',re.I)
PATTERNS[2:2]=[('labor.government_employment',PUBLIC_EMPLOYMENT),('labor.kasambahay',HOUSEHOLD_EMPLOYMENT)]
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
MINIMUM=re.compile(r'\b(?:minimum|minimun|min)[\s-]+(?:daily[\s-]+)?wage\b',re.I)
AMOUNT=re.compile(r'\b(?:exact|amount|rate|peso|magkano|how.much|today|current|ngayon\w*|mismo)\b',re.I)
LABOR=re.compile(r'\b(?:wage\w*|salar\w*|sahod|sweldo|suweldo|pay\w*|paid|unpaid|unpayed|overtime|thirteenth|13th|holiday|rest.?day|day.off|break|shift|briefing|waiting.time|notice|due.process|tinanggal|probation\w*|redundan\w*|terminat\w*|dismiss\w*|resign\w*|fired|coe|contract|kontrata|job.terms|final.pay)\b',re.I)
PRIVATE=re.compile(r'\b(?:private|pribado)\b',re.I)
RETAIL=re.compile(r'\b(?:retail\w*|merchant|seller|salesperson|store|shop\w*|groc\w*|supermarket|mall|tindahan|appliance|kettle|ketle|blender|vacuum|electric.fan|phone|handset|rice.cooker|keyboard|folding.table|extension.cord|consumer.product|household.product|laundry|sukli|cashier|repair.service|online.(?:platform|business|shop|seller))\b',re.I)
CONSUMER_ISSUE=re.compile(r'\b(?:warr?ant\w*|warant\w*|refund|return\w*|shipping|wrong.(?:item|model|product)|repair|replac\w*|defect\w*|faulty|broken|cracked|unsafe|exposed.(?:live.)?wir(?:e|ing)|sparks|amoy\s+sunog|buy|bought|purchas\w*|sold|sell(?:s|ing)?|decept\w*|misrepresent\w*|passed.off|binenta|order|deliver\w*|sira|basag|bumili|bumibili|binili|nabili|kakabili|palitan|sukli|paid|service|clothes|bayad|magbayad|nagbayad|charge\w*|fee|quote|prices?|ads?|advert\w*|demonstrat\w*|recalled|complaint|reklamo|transaction|coins|change|candy)\b|\bayaw\s+(?:umandar|gumana)\b|\b(?:hindi|di)\s+(?:gumagana|umandar|umiinit)\b',re.I)

def employment_issue(text):
    """A work relationship plus a scoped issue, never pay/notice alone.

    This identifies general employment information, not private-sector status.
    Excluded worker categories still take precedence in constraint().
    """
    t=scope_text(text)
    actor=re.search(r'\b(?:employer|employee\w*|company|boss|manager|hr|payroll|kumpanya|trabaho|nagtatrabaho|nagtrabaho|job|staff|supervisor)\b|\b(?:i|we)\s+(?:work|worked|am\s+employed|are\s+employed)\b|\b(?:the\s+)?firm\b.{0,35}\b(?:hir\w*|employ\w*|contract\w*)\b',t)
    actor=actor or re.search(r'\bprivate[ -]sector\s+(?:employment|job|work|employee\w*|worker\w*|dismiss\w*|termination)\b',t)
    actor=actor or re.search(r'\b(?:private\s+)?(?:hotel|clinic|hospital|restaurant|factory|shop|store)\b.{0,45}\b(?:dismiss\w*|fired|hired)\b.{0,25}\b(?:worker|employee|receptionist|cashier|staff|me|us)\b',t)
    issue=LABOR.search(t) or re.search(r'\b(?:ot|deduct\w*|missing.cash|inventory.loss\w*|weekly.rest|conciliation|mediat\w*|working.time|working.hours|project[ .-](?:based|contracts?)|employment.status|regulari[sz]\w*|lampas\s+\d+\s+oras|tinanggal)\b',t)
    intrinsic=re.search(r'\b(?:wages?|salar\w*|sahod|sweldo|suweldo|thirteenth.month|13th.month|overtime|probation[ -]standards?|certificate.of.employment|final.pay)\b',t)
    project_worker=re.search(r'\bproject[ -]based\b.{0,25}\b(?:ako|employee|worker|contract)\b',t)
    required_waiting=re.search(r'\b(?:factory|warehouse|workplace)\b',t) and re.search(r'\b(?:pinapastay|pinapahintay|required\s+to\s+(?:stay|wait))\b',t)
    described_hours=actor and re.search(r'\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+hours?\b',t)
    workplace_duty=(PRIVATE.search(t) and re.search(r'\b(?:restaurant|office|warehouse|factory|workplace)\b',t)
                    and re.search(r'\b(?:require\w*|mandatory|duty)\b',t)
                    and re.search(r'\b(?:briefing|shift|waiting|meal.break|working.time|inspect\w*|equipment.check)\b',t))
    return bool(actor and issue or intrinsic or project_worker or required_waiting or workplace_duty or described_hours)


# Place names only identify an overseas context when linked to employment.
# A country in a product description or an employer's name is insufficient.
FOREIGN_WORKPLACE=re.compile(r'\b(?:employer|employment|job|work|working|employed)\s+(?:is\s+)?(?:in|at)\s+(?:the\s+)?(?:kuwait|saudi(?:\s+arabia)?|qatar|uae|dubai|abu\s+dhabi|bahrain|oman|singapore|hong\s+kong|taiwan|japan|korea|canada|australia|united\s+(?:states|kingdom)|usa|uk)\b',re.I)


def industry_is_employer(text, topic):
    """Recognize employer industry without swallowing an actual service claim."""
    if not employment_issue(text):return False
    relationship=re.search(r"\b(?:employed\s+by|work(?:ing)?\s+(?:for|at)|employee\s+(?:of|at)|my\s+employer\s+is|our\s+employer\s+is)\b",text)
    if not relationship:return False
    # Explicitly denied service concerns do not turn into service complaints.
    active=re.sub(r"\b(?:not|never)\s+(?:about\s+)?(?:(?:a|an|the|my|our)\s+)?(?:policy\s+claim|insurance\s+claim|bank\s+account|medical\s+treatment|(?:phone|water|electricity|utility)\s+bill|internet\s+(?:plan|bill))\b",'',text)
    service={
        'consumer.insurance':r'\b(?:policy|claim|coverage|premium|insured)\b',
        'consumer.banking_credit':r'\b(?:account|interest|loan|credit.card|deposit|bank.fee)\b',
        'consumer.medical_malpractice':r'\b(?:patient|treatment|surgery|malpractice|medical.negligence)\b',
        'consumer.telecommunications':r'\b(?:phone.bill|internet.plan|subscription|broadband|data.charge|mobile.plan)\b',
        'consumer.utility_billing':r'\b(?:my|our|home|household)\s+(?:water|electricity|electric|utility)\s+bill|\bmeter.reading|billing.error|double.bill',
        'consumer.transportation':r'\b(?:passenger|fare|ticket|booked|flight|trip|boarding|baggage|cancelled|canceled)\b',
        'consumer.real_estate':r'\b(?:unit|condominium|condo|turnover|installment|house.purchase|property.purchase|tenant|landlord|lease)\b',
    }[topic]
    return not re.search(service,active)

def employment_background(text):
    """An actor introduction has no independent service/product complaint.

    A hospital/insurer can be an employer. Mentioning the industry in a job
    introduction does not assert medical negligence or an insurance dispute.
    """
    t=scope_text(text)
    intro=re.search(r"^(?:i\s+(?:am|work|am employed)|i'm|my\s+(?:private\s+)?(?:company|employer)\s+(?:is|was)|(?:ofw|seaf\w*r|kasambahay|cashier|public.school.teacher)\s+ako)\b",t)
    intro=intro or re.fullmatch(r'sa\s+(?:private|pribado)\s+(?:factory|warehouse|office|restaurant|company|hotel|shop|farm)\s+ako',t)
    intro=intro or re.fullmatch(r'(?:former\s+)?(?:crew|staff|employee|worker)\s+ako\s+(?:sa|ng)\s+(?:private|pribado)\s+[\w -]+',t)
    intro=intro or re.fullmatch(r'sa\s+(?:private|pribado)\s+[\w -]+\s+ako\s+employed',t)
    intro=intro or re.fullmatch(r'my\s+(?:private\s+)?employer\s+gave\s+me\s+(?:a\s+)?gift\s+card',t)
    return bool(intro and not employment_issue(t) and not ISSUE_ACTION.search(t))

ISSUE_ACTION=re.compile(r'\b(?:refus\w*|denied|withheld|owe\w*|unpaid|not\s+paid|complaint|reklamo|dispute|defect\w*|sira|warranty|refund|bill\w*|charge\w*|leak\w*|posted|changed|sinunod|walang|incorrect|wrong|discrep\w*|hindi\s+tu?gma)\b',re.I)

def literal_concern_text(text):
    """Ignore quoted demonstration text only when explicitly introduced as such."""
    if re.search(r'\b(?:training|example|hypothetical|fictional|quoted|phrase|sample)\b',text,re.I):
        return re.sub(r'"[^"\n]*"|“[^”\n]*”|`[^`\n]*`', ' passage ', text)
    return text

def negated_scope_statement(text):
    """An explicit non-concern is background, not an excluded issue to learn."""
    return bool(re.fullmatch(r'bank\s+transfer\s+(?:is\s+(?:just|only)\s+(?:the|my|our)|lang\s+(?:yung|ang))\s+payment\s+method,?\s*(?:hindi\s+(?:bank|banking)\s+fees?\s+(?:ang|yung)\s+(?:reklamo|concern|issue)\s+ko|not\s+a\s+banking\s+(?:complaint|dispute))[.! ]*',text.strip(),re.I)
        or re.fullmatch(r'(?:this|it|my\s+(?:question|concern|issue))\s+is\s+not\s+(?:an?\s+)?(?:ordinary\s+)?(?:retail|consumer)\s+(?:purchase|transaction|issue|concern)[.! ]*',text.strip(),re.I)
        or re.fullmatch(r'(?:this|it|my\s+(?:question|concern|issue))\s+is\s+about\s+(?:employment|my\s+job|work),?\s+not\s+(?:(?:my|our|a|the)\s+){0,2}(?:(?:water|electricity|phone|internet|utility)\s+bill|insurance\s+claim|bank\s+account)[.! ]*',text.strip(),re.I)
        or re.fullmatch(r"(?:this|it|my (?:question|concern|case|issue))\s+(?:is\s+not|isn't|does\s+not\s+(?:concern|involve))\s+(?:about\s+)?(?:a\s+|an\s+)?(?:insurance|banking|bank|loan|government|privacy|criminal|medical|family)(?:\s+[a-z-]+){0,4}[.! ]*",text.strip(),re.I)
        or re.fullmatch(r'hindi\s+(?:ito|iyon|yan)\s+(?:(?:tungkol\s+)?sa\s+)?(?:insurance|banking|privacy|criminal|medical)(?:\s+[a-z-]+){0,5}[.! ]*',text.strip(),re.I)
        or re.fullmatch(r"(?:i|we)\s+(?:did\s+not|didn't|never)\s+(?:buy|purchase|order)\s+(?:(?:a|an|the|any)\s+)?(?:[a-z-]+\s+){0,3}(?:handset|phone|product|item|goods)[.! ]*",text.strip(),re.I))

def historical_background(text):
    """Explicit historical/unrelated facts, without a request about that event."""
    historic=re.search(r'\b(?:\d+|one|two|three|ten|many|several)\s+years?\s+ago\b|\bunrelated\b',text,re.I)
    request=re.search(r'\b(?:what|how|why|claim|compensation|sue|complaint|concern|issue|help|need|gusto|paano|ano)\b',text,re.I)
    return bool(historic and not request)

def constraint(text):
    t=scope_text(literal_concern_text(text))
    if negated_scope_statement(t):return None
    # Public employment does not require the English noun "employee" directly
    # after "government". Keep this limited to a job/pay relationship.
    if (any(not re.search(r'\b(?:not|hindi|never)\s+$',t[max(0,m.start()-20):m.start()]) for m in re.finditer(r'\b(?:government|govt|municipal)\b',t))
            and re.search(r'\b(?:clerk|overtime|pay|salary|wages?|employment)\b',t)):
        return ('excluded','labor.government_employment')
    if re.search(r'\b(?:factory|workplace)\b.{0,100}\b(?:ventilation|chemical.exposure|safety.compliance)\b',t):
        return ('excluded','labor.occupational_safety')
    if re.search(r'\bpersonal[ -]data\b',t) and re.search(r'\b(?:breach|complaint|posted|exposed|privacy)\b',t):
        return ('excluded','consumer.data_privacy')
    if re.search(r'\b(?:transportation.regulator|family[ -]court)\b',t):
        return ('excluded','consumer.transportation' if 'transportation' in t else 'outside.family')
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
    if FOREIGN_WORKPLACE.search(t):return ('excluded','labor.ofw')
    for topic,pattern in PATTERNS:
        match=pattern.search(t)
        if match:
            # A negated category is not evidence of that category.
            preceding=t[max(0,match.start()-24):match.start()]
            if re.search(r'\b(?:not|hindi|never)\s+(?:(?:a|an|the|ako|sa|nila|niya|ko|namin)\s+){0,2}$',preceding):continue
            if topic=='consumer.telecommunications' and re.search(r'\b(?:bought|purchas\w*|binili)\b',t) and re.search(r'\b(?:not|hindi)\s+(?:(?:a|an|the|yung)\s+)?(?:service|phone|mobile|internet)\s+plan\b',t) and not re.search(r'\b(?:bill\w*|subscription|provider|telco)\b',t):continue
            # An industry noun can describe an employer, rather than a service
            # dispute. Keep separate claims, policies and financial issues.
            if topic in {'consumer.insurance','consumer.medical_malpractice','consumer.banking_credit','consumer.telecommunications','consumer.utility_billing','consumer.transportation','consumer.real_estate'} and industry_is_employer(t,topic):continue
            if topic=='consumer.telecommunications' and employment_issue(t) and re.search(r'\b(?:not|never)\s+(?:about\s+)?(?:(?:my|our|a|the)\s+)?(?:phone|internet)\s+bill\b',t):continue
            if topic=='consumer.utility_billing' and RETAIL.search(t) and re.search(r'\b(?:sold|bought|purchas\w*)\b',t) and not re.search(r'\b(?:bill\w*|utility|provider|reading)\b',t):continue
            return ('excluded',topic)
    if MINIMUM.search(t) and AMOUNT.search(t):return ('excluded','labor.regional_minimum_wage_amounts')
    if MINIMUM.search(t):return ('labor','general_minimum_wage_framework')
    if re.search(r'\bconsumer.act\b',t) and re.search(r'\b(?:framework|policy|objectives?|interests?|protections?)\b',t):
        return ('consumer','explicit_consumer_framework')
    if re.search(r'\bsena\b',t):return ('labor','explicit_sena_procedure_context')
    if employment_issue(t):return ('labor','employment_relationship_and_scoped_issue')
    if PRIVATE.search(t) and (LABOR.search(t) or re.search(r'\buniform\s+fee\b',t)) and re.search(r'\b(?:employ\w*|company|job|trabaho|workers?|workplace)\b',t):return ('labor','explicit_private_employment_context')
    # Work duties/schedules plus a private workplace establish employment;
    # the word "private shop" by itself still does not establish it.
    private_workplace=PRIVATE.search(t) and re.search(r'\b(?:office|warehouse|restaurant|shop|store|factory|bodega)\b',t)
    work_duty=re.search(r'\b(?:meal\s+break|briefing|after\s+shift)\b',t) and re.search(r'\b(?:duty|required|require\w*|shift|trabaho|work\w*)\b',t)
    own_rest_day=re.search(r'\brest\s+day\b.{0,12}\b(?:ko|namin|my|our)\b|\b(?:my|our)\b.{0,15}\brest\s+day\b',t)
    changed_rest_day=own_rest_day and re.search(r'\b(?:pinalitan|changed|assigned|scheduled|shifted)\b',t)
    if private_workplace and (work_duty or changed_rest_day) and not re.search(r'\b(?:customer|diner|buyer)\b',t):return ('labor','explicit_private_workplace_duty')
    # The complete product-label concept is unambiguous even when a nearby
    # compressed token (e.g. product/predict) cannot be safely expanded.
    if re.search(r'\bnet\s+quantity\b',t) and re.search(r'\blabel(?:ing|ling)?\b',t):
        return ('consumer','explicit_product_label_quantity')
    if (private_workplace and re.search(r'\b(?:dismiss\w*|fired|rest.day|day.off|overtime|ot)\b',t)
            and not re.search(r'\b(?:buy|bought|purchas\w*|binili|nabili|kakabili)\b',t)):
        return ('labor','explicit_private_workplace_duty')
    if RETAIL.search(t) and (CONSUMER_ISSUE.search(t) or re.search(r'\b(?:laundry|repair|cleaning)\b.{0,40}\b(?:lost|damaged|ruined)\b',t)):return ('consumer','explicit_ordinary_retail_context')
    if re.search(r'\bnagpa[ -](?:laundry|repair)\b',t):return ('consumer','explicit_paid_service_context')
    if re.search(r'\b(?:sold\s+me|bought\s+from|purchased\s+from|binenta|display\s+unit)\b',t) and CONSUMER_ISSUE.search(t):
        return ('consumer','explicit_product_sale_context')
    if re.search(r'\b(?:bought|purchased|binili|nabili|kakabili)\b',t) and re.search(r'\b(?:defect\w*|broken|faulty|sira|delikado|matutulis|unsafe|overheat\w*|scorch\w*|not.work\w*|ayaw\s+(?:umandar|gumana))\b',t):
        return ('consumer','purchased_product_defect_or_safety')
    # Service-quality defects belong to the ordinary consumer framework after
    # regulated-service exclusions above. A generic provider alone is insufficient.
    if re.search(r'\bservice\s+(?:provider|supplier)\b',t) and re.search(r'\b(?:defect\w*|flawed|faulty|poor.quality|improper)\s+(?:work|service\w*)\b',t):
        return ('consumer','explicit_service_quality_defect')
    return None
