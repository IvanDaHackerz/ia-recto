"""Pure local query/source concepts; no models, IDs, network or legal claims."""
import re,unicodedata

STOP=set('a an the of to and or in on at for from with by is are was be been this that it my i me we our you your ang ng sa mga ako ko po ba yung at na ay may'.split())
CONCEPTS=[
 (r'\b(?:sukli|shortchang\w*)\b','change'),
 (r'\b(?:labels?|labeling|labelling)\b','label'),
 (r'\b(?:short\s+(?:hours|workday)|kulang\s+(?:ang\s+)?oras|undertime)\b','undertime'),
 (r'\b(?:gaano\s+kadalas|how\s+often|frequency|frequently|regularity)\b','frequency'),
 (r'\b(?:sahod|sweldo|suweldo|salary|salaries|wages?)\b','wage'),
 (r'\b(?:ibigay|bigay|bayad|pagbabayad|paid|pay|payments?|paying)\b','payment'),
 (r'\b(?:lawyers?|attorneys?)\b','lawyer'),
 (r'\b(?:agents?)\b','agent'),
 (r'\b(?:representatives?|representing|represent)\b','representative'),
 (r'\b(?:pagharap|appearance|appearing)\b','appearance'),
 (r'\b(?:sena|conciliation.mediation)\b','conciliation'),
 (r'\b(?:palpak|flawed|faulty|defective|imperfections?)\b','defect'),
 (r'\b(?:redo|reperformance|reexecution)\b','reperformance'),
 (r'\b(?:refunds?|reimbursements?)\b','refund'),
 (r'\b(?:bawas|reductions?)\b','reduction'),
 (r'\b(?:presyo|prices?)\b','price'),
 (r'\b(?:services?)\b','service'),
 (r'\b(?:employers?)\b','employer'),
 (r'\b(?:employees?)\b','employee'),
 (r'\b(?:working|worked|works|work)\b','work'),
 (r'\b(?:rules?)\b','rule'),
]

def tokens(text):
    # Symmetric source/query glossary. Disclosed development preprocessing.
    text=unicodedata.normalize('NFKC',text).casefold()
    for pattern,replacement in CONCEPTS:text=re.sub(pattern,replacement,text)
    return [w for w in re.findall(r'[^\W_]+',text) if w not in STOP]

