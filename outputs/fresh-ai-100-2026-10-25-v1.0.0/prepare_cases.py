"""Freeze new fictional questions and expectations before any inference."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
DATA = r"""
L|night_work|I pack orders for a private Cebu warehouse from 11 at night until 7 in the morning. Payroll lists the same basic hourly pay throughout. What general night-work provision should I read?
L|night_work|sa private hotel aq nagwowork, 9pm to 5am duty q. wlang night differential sa payslip. anu ba ung recorded rule at sino covered?
L|overtime|At a private printing shop in Laguna we sometimes work eleven hours on a normal Tuesday. The owner calls the extra hours volunteer time even though attendance is required. Explain the ordinary overtime rule conditionally.
L|overtime|private factory worker po, pinapasok kmi 8am hanggang 7pm may one-hour lunch. sabi fixed monthly salary kaya walang ot. ano general rule sa overtime?
L|wage_timing|Our private furniture business pays workers once every six weeks because customers pay slowly. Which rule deals with how often wages are paid?
L|wage_timing|empleyado aq sa pribadong laundry, sahod namin laging pinapaabot next month kasi wala pa raw collection. ano sabi ng source tungkol sa pagitan ng sweldo?
L|deductions|A private pharmacy deducted the full cost of a missing medicine box from my wages without letting me explain. What conditions on loss-related deductions should be checked?
L|deductions|pribadong stockroom helper aq, knaltas ung basag na tray sa sahod q kahit di pa sure sino nkabasag. may rules ba bago sila magkaltas?
L|payroll|For workers in a private garment factory, what entries should payroll records contain about working hours, pay rates, and deductions?
L|payroll|private office employee ako. ang payslip total lang walang hours o breakdown ng bawas. anong payroll information ang nasa recorded rules?
L|weekly_rest|I work seven days every week at a private bakery. Management says our store never closes, so workers do not get a weekly rest period. What general provision covers this?
L|religious_rest|A worker in a private supermarket requested a weekly rest day that matches their religious observance. How does the recorded rule treat that preference and its exceptions?
L|holiday|Our private repair shop closed on a regular holiday and marked the day unpaid for everyone. Explain the general holiday-pay rule and coverage exceptions without deciding anyone's entitlement.
L|holiday|private warehouse po, walang pasok nung regular holiday tas zero bayad lahat. ano ung general holiday-pay provision at may exclusions ba?
L|undertime|My private employer says arriving an hour late on Wednesday cancels an hour of overtime already worked on Thursday. What does the recorded offsetting rule say?
L|undertime|sa private shop q, papalitan daw ng half-day leave ung overtime ko last week. pwede bang explain ung rule sa offsetting, general lang?
L|probation|A private distributor told a probationary worker about the performance standards only on the last day of probation. What does the recorded provision say about communicating those standards?
L|status|A private food manufacturer keeps renewing four-month contracts for workers doing its everyday production work. Explain the regular-versus-casual rule and project or seasonal exceptions generally.
L|status|pribadong farm worker aq, tuwing harvest lng kmi kinukuha. ano ung seasonal exception sa employment-status rule? di ko hinihingi na ideclare agad akong regular.
L|dismissal|A private hardware employer fired a worker for alleged misconduct without giving a chance to respond. What recorded procedural protections can be explained?
L|closure|A private shoe factory says it will close permanently and terminate its employees. Which recorded rules discuss business closure, notice, and applicable conditions?
L|security_tenure|I am a regular employee of a private bookstore. The owner says I can be removed whenever sales are low without explaining any legal cause. What general security-of-tenure rule is recorded?
L|conciliation|What is the purpose of SEnA when a private-sector worker and employer disagree about unpaid wages? Explain the basic assistance process rather than predicting a result.
L|hours_worked|My private café requires us to attend a twenty-minute briefing before clocking in. Which recorded definition would be needed to check whether that time counts as work?
L|meal_period|A private assembly plant gives only twenty minutes for lunch while the machines keep running. What sources or limitations apply to a general meal-period question?
L|final_pay|A worker resigned from a private travel agency and asks about the release deadline for final pay and a certificate of employment. Explain only what the available sources actually support.
L|thirteenth|I work for a private retailer and want the general rule for thirteenth-month pay. If your recorded sources do not cover the computation, say so rather than inventing a formula.
L|wage_payment|My private employer wants to pay part of our wages using vouchers that can only be spent in the company store. What recorded wage-payment rules should be checked?
L|rest_work|Private restaurant employee ako. pinapasok nila ako sa scheduled rest day tapos ordinary daily rate lang. ano general provision tungkol sa premium for rest-day work?
L|night_work|pribadong call center agent aq, midnight shift. d q mahanap ung dagdag para sa night hours sa payslip. pls explain ung rule pati coverage limits.
C|warranty|A local shop sold me a new stand mixer with a written warranty, but now refuses to accept a claim because I bought it during a promotion. What recorded warranty rules are relevant?
C|warranty|bumili aq ng plantsa sa appliance store sa Bacolod, sira agad switch. may warranty pero sabi seller wala na silang pake after payment. ano rules dto?
C|claim_forwarding|A retailer told me to submit my written warranty complaint to the manufacturer myself. What does the recorded rule say about the retailer forwarding a claim and charging for it?
C|repair_refund|A new rechargeable lamp from a neighborhood store stopped charging after one use. What conditions govern correction, replacement, or refund under the recorded product-imperfection rule?
C|defective_goods|yung bagong folding chair na nabili q sa shop nawawala ung locking pin at bumabagsak. ano consumer provision pwde basahin?
C|product_safety|A new toaster from a local appliance seller produces sparks from exposed wiring. What recorded product-safety and defect rules can you explain without diagnosing the electrical fault?
C|advertising|An advertisement says a power bank has a certain capacity, but the packaging lists a much smaller capacity. Which recorded rules discuss misleading product advertising?
C|deceptive_sale|A gadget seller described a tablet as brand new but later admitted it had been repaired and previously used. What general deceptive-sales rule is relevant?
C|hidden_fee|A local furniture shop added an undisclosed handling charge after I had already paid the displayed total. What recorded consumer rule addresses that kind of sales practice?
C|price_tag|A shelf label in a small grocery says 79 pesos, but checkout charges 92 pesos for the same item. What does the recorded price-tag provision say?
C|price_list|A shop uses a visible price list instead of individual tags. Does the recorded provision distinguish permitted price displays from charging more than the displayed price?
C|exact_change|A cashier owed me seven pesos change but gave me a discount coupon without asking. Which recorded exact-change rule covers this situation?
C|exact_change|sa grocery kulang ng 4 pesos ung sukli q. sabi wala silang barya kaya hayaan nlng daw. anu general rule, di q naman pinayagan?
C|service_quality|A paid laundry service returned my jacket badly shrunken after ignoring the care instructions. What general recorded provisions cover defective services?
C|service_quality|nagbayad aq sa repair shop para ayusin ung fan. binalik nila pero same sira at ayaw nila tignan uli. ano source tungkol sa service quality?
C|online_wrong_item|I ordered a stainless cooking pot from a Philippine online merchant but received a plastic storage box. What recorded online-sale remedies and return conditions can be explained?
C|online_redress|A Philippine marketplace seller has no working way to submit a complaint about a faulty kettle. What recorded obligations concern an internal complaint or redress mechanism?
C|online_description|sa online seller sa pinas ako umorder ng blue backpack, green at ibang model dumating. anu general rules at kelan kailangan ibalik ung original item?
C|warranty_document|A shop says the written warranty document is unnecessary because its staff can remember the promise. What does the recorded consumer law say about warranty information?
C|consumer_complaint|A local seller and I disagree about a defective desk lamp. What is the general DTI consumer-complaint or mediation process in the recorded sources, without promising a result?
C|labeling|The package of an appliance does not identify the manufacturer or importer. What general consumer labeling provisions are available in the corpus?
C|unsafe_toy|A toy bought from a local shop has a battery compartment that falls open during normal handling. What recorded safety or product-quality rules can be discussed?
C|used_as_new|nabili q sa gadget shop sealed kuno pero may lumang account pa at repair marks ung unit. sabi new daw nung binenta. ano consumer concern ito?
C|cash_change|A bakery cashier wants to give bread instead of the cash change owed to me. What recorded rule applies if I do not agree to that substitution?
C|warranty_scope|A dealer says every warranty disappears whenever the product is on clearance. Explain the general recorded warranty rule and any necessary qualifications.
C|repair_delay|The store accepted my defective appliance for correction but still has not fixed it after several weeks. Explain the recorded product-imperfection remedy sequence with its conditions.
C|deceptive_features|A local shop promised a printer had wireless connectivity, but the delivered model has no wireless function. Which recorded consumer provisions address the difference?
C|price_display|nasa shelf 150 ung bottle, sa receipt 175. same brand same size. sabi cashier updated na raw price pero d pa napapalitan tag. ano general rule?
C|warranty_claim|My receipt and warranty card show the seller's name, but the seller says only its supplier is responsible for receiving my written complaint. Explain the recorded claim-forwarding obligation.
C|online_refund|A Philippine online merchant admits it sent the wrong shoe size. Explain the recorded remedy and distinguish a return obligation after choosing replacement or refund from merely reporting the problem.
M|both|My private security employer omitted overtime pay. Separately, a local appliance seller refuses to receive my written warranty complaint for a defective oven. Explain each concern using its own source.
M|both|pribadong factory worker aq, binawasan sahod q sa kulang inventory. hiwalay ung grocery na sobra singil sa price tag. pakiseparate ung dalawang concern.
M|both|My private office has not paid wages for six weeks. An unrelated online merchant also sent the wrong model of desk fan. What recorded rules cover the two situations?
M|both|A private hotel worker's night hours are paid at the ordinary rate. Separately, a repair service returned the worker's radio with the original defect still present. Explain both issues.
M|both|sa private bakery wala kaming weekly rest. saka ung binili kong charger sa local shop may exposed wire. labor at consumer ba pareho, at ano sources nila?
M|both|My private employer wants to substitute leave for earned overtime. Separately, a supermarket gave me sweets instead of my cash change. Please address both concerns separately.
M|both|A private manufacturer dismissed me without an opportunity to answer. In a separate purchase, a gadget seller passed off a refurbished laptop as new. Which recorded rules relate to each?
M|both|private employee aq na hindi sinabi probation standards nung hiring. unrelated, may advertised feature ung blender na binili q na wala pala. paki explain bawat concern.
M|both|A private factory will close permanently and dismiss its staff. Separately, my local appliance dealer refuses a warranty claim solely because the purchase was discounted. Keep the two explanations separate.
M|both|My private shop employer wants to pay wages with store vouchers. An unrelated laundry business damaged the coat I paid it to clean. What recorded provisions are relevant to each issue?
P_L|banking|My private employer pays wages only every two months. Separately, my bank charged an ATM fee I want to dispute. Which concern can this project cover?
P_L|inheritance|pribadong warehouse worker aq, di bayad overtime. hiwalay ung away naming magkapatid sa mana ng lupa. alin lang ung kaya ng system?
P_L|criminal|A private employer deducted an alleged equipment loss from wages without a hearing. Separately, I need advice about a criminal accusation involving a stolen motorcycle. Explain only the supported concern.
P_L|tax|A private hotel worker has a night-pay concern. Separately, I want the amount of income tax due on a side business. Identify what falls inside the project scope.
P_C|tenancy|A store charged above its shelf price. Separately, my landlord refuses to return my apartment deposit. Which recorded consumer concern can you explain?
P_C|privacy|yung bagong kettle q may sira at warranty pa sa seller. hiwalay, pinost ng kapitbahay private messages q online. alin ung covered nyo?
P_C|banking|An online merchant delivered a different appliance model from my order. Separately, I want advice on a credit-card interest charge from the bank. Distinguish the supported part.
P_C|family|A local shop sold a repaired phone as brand new. In another matter, I need advice on child custody after separation. Explain only what this project's sources cover.
P_B|criminal|My private employer withheld wages, a separate grocery kept my cash change, and I also want criminal-defense advice about an unrelated incident. Keep all three concerns visible and explain only those in scope.
P_B|government|pribadong hotel employer q di binayaran overtime. ung store din ayaw tumanggap warranty claim. may hiwalay din akong tanong para sa kapatid kong government employee tungkol sa GSIS. alin ung covered?
P_L|overseas|My private employer in Davao deducted a cash shortage from my salary. Separately, my cousin employed in Qatar asks about an overseas employment contract. What can this project cover?
P_C|telecom|A Philippine online shop sent me broken headphones. Separately, my mobile network provider imposed a termination charge. Please identify the project boundary.
P_L|prediction|My private employer dismissed me without letting me answer. Explain the general recorded procedural rule, but I also want you to guarantee that I will win a case and state the exact damages.
P_C|prediction|A shop sold me a defective induction cooker. Explain the general recorded consumer remedy, and separately tell me the exact damages a judge will award in my case.
P_B|inheritance|A private employer delayed wages, a separate online merchant supplied the wrong product, and a third issue concerns inheritance of our family house. Give separate scope decisions.
O|government|I work for a provincial government office in the Philippines and want to challenge a civil-service disciplinary suspension. What rules govern my appeal?
O|overseas|I am employed by a household in Hong Kong and my employer retained part of my wages. What overseas-worker procedure applies?
O|seafarer|I am a Filipino seafarer on an international vessel and want advice on compensation under my maritime employment contract.
O|domestic|kasambahay po ako sa isang bahay sa Quezon City. ano rules sa special employment contract at benefits ng domestic worker?
O|banking|My savings bank charged a dormancy fee on my account. What banking regulation determines whether the fee is valid?
O|telecom|A Philippine internet provider charged for a month after I canceled service. What telecom rules govern the dispute?
O|tenancy|My apartment landlord in Pasig kept the security deposit after I moved out. What rental-law remedy can I use?
O|inheritance|How should siblings divide a deceased parent's house in the Philippines when they disagree about inheritance?
O|criminal|May subpoena ako tungkol sa criminal complaint sa Pilipinas. ano defense strategy ko at ano dapat sabihin ko sa prosecutor?
O|family|I want to change a child-custody arrangement after separation in the Philippines. What family-law process applies?
O|privacy|A neighbor uploaded screenshots of our private conversation. What data-privacy complaint can I bring?
O|tax|I run a small online business and want the exact tax return and tax computation I should file with the BIR.
O|current_rate|What is the exact current minimum wage amount today for a private retail worker in my city? I only want today's rate, not general wage-payment rules.
O|prediction|Without explaining any general rule, tell me whether I will win my labor case and exactly how much money the judge will award.
O|unrelated|Can you recommend the best fertilizer schedule for a balcony tomato plant in Manila?
"""


def write(name, value):
    path = BASE / name
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    cases = []
    for number, line in enumerate(DATA.strip().splitlines(), 1):
        kind, topic, question = line.split('|', 2)
        domains = {'L':['labor'], 'C':['consumer'], 'M':['labor','consumer'],
                   'P_L':['labor'], 'P_C':['consumer'], 'P_B':['labor','consumer'], 'O':[]}[kind]
        primary = {'L':'labor', 'C':'consumer', 'M':'mixed', 'O':'out_of_scope'}.get(kind, 'mixed')
        scope = 'unsupported' if kind == 'O' else 'partially_supported' if kind.startswith('P_') else 'fully_supported'
        route = 'refer_out_of_scope' if kind == 'O' else 'retrieve_supported_components' if kind in {'M','P_L','P_C','P_B'} else 'retrieve_supported_evidence'
        case_id = f'PH5_{number:03}'
        cases.append(dict(case_id=case_id, family_id=case_id, group=kind, topic=topic,
            question_text=question, AI_authored=True, independent_human_gold=False, development_replay=False,
            source_case=dict(expected_primary=primary, expected_scope=scope, expected_route=route,
                expected_domains=domains, relevant_ids=[], concerns=[], retrieval_judgment='no_candidates' if kind=='O' else 'unjudged')))
    assert len(cases) == 100, len(cases)
    normalize = lambda text: ' '.join(text.lower().split())
    questions = {normalize(c['question_text']) for c in cases}
    assert len(questions) == 100
    duplicates = []
    scanned = 0
    for path in (ROOT/'outputs').rglob('*cases*.json'):
        if BASE in path.parents or 'source_snapshot' in path.parts:
            continue
        try:
            rows = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            continue
        if not isinstance(rows, list): continue
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get('question_text'),str):
                scanned += 1
                if normalize(row['question_text']) in questions: duplicates.append(str(path.relative_to(ROOT)))
    assert not duplicates, duplicates
    write('live-cases.json', cases)
    write('live-case-manifest.json', dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        cases_sha256=hashlib.sha256((BASE/'live-cases.json').read_bytes()).hexdigest(),
        input_forms=len(cases), group_counts=dict(Counter(c['group'] for c in cases)),
        earlier_input_rows_checked_for_exact_duplicates=scanned, exact_duplicates=0,
        provenance='Fresh AI-authored fictional development questions, authored before inference; not human gold.',
        sampling='Purposive coverage, English/Taglish/noisy typing, not random population sampling.',
        prior_topic_overlap_expected=True, semantic_novelty_independently_validated=False))
    write('acceptance-criteria.json', dict(purpose='Engineering usability and source-agreement checks, not legal validation',
        criteria=['No dropped supported concerns','No substantive answers for excluded concerns',
        'No invented facts in normalization','Displayed claims address the requested issue and retain source conditions',
        'Quotes match exact recorded source spans','Provider problems and source gaps remain visible'],
        fresh_questions_frozen_before_inference=True, no_relabeling_after_inference=True))
    print(json.dumps(dict(count=len(cases), groups=dict(Counter(c['group'] for c in cases)), earlier_rows_checked=scanned)))


if __name__ == '__main__': main()
