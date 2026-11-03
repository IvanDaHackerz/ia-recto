"""Freeze new fictional Philippine development questions before any inference."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
# Expectations describe the project's documented topic scope, not legal merits.
LABOR = [
('wage_frequency', 'Crew ako sa private bakery sa Quezon City. Sabi ng may-ari isang bagsakang sahod lang tuwing katapusan. Ano ang general rule sa pagitan ng mga payday?'),
('delayed_wages', 'The payroll of our private printing business in Cebu is twelve days late. The manager says customers have not paid yet. What wage-payment framework should workers inspect?'),
('deductions', 'Private hardware employee ako. May nabasag na paninda at ibabawas daw sa akin kahit hindi pa ako napapaliwanag. What safeguards apply to loss deductions?'),
('deductions', 'A private canteen owner wants to deduct the entire cost of a lost utensil from the next salary. What facts and conditions matter under the recorded deduction rule?'),
('hours', 'A private delivery warehouse makes staff attend a compulsory safety briefing before clocking in. I am asking whether the briefing counts as work time, not about safety compliance.'),
('hours', 'Private shop employee ako sa Iloilo. Tapos na ang shift pero pinaghihintay kami sa premises hanggang dumating ang reliever. What source covers that waiting time?'),
('meal_period', 'At a private office in Pasig, what is the general rule on the length of an ordinary meal break? Please explain the framework rather than calculate compensation.'),
('overtime', 'Private factory worker ako. Naka-eight hours na ako tapos pinadagdag pa ng tatlong oras. What general overtime provisions and coverage limits are relevant?'),
('undertime', 'Our private employer says leaving early on Tuesday will erase overtime on Friday. How does the recorded undertime-offsetting rule treat that?'),
('rest_day', 'Private grocery staff ako. Eleven days straight ang schedule ko na walang buong araw na pahinga. What weekly rest rule can you explain?'),
('rest_day', 'A private employer schedules my weekly rest day but I have a religious preference. What does the recorded scheduling rule require the employer to consider?'),
('holiday', 'Private-sector employee ako sa Davao. We worked on a regular holiday. What is the recorded holiday-pay framework, including its exceptions?'),
('holiday', 'An ordinary private shop stayed closed on a regular holiday and withheld the day\'s pay. Can you show the applicable recorded rule without deciding whether every employee is covered?'),
('premium', 'In a private workplace, how is work on a scheduled rest day distinguished from ordinary weekday work under the premium-pay provisions?'),
('probation', 'A private company hired me on probation but only told me its regularization standards at the end. What does the recorded probationary rule say about communicating standards?'),
('employment_status', 'Private employee ako sa garment business. Paulit-ulit ang contract at usual na trabaho ng negosyo ang ginagawa ko. What regular-employment test is recorded? Do not decide my status.'),
('project', 'For a private construction employer, what needs to be identified when a worker is hired for a particular project? I want the general employment framework.'),
('seasonal', 'Sa private farm ako. Seasonal daw ang trabaho namin. Explain the seasonal exception in the recorded employment-status rule without saying that I am automatically casual.'),
('termination', 'A private hotel dismissed a receptionist after an accusation of theft. The worker was given no chance to explain. What procedural safeguards can be described generally?'),
('termination', 'My private employer says the business is closing and has sent a termination letter. What general authorized-cause framework and notice requirements should I inspect?'),
('complaint', 'May unpaid salary concern ako sa private repair shop. Ano ang purpose ng SEnA conciliation, at may decision na ba agad doon?'),
('complaint', 'I have an overtime dispute with a private company in Laguna. Can you explain the basic labor complaint and referral process without filing a case for me?'),
('thirteenth', 'Sa private cafe ako employed. Wala raw kaming 13th-month pay dahil maliit lang ang business. Does your source collection cover this issue?'),
('final_pay', 'I resigned from a private accounting firm in Makati. My final pay is still pending. What recorded source supports any release deadline?'),
('coe', 'Former employee ako ng private tutorial center. Humihingi ako ng certificate of employment pero ayaw nilang mag-issue. What can this system support?'),
]
CONSUMER = [
('defect', 'Bumili ako ng bagong rice cooker sa appliance shop sa Manila. Hindi ito umiinit kahit tama ang gamit. What product-imperfection remedies are recorded?'),
('defect', 'The brand-new office chair I bought for my home from a retail store has a broken height mechanism. No injury occurred. What quality-remedy framework applies generally?'),
('defect', 'A retail seller delivered a dining table with one leg missing. Please explain the product-quality framework without promising an immediate refund.'),
('warranty', 'A shop in Baguio refuses to accept my blender warranty complaint and tells me to contact the maker myself. What duties of the retailer are actually recorded?'),
('warranty', 'I bought a washing machine directly at a manufacturer showroom and it has a written warranty. What is the recorded process for honoring that warranty?'),
('warranty', 'May written warranty yung electric fan na binili ko sa tindahan. Ano ang role ng distributor kapag ipinasa ng retailer ang claim?'),
('correction', 'If a product imperfection is not corrected within the applicable period, what alternative remedies are listed, and can the parties agree on a different period?'),
('correction', 'Under the recorded consumer-product rule, are there circumstances allowing remedies without first waiting for correction? Please preserve the conditions.'),
('refund', 'A store sign says NO RETURN NO EXCHANGE even for a defective new kettle. What general product-remedy rules should a buyer read?'),
('price', 'Sa supermarket sa Cavite, 180 pesos ang shelf label pero 210 ang singil sa counter. What rule addresses charging above the displayed price?'),
('price', 'A sari-sari shop displays one price list for tiny individually sold items. Does that allow it to charge more than the listed price?'),
('change', 'After a cash purchase at a grocery in Bacolod, the cashier gave sweets instead of the remaining coins. What general rule covers my change?'),
('change', 'I paid exact bills at a retail shop but the cashier rounded the change down and kept the difference. What recorded consumer framework fits?'),
('advertisement', 'A shop advertised a phone as unused but sold a previously activated display unit. What deceptive-sales framework can be explained if that allegation is true?'),
('advertisement', 'An ordinary online furniture seller advertises hardwood but the delivered cabinet is plastic laminate. Which recorded representation rules are relevant?'),
('advertisement', 'A kitchen-appliance advertisement claims official certification that the seller cannot substantiate. Explain the recorded rule without declaring a violation proved.'),
('service', 'Nagpa-laundry ako sa commercial laundry shop sa Cebu. Hindi nila ginawa yung binayarang stain-removal service. What service-imperfection remedy framework is recorded?'),
('service', 'A paid appliance repair service returned my toaster without performing the repair described in the receipt. What general consumer-service rule is relevant?'),
('online_wrong', 'An online retail merchant sent medium shoes although the confirmed order says large. What recorded conformity remedies should I inspect?'),
('online_return', 'My online order was the wrong appliance model. The merchant says I must pay shipping to send it back. What does the recorded return rule say?'),
('online_complaint', 'For an ordinary online retail dispute in the Philippines, what platform complaint steps are recorded before the buyer escalates to a government office?'),
('online_change', 'I ordered the wrong color myself from an ordinary online retailer and want to change my order. Please distinguish a change of mind from delivery of a nonconforming item.'),
('safety', 'A newly bought power strip overheated during ordinary household use and scorched a desk. What recorded product-safety framework and limitations can you explain?'),
('safety', 'The bottle of household cleaner I bought from a shop has a damaged safety seal. What recorded consumer-product safety provisions can I inspect?'),
('dti', 'I bought a defective household fan at a retail shop in Naga. What basic DTI consumer complaint process can this system describe?'),
]
# (topic, text, supported domains, partial scope). Different actors are explicit.
MIXED = [
('wage_price', 'Private bakery employee ako with delayed wages. Separately, a grocery charged me more than its shelf label. Please explain both concerns.', ['labor','consumer'], False),
('overtime_warranty', 'My private employer will not pay ordinary overtime. Separately, an appliance shop refuses my written warranty claim. Handle these as two issues.', ['labor','consumer'], False),
('deduction_defect', 'A private shop deducts breakages from my salary without hearing me. I also bought a defective home blender from another seller. What frameworks fit?', ['labor','consumer'], False),
('rest_change', 'Private warehouse worker ako with no weekly rest day. Also, a supermarket gave candy instead of cash change. Please keep the issues separate.', ['labor','consumer'], False),
('dismissal_service', 'A private clinic dismissed its receptionist without an opportunity to respond. Separately, a commercial laundry business did not perform the cleaning I paid for.', ['labor','consumer'], False),
('probation_online', 'My private employer never explained probation standards. Also, my online retail order arrived in the wrong size. Explain the supported rules for each.', ['labor','consumer'], False),
('project_ad', 'My private construction contract never identifies the alleged project. A separate furniture store also advertised hardwood but supplied particle board. What can you explain?', ['labor','consumer'], False),
('holiday_price', 'Private employee ako asking about regular holiday pay. Separately, a store checkout charge exceeded the price list. Which provisions address each?', ['labor','consumer'], False),
('sena_safety', 'I need basic SEnA information for a private-sector unpaid-wage concern. Separately, a retailer sold me a power strip that overheated. Please distinguish the concerns.', ['labor','consumer'], False),
('source_gap_supported', 'I need a COE from my former private employer. Separately, the retailer refuses to accept my appliance warranty claim. Explain whatever your sources support and name any gap.', ['labor','consumer'], False),
('labor_bank', 'Private employee ako at hindi pa binabayaran ang overtime. Separately, I dispute a bank charge on my personal savings account.', ['labor'], True),
('consumer_government', 'I am a government clerk disputing my employment overtime. Separately, a retail store sold me a rice cooker that does not heat.', ['consumer'], True),
('labor_telecom', 'My private employer deducts missing inventory from my wages. Separately, my mobile network billed me for a plan I did not order.', ['labor'], True),
('consumer_ofw', 'OFW ako working abroad with unpaid wages. Separately, I bought a defective fan from a local Philippine retail store for my home.', ['consumer'], True),
('labor_rent', 'A private company fired me without giving me a chance to answer. My apartment landlord also refuses to return my rental security deposit.', ['labor'], True),
('consumer_insurance', 'An appliance retailer ignores my written warranty complaint. Separately, my insurer denied an accident insurance claim.', ['consumer'], True),
('labor_union', 'I want general rules on ordinary overtime at my private job. I also want help challenging our union certification election result.', ['labor'], True),
('consumer_privacy', 'An online retailer sent the wrong model of kettle. The seller also posted my ID publicly; I want to pursue that privacy complaint separately.', ['consumer'], True),
('labor_minimum', 'Private employee ako asking about the interval between wage payments. Separately, give me the exact current minimum-wage amount for my region.', ['labor'], True),
('consumer_crime', 'A retail shop sold me a broken new chair. Separately, somebody stole my motorcycle outside the shop and I need criminal-case advice.', ['consumer'], True),
('three_bank', 'My private employer owes ordinary overtime. A shop separately refuses my blender warranty claim. My bank also charged an account fee that I dispute. Treat all three concerns.', ['labor','consumer'], True),
('three_rent', 'Private worker ako with a rest-day concern. I also received the wrong retail order online. Separately, my landlord kept my rental deposit.', ['labor','consumer'], True),
('three_utility', 'A private employer deducts missing cash from everyone. A grocery also kept my small change. Separately, I dispute an electricity utility bill.', ['labor','consumer'], True),
('three_medical', 'A private employer dismissed me without a chance to respond. A store also charged above its shelf price. Separately, I want to sue my surgeon for a medical error.', ['labor','consumer'], True),
('three_seafarer', 'I have a private office probation-standards concern. A retail repair shop also did not perform the agreed service. Separately, my seafarer brother asks about unpaid shipboard wages.', ['labor','consumer'], True),
]
OUTSIDE = [
('regional_wage', 'What is the exact current minimum daily wage in Region IV-A for a small retail employer? I only need the peso amount.'),
('ofw', 'OFW ako employed in Dubai. My overseas employer kept two months of salary. What overseas employment case should I bring?'),
('seafarer', 'I work aboard an international vessel as a Filipino seafarer. How do I recover unpaid shipboard wages?'),
('government', 'Permanent employee ako sa city hall. Government overtime pay ang concern ko. What rules should I rely on?'),
('kasambahay', 'Kasambahay ako sa private household sa Manila. What employment rights and salary rules apply to my domestic work?'),
('union', 'Our union lost a certification election at a private factory. How can we challenge the election and representation result?'),
('compensation', 'Compute the workers compensation disability benefit for my workplace injury. I need the award amount.'),
('osh', 'What mandatory occupational-safety compliance documents must our private factory submit after a machine accident?'),
('retirement', 'I am leaving my private employer at retirement age. Please calculate my retirement benefit and pension entitlement.'),
('pending_case', 'My labor case is already pending in court. Can you draft my next pleading and predict how the judge will decide?'),
('prediction', 'My private employer dismissed me. Can you guarantee whether I will win and how much the tribunal will award me?'),
('bank', 'My bank froze my savings account and charged dormancy fees. What banking dispute should I file?'),
('lending', 'A lending app charges interest and penalties I dispute. What specialized lending rules let me challenge the loan?'),
('credit_card', 'My credit-card bank billed a transaction I did not authorize. What banking process covers the chargeback?'),
('insurance', 'My insurer denied payment under my health insurance policy. What insurance complaint should I bring?'),
('securities', 'A broker promised investment returns and my shares lost value. What securities complaint can I file?'),
('telecom', 'My fiber internet provider bills me during an outage. What telecom regulations require a bill adjustment?'),
('privacy', 'A grocery store publicly posted my ID and address. My only concern is the personal-data breach, not a product purchase.'),
('medical', 'A surgeon allegedly used the wrong procedure at a hospital. I want medical malpractice advice, not a retail-product remedy.'),
('real_estate', 'The developer has not delivered the condominium unit I purchased. What real-estate housing complaint should I file?'),
('transport', 'A bus operator refused to honor a transport fare discount. What transportation regulator should decide the dispute?'),
('utility', 'The water utility billed me for consumption after a meter problem. What utility-billing rules govern this?'),
('criminal_online', 'I paid a fake online seller who disappeared and used a stolen identity. I need a cybercrime investigation, not an ordinary retail return.'),
('family', 'My spouse and I disagree about custody of our child in the Philippines. What family-court order should I request?'),
('unrelated', 'How do I cook adobo for six people without making it too salty?'),
]

def main():
    if (BASE/'live-cases.json').exists():
        raise SystemExit('Preserve frozen input; use a new study version')
    assert len(LABOR)==len(CONSUMER)==len(MIXED)==len(OUTSIDE)==25
    rows=[]
    for group, items in [('labor',LABOR),('consumer',CONSUMER),('mixed',MIXED),('out_of_scope',OUTSIDE)]:
        for item in items:
            topic, question=item[:2]
            domains=item[2] if group=='mixed' else [group] if group in {'labor','consumer'} else []
            scope='partially_supported' if group=='mixed' and item[3] else 'unsupported' if group=='out_of_scope' else 'fully_supported'
            route='refer_out_of_scope' if group=='out_of_scope' else 'retrieve_supported_components' if group=='mixed' else 'retrieve_supported_evidence'
            cid=f'PH2_{len(rows)+1:03d}'
            rows.append({'case_id':cid,'family_id':cid,'question_text':question,'group':group,'topic':topic,
                         'AI_authored':True,'independent_human_gold':False,
                         'source_case':{'expected_primary':group,'expected_scope':scope,'expected_route':route,
                         'expected_domains':sorted(domains),'relevant_ids':[],'concerns':[],
                         'retrieval_judgment':'no_candidates' if group=='out_of_scope' else 'unjudged'}})
    assert len({r['question_text'] for r in rows})==100
    raw=(json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode()
    (BASE/'live-cases.json').write_bytes(raw)
    (BASE/'live-case-manifest.json').write_text(json.dumps({'count':100,'groups':{g:25 for g in ['labor','consumer','mixed','out_of_scope']},
        'cases_sha256':hashlib.sha256(raw).hexdigest(),'expectations_frozen_before_inference':True,
        'authorship':'AI-authored fictional Philippine development questions','independent_human_questions':0,
        'legal_accuracy_measured':False,'repair_policy':'Preserve first-pass results; disclose all retests as development reuse.',
        'retrieval_policy':'Topic expectations frozen; relevant source IDs not independently pre-judged. Source gaps are separate from classification.'},indent=2)+'\n',encoding='utf-8')
    print('Frozen 100 new questions:',hashlib.sha256(raw).hexdigest())

if __name__=='__main__': main()