# Transparent, taxonomy-level relevance features. These are query concepts,
# never expected provision IDs or statements that a source proves entitlement.
# Heading matches outrank incidental words deep in unrelated provisions.
FACETS = [
 ('labor',r'\b(?:payroll\w*|wage.records?|payslip.{0,30}(?:contents?|information|records?)|(?:what|which).{0,25}(?:payroll|payslip))\b',r'\b(?:payroll\w*|payslip\w*|records?)\b','payroll records'),
 ('labor',r'\b(?:confidential\w*|video.record\w*)\b',r'\b(?:confidential\w*|recording)\b','confidential proceedings recording'),
 ('labor',r'\b(?:lawyers?|agents?|representativ\w*|pagharap)\b',r'\b(?:appearance|representation|representative)\b','appearance lawyer agent representative'),
 ('consumer',r'\binternal.{0,15}(?:complaint|redress)\b',r'\b(?:exhaustion|internal.{0,15}(?:complaint|redress))\b','internal redress mechanism'),
 ('labor',r'\b(?:payday|wages?|salar\w*|sahod|sweldo|suweldo)\b',r'\b(?:time.of.payment|payment.of.wages|wage.payment|direct.payment|manner.of.wage|wages?)\b','time payment wages'),
 ('labor',r'\b(?:deduct\w*|bawas|kinakaltas|kaltas)\b',r'\b(?:deduct\w*|withholding|prohibition.regarding.wages)\b','wage deductions withholding'),
 ('labor',r'\b(?:store.vouchers?|pays?.{0,12}(?:vouchers?|instead.of.money)|legal.tender)\b',r'\b(?:form.of.payment|legal.tender|prohibited.forms|payment.of.wages)\b','wages legal tender form payment'),
 ('labor',r'\b(?:working.time|working.hours|hours.of.work|clock.in|clock-in|required.waiting|equipment.check|briefing|meal.break|pinapastay|pinapahintay|naghihintay)\b',r'\b(?:hours.worked|hours.of.work|working.hours|compensable.hours|rest.periods)\b','hours worked compensable'),
 ('labor',r'\b(?:overtime|lampas.{0,15}shift|after.{0,12}eight.hours|work(?:ing)?.{0,12}(?:nine|ten|eleven|twelve|9|10|11|12).hours|extra.(?:time|hours).{0,25}(?:paid|pay|compensat\w*))\b',r'\bovertime\b','overtime additional compensation ordinary'),
 ('labor',r'\b(?:rest.day|weekly.rest|day.off|weekly.pahinga|walang.day.off)\b',r'\b(?:weekly.rest|rest.day|rest.period|weekly.day)\b','weekly rest day'),
 ('labor',r'\b(?:holiday|christmas|pasko|regular.holiday)\b',r'\b(?:holiday.pay|holidays.with.pay|right.to.holiday|regular.holiday)\b','holiday pay'),
 ('labor',r'\b(?:13th|thirteenth)\b',r'\b(?:13th|thirteenth)\b','thirteenth month pay'),
 ('labor',r'\b(?:project.contract|project.based|employment.status|regulari[sz]\w*|probation\w*|employment.contract)\b',r'\b(?:regular.and.casual|probation\w*|employment.contract|employment.agreement)\b','regular casual employment status'),
 ('labor',r'\b(?:final.pay|coe|certificate.of.employment|employment.certificates?)\b',r'\b(?:final.pay|certificate.of.employment|employment.certificates?)\b','final pay certificate employment'),
 ('labor',r'\b(?:dismiss\w*|terminat\w*|fired|tinanggal|removed.{0,20}roster|security.of.tenure)\b',r'\b(?:termination|dismissal|notice|due.process|security.of.tenure)\b','termination notice employer'),
 ('labor',r'\b(?:sena|conciliation|labor.complaint|dole.{0,15}help)\b',r'\b(?:sena|conciliation|mediation|request.for.assistance)\b','conciliation request assistance'),
 ('consumer',r'\b(?:warrant\w*|garantiya|guarant\w*)\b',r'\b(?:warrant\w*|guarant\w*)\b','warranty warranties'),
 ('consumer',r'\b(?:defect\w*|faulty|broken|cracked|leaks?|leaking|sira|basag|not.work\w*|stopped.(?:working|switching.on)|ayaw.gumana|(?:di|hindi).(?:umiinit|gumagana|umandar))\b',r'\b(?:defect\w*|imperfection)\b','defective product imperfection'),
 ('consumer',r'\b(?:repair|refund|replace\w*|palitan|ibalik.{0,12}bayad)\b',r'\b(?:repair|imperfection|warrant\w*|refund|replacement)\b','repair imperfection refund replacement'),
 ('consumer',r'\b(?:decept\w*|unfair|unconscionable|(?:secondhand|refurbished|used).{0,35}brand.new|display.unit.{0,25}(?:brand.new|bilang.bago)|hid.{0,25}repair|(?:hid|hidden|undisclosed).{0,35}(?:fee|cost|charge|condition)|(?:fee|charge).{0,35}after.i.had.already.paid|passed.off)\b',r'\b(?:decept\w*|unfair|unconscionable)\b','deceptive unfair sales practices'),
 ('consumer',r'\b(?:advert\w*|misleading|ads)\b',r'\b(?:advert\w*|misleading)\b','misleading advertisement'),
 ('consumer',r'\b(?:price.tag|shelf.tag|shelf.price|price.sticker|displayed.prices?|displays?.{0,12}prices|shelf.{0,30}checkout|sukli|shortchang\w*|change)\b',r'\b(?:price.tag|price.label|change|shortchang\w*)\b','price tag change'),
 ('consumer',r'\b(?:unsafe|exposed.(?:(?:live.)?wir(?:es?|ing)|metal)|sparks|hazard\w*|dangerous\w*|overheats?|amoy.sunog|product.safety)\b',r'\b(?:safety|unsafe|hazard\w*|defect\w*)\b','product safety defect'),
 ('consumer',r'\b(?:laundry|service.{0,35}(?:damage|shrank|poor|faulty)|service.quality)\b',r'\b(?:service.quality|defective.services|supply.of.services|service.imperfection)\b','service quality imperfection'),
 ('consumer',r'\b(?:online|internet|platform|marketplace)\b',r'\b(?:online|internet|e.commerce|consumer.remedies)\b','internet online consumer remedies'),
 ('consumer',r'\b(?:consumer.act|purpose|general.framework|general.consumer.protection)\b',r'\b(?:declaration.of.(?:basic.)?policy|short.title|construction|policy)\b','consumer policy'),
 ('consumer',r'\b(?:dti|consumer.complaints?|mediation|investigat\w*)\b',r'\b(?:complaints?|mediation|adjudication|consumer.assistance|investigat\w*)\b','consumer complaint mediation investigation'),
]


