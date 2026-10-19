"""Transparent scope constraints from the project's taxonomy, never legal-answer rules.

These constraints are development code informed by error analysis. They are not
learned probabilities, independently validated labels, or final-test evidence.
"""
from __future__ import annotations
import re

EXCLUDED=[
 ('labor.seafarers',r'\bseaf[a-z]*r\b'),
 ('labor.ofw',r'\bofw\b|\boverseas\s+(?:employ\w*|recruit\w*|work\w*|job|contract)|\b(?:employ\w*|recruit\w*|work\w*)\s+(?:abroad|overseas)|\brecruitment\s+agency\b.{0,60}\bdeployment\b'),
 ('labor.government_employment',r'\b(?:government|govt|municipal|civil.service)\s+(?:employ\w*|work\w*|job)|\b(?:employ\w*|work\w*)\s+(?:by|for|at|in)\s+(?:a |the )?(?:government|municipal)|\bpublic\s+office\b.{0,60}\bcivil.service\b'),
 ('labor.kasambahay',r'\bkasambahay\b|\b(?:household|domestic)\s+(?:employ\w*|work\w*)'),
 ('labor.union_cba',r'\bcba\b|\bcollective.bargain\w*|\bunion\s+(?:election|representation|officer|dues|bargain\w*)'),
 ('labor.workers_compensation',r'\bdisability\b|\b(?:workers?|employees?).?\s+compensation\b|\b(?:workplace|work.related)\s+(?:injury|illness)\b.{0,65}\b(?:ec|compensation|benefits?)\b'),
 ('labor.occupational_safety',r'\b(?:osh|osha)\b|\boccupational\s+safety\b|\b(?:factory|workplace)\b.{0,45}\b(?:ventilation|chemical|compliance|safety.standard)|\bemployees?\b.{0,50}\bdangerous\s+chemicals?\b'),
 ('labor.retirement_pension',r'\bpension\b|\b(?:sss|gsis)\b|\bretirement\s+(?:pay|benefit|comput\w*)'),
 ('labor.pending_case',r'\bpending\b.{0,40}\b(?:case|nlrc|proceeding|court)|\b(?:case|proceeding)\b.{0,25}\bpending\b|\bnlrc\b.{0,40}\b(?:hearing|arguments?)\b'),
 ('labor.case_outcome_prediction',r'\b(?:will|can)\s+i\s+win\b|\bi\x27ll\s+win\b|\b(?:predict|chance\w*|odds|whether|sure)\b.{0,45}\b(?:win|success)'),
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
MINIMUM=re.compile(r'\b(?:minimum|minimun|min)\s+wage\b',re.I)
AMOUNT=re.compile(r'\b(?:exact|amount|rate|peso|magkano|how.much|today|current|ngayon\w*|mismo)\b',re.I)
LABOR=re.compile(r'\b(?:wage\w*|salar\w*|sahod|sweldo|pay\w*|paid|unpaid|unpayed|overtime|thirteenth|13th|holiday|rest.?day|break|shift|briefing|waiting.time|notice|probation\w*|redundan\w*|terminat\w*|dismiss\w*|resign\w*|fired|coe|contract|job.terms|final.pay)\b',re.I)
PRIVATE=re.compile(r'\b(?:private|pribado)\b',re.I)
RETAIL=re.compile(r'\b(?:retail\w*|seller|store|shop\w*|groc\w*|appliance|kettle|ketle|blender|rice.cooker|keyboard|folding.table|extension.cord|consumer.product|household.product|laundry|sukli|cashier|repair.service|online.platform)\b',re.I)
CONSUMER_ISSUE=re.compile(r'\b(?:warr?ant\w*|warant\w*|refund|repair|replac\w*|defect\w*|faulty|unsafe|buy|bought|purchase|sold|order|deliver\w*|sira|binili|nabili|sukli|paid|service|clothes|bayad|magbayad|charge\w*|fee|quote|price|advert\w*|demonstrat\w*|recalled|complaint|reklamo|transaction|coins|change|candy)\b',re.I)

def constraint(text):
    t=text.lower()
    for topic,pattern in PATTERNS:
        match=pattern.search(t)
        if match:
            # A negated category is not evidence of that category.
            preceding=t[max(0,match.start()-24):match.start()]
            if re.search(r'\b(?:not|hindi|never)\s+(?:(?:a|an|the|ako|sa|nila|niya|ko|namin)\s+){0,2}$',preceding):continue
            return ('excluded',topic)
    if MINIMUM.search(t) and AMOUNT.search(t):return ('excluded','labor.regional_minimum_wage_amounts')
    if re.search(r'\bsena\b',t):return ('labor','explicit_sena_procedure_context')
    if PRIVATE.search(t) and (LABOR.search(t) or re.search(r'\buniform\s+fee\b',t)) and re.search(r'\b(?:employ\w*|company|job|trabaho|workers?|workplace)\b',t):return ('labor','explicit_private_employment_context')
    if RETAIL.search(t) and CONSUMER_ISSUE.search(t):return ('consumer','explicit_ordinary_retail_context')
    # Service-quality defects belong to the ordinary consumer framework after
    # regulated-service exclusions above. A generic provider alone is insufficient.
    if re.search(r'\bservice\s+(?:provider|supplier)\b',t) and re.search(r'\b(?:defect\w*|flawed|faulty|poor.quality|improper)\s+(?:work|service\w*)\b',t):
        return ('consumer','explicit_service_quality_defect')
    return None