def query_facets(query, domain):
    facets=[f for f in FACETS if f[0] == domain and re.search(f[1],query,re.I)]
    # A wage amount mentioned in a deductions question is not a request about
    # pay frequency. Preserve frequency when the user actually asks about it.
    if domain=='labor' and re.search(r'\b(?:deduct\w*|bawas|kinakaltas|kaltas)\b',query,re.I) and not re.search(r'\b(?:late|delayed|unpaid|when|often|payday|frequency|kadalas)\b',query,re.I):
        facets=[f for f in facets if f[3]!='time payment wages']
    return facets


def source_relevance(query, domain, hit):
    """Local topical ranking, not a support verdict or calibrated confidence."""
    facets=query_facets(query,domain)
    heading=hit.get('heading') or ''
    title=hit.get('document_title') or ''
    text=hit.get('parent_text','')
    context=' '.join([hit.get('provision_id',''),heading,title])
    coverage=' '.join(hit.get('conditions',[]))
    # Source identity matters even when two statutes share a generic heading.
    if domain=='consumer':
        if re.search(r'\bconsumer.act\b',query,re.I) and not re.search(r'\bconsumer.act\b',title,re.I):return 0.
        if re.search(r'no.shortchanging|republic.act.no.?\s*10909',title,re.I) and not re.search(r'\b(?:shortchang\w*|sukli|exact.change|change)\b',query,re.I):return 0.
    if (domain=='consumer' and re.search(r'internet.transactions|online.consumers?',title+' '+heading,re.I)
            and not re.search(r'\b(?:online|internet|marketplace|e.commerce|platform|website)\b',query,re.I)):return 0.
    if (domain=='labor' and re.search(r'\b(?:educational.institutions?|schools?|tuition)\b',heading,re.I)
            and not re.search(r'\b(?:school\w*|educat\w*|tuition|teacher\w*|college|university)\b',query,re.I)):return 0.
    if (domain=='labor' and re.search(r'\bthis\s+rule\s+shall\s+apply\s+to\b[\s\S]{0,180}\ball\s+hospitals\s+and\s+clinics\b',coverage,re.I)
            and not re.search(r'\b(?:hospital|clinic|healthcare)\b',query,re.I)):return 0.
    # Some narrowly applicable provisions use generic section headings. Read
    # the stated worker category as well as the heading before ranking them.
    if (domain=='labor' and re.search(r'\b(?:for|of)\s+(?:hospital.and.clinic|hospital|clinic)\s+personnel\b',text[:600],re.I)
            and not re.search(r'\b(?:hospital|clinic|healthcare)\b',query,re.I)):return 0.
    service_question=re.search(r'\b(?:laundry|(?:paid|repair|cleaning|installation).service|service.quality)\b',query,re.I)
    if (service_question and re.search(r'\bproduct(?:.and.service)?(?:.quality)?.imperfection\b',heading,re.I)
            and not re.search(r'\b(?:bought|purchased|goods|products?)\b',query,re.I)):return 0.
    # Specialized employment provisions are not ordinary workplace rules.
    special=[(r'apprentice\w*',r'\bapprentice\w*'),
             (r'handicapped.worker\w*',r'\b(?:handicapped|disabled).worker'),
             (r'private.employment.agenc\w*|overseas.recruit\w*',r'\b(?:recruit\w*|placement|employment.agenc\w*|overseas|ofw)\b'),
             (r'hospital\w*|clinic\w*',r'\b(?:hospital|clinic|healthcare)\b')]
    # A generic section heading must not hide a recruitment-agency-only
    # requirement. Hospital exceptions inside general rules do not make the
    # entire general provision hospital-only.
    for restricted,query_context in special:
        restricted_context=context+(' '+text[:350] if 'agenc' in restricted else '')
        if domain=='labor' and re.search(restricted,restricted_context,re.I) and not re.search(query_context,query,re.I):return 0.
    if (domain=='labor' and re.search(r'conciliation.mediation.on.termination.disputes',heading,re.I)
            and not re.search(r'\b(?:terminat\w*|dismiss\w*|fired|tinanggal)\b',query,re.I)):return 0.
    qualifications=[(r'bankruptcy',r'bankrupt\w*|insolven\w*'),
                    (r'payment.by.check',r'bank.check|cheque|payment.by.check'),
                    (r'emergency.overtime',r'emergency|urgent|disaster'),
                    (r'compulsory.overtime',r'compulsory|force\w*|require\w*|must|mandatory'),
                    (r'successive.regular.holidays',r'successive|consecutive|two.holidays'),
                    (r'report.of.dismissal',r'report|record|statistic|regional.office'),
                    (r'deceptive.sales.*by.regulation',r'regulat\w*|rule.?making|department|authority'),
                    (r'professional.services',r'professional|licensed|license')]
    if any(re.search(h,heading,re.I) and not re.search(q,query,re.I) for h,q in qualifications):return 0.
    if re.search(r'quantity.imperfection',heading,re.I) and not re.search(r'quantity|amount|weight|volume|shortage|net.content',query,re.I):return 0.
    if facets:
        direct=sum(1. if re.search(f[2],heading,re.I) else
                   .5 if re.search(f[2],title,re.I) and re.search(f[2],text,re.I) else 0.
                   for f in facets)
        # Thirteenth-month documents have section headings without the topic.
        if re.search(r'\b(?:13th|thirteenth)\b',query,re.I) and re.search(r'\b(?:13th|thirteenth)\b',title,re.I):direct+=1
        if not direct:return 0.
        return float(direct*3)
    words=set(tokens(query))-set('rule rules help concern rights general explain employer employee company consumer question apply do can what which how not no'.split())
    overlap=words & set(tokens(heading+' '+text))
    return float(len(overlap)) if len(overlap)>=2 else 0.


def relevant_excerpt(query,domain,hit,limit=1800):
    """Choose one complete exact paragraph, preserving stored source identity."""
    text=hit['parent_text']
    if not source_relevance(query,domain,hit):return ''
    if len(text)<=limit:return text
    facets=query_facets(query,domain);words=set(tokens(query))
    # Keep a heading, its list, and its qualifications together. Isolated PDF
    # lines/list items can omit the rule's subject or its limiting exception.
    starts=[0]+[m.start() for m in re.finditer(r'(?m)^[A-Z][A-Za-z ,/-]{4,100}\.\s*[-–—]',text) if m.start()>0]
    spans=[text[a:b].strip() for a,b in zip(starts,starts[1:]+[len(text)])]
    units=[s for s in spans if 60<=len(s)<=limit and re.search(r'[.;:!?)]\s*$',s)]
    if not units:
        units=[s.strip() for s in re.split(r'\n\s*\n',text) if 60<=len(s.strip())<=limit
               and re.match(r'[A-Z0-9]',s.strip()) and re.search(r'[.;!?)]\s*$',s)]
    if not units:return ''
    def value(unit):
        topical=sum(bool(re.search(f[2],unit,re.I)) for f in facets)
        overlap=len(words & set(tokens(unit)))
        expressed=bool(re.search(r'\b(?:written|express)\s+warrant',query,re.I))
        if expressed and re.search(r'\b(?:written|express)\s+warrant',unit,re.I):overlap+=3
        return (topical,overlap)
    return max(units,key=value)

