"""AI-authored scope-wide development and reserved wording tests; no human gold."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Two development cases and one reserved case per scope field. The third case
# must not be inspected by the evaluation runner until implementation is frozen.
TOPICS = {
'labor.wages_payment': [
 'Two paydays have passed and my company still owes me my salary. Where do I start?',
 'Boss di pa nagbibigay ng sweldo namin, may pwede ba gawin?',
 'My employer keeps paying our wages several weeks late. What general rules cover payment?'],
'labor.hours_of_work': [
 'The company requires us to arrive early and wait for instructions. Does that time count as work?',
 'Required kami mag stay sa office kahit tapos na shift, working time ba yun?',
 'Our supervisor makes staff attend a mandatory briefing before clocking in. Is that working time?'],
'labor.rest_days': [
 'I work at a restaurant and have not had a day off for three weeks. What rest rules apply?',
 'May karapatan ba kami sa weekly day off sa trabaho?',
 'Our factory schedules us seven days each week. Can workers ask about weekly rest?'],
'labor.overtime_pay': [
 'I work ten hours a day in a warehouse but only get the usual daily pay. What are overtime rules?',
 'Lampas 8 oras kami sa trabaho pero walang dagdag bayad, ano rules?',
 'Our office requires two extra hours after the regular shift. How is additional work generally paid?'],
'labor.holiday_premium_pay': [
 'The office closed on Christmas and our manager deducted a day of pay. What holiday rules apply?',
 'Pumasok kami nung regular holiday, may premium ba dapat?',
 'What do the recorded rules say about pay when a private business closes on a regular holiday?'],
'labor.thirteenth_month_pay': [
 'I resigned after working for seven months. Can you explain thirteenth month pay?',
 'Wala raw 13th month kasi probationary lang ako, tama ba yun?',
 'My company calls its December payment a bonus. How does that differ from required thirteenth month pay?'],
'labor.employment_contracts': [
 'My company keeps renewing a five month contract. What does regular employment generally mean?',
 'Project based daw ako pero araw araw pareho trabaho ko sa kumpanya, ano ibig sabihin nun?',
 'I was hired on probation by a private company. What rules explain the probationary period?'],
'labor.termination_due_process': [
 'My boss fired me by text without a notice or a chance to respond. What process is usually required?',
 'Tinanggal ako sa trabaho bigla walang written notice, ano dapat proseso?',
 'Our company plans redundancies. What notice rules normally apply to authorized termination?'],
'labor.final_pay_coe': [
 'I left my company last month and HR is withholding my final pay and certificate of employment.',
 'Ayaw ibigay ng HR yung COE ko kahit resigned na, anong pwede gawin?',
 'After resignation, what do the stored sources say about requesting a certificate of employment?'],
'labor.complaint_referral': [
 'Where do I begin a labor complaint for unpaid wages at my company?',
 'Paano mag request ng SEnA assistance para sa problema sa trabaho?',
 'Is there a conciliation process at DOLE before a private employee files a formal labor dispute?'],
'consumer.general_framework': [
 'What is the Consumer Act of the Philippines intended to protect?',
 'Ano ba sakop ng Consumer Act para sa ordinaryong mamimili?',
 'Can you explain the general policy behind Philippine consumer protection law?'],
'consumer.defective_products': [
 'The new headphones I bought stopped working the next morning. What consumer rules cover that?',
 'Yung bagong electric fan ko ayaw umandar, kakabili ko lang sa mall.',
 'A retailer sold me a blender with a broken motor. What general rights should I inspect?'],
'consumer.warranties': [
 'The store says the written warranty on my laptop is no longer their problem. Can they ignore it?',
 'May warranty pa ref namin pero ayaw ayusin ng tindahan.',
 'A shop promised a one year warranty but now refuses to honor it. What does the law say about warranties?'],
'consumer.repair_replace_refund': [
 'The same faulty appliance has been repaired twice by the shop. Can I ask about replacement or a refund?',
 'Sira agad binili kong charger, ayaw ibalik ng seller yung bayad.',
 'A merchant delivered a defective desk lamp. Which repair, replacement or refund rules might be relevant?'],
'consumer.deceptive_unfair_sales': [
 'A salesperson hid an extra required fee until after I paid for the appliance. What protections apply?',
 'Sabi ng shop brand new yung phone pero refurbished pala.',
 'The merchant described a used device as unused to persuade me to buy it. Is that a deceptive sales concern?'],
'consumer.misleading_advertising': [
 'The advertised storage capacity of a tablet does not match the product the shop delivered.',
 'Iba yung nasa ads ng vacuum kumpara sa dumating na item, saan sakop yan?',
 'An appliance advertisement promises a feature that the actual product lacks. What rules address misleading ads?'],
'consumer.price_tags': [
 'The supermarket checkout charged a higher amount than the shelf label. What displayed-price rules apply?',
 'Candy binigay ng cashier imbes na tamang sukli, pwede ba yun?',
 'The price on a store shelf differs from the register price for the same goods. What can a buyer ask about?'],
'consumer.product_safety': [
 'A newly purchased extension cord sparks during normal use. What product safety rules are relevant?',
 'Delikado yung laruan na binili namin, may matutulis na parte.',
 'A household kettle sold by a retailer overheats dangerously. What general consumer safety protections apply?'],
'consumer.service_complaints': [
 'The laundry service damaged my clothes and refuses to discuss the problem. What consumer rules cover services?',
 'Nagbayad ako sa repair shop pero di nila inayos yung electric fan.',
 'A repair business accepted payment but returned my appliance without doing the agreed work. What protections apply?'],
'consumer.online_transactions': [
 'An online business keeps delaying my paid order and will not refund it. It still responds to messages.',
 'Maling kulay at size pinadala ng online shop, ayaw palitan.',
 'A registered online retailer delivered the wrong item and refuses a return. What consumer transaction rules apply?'],
'consumer.complaint_referral': [
 'How do I submit a consumer complaint to DTI against a shop?',
 'San pwede magreklamo sa DTI tungkol sa sirang appliance?',
 'What is the basic DTI mediation process for a consumer dispute with a retailer?'],
'labor.regional_minimum_wage_amounts': [
 'How many pesos is the minimum wage in Cebu today?',
 'Magkano na minimum wage sa NCR ngayon?',
 'Give me the exact current daily minimum wage rate for Region III.'],
'labor.ofw': [
 'I work in Dubai and my overseas employer has not paid me for a month.',
 'OFW ako sa Qatar, di sinunod ng employer kontrata namin.',
 'My recruiter changed the terms of my overseas job after deployment. Where does that fall?'],
'labor.seafarers': [
 'I am a seafarer and need help with a shipboard employment contract.',
 'Seaman ako, paano yung disability claim ko?',
 'A crew member on an international vessel disputes his seafarer benefits. Can this project cover that?'],
'labor.government_employment': [
 'I am employed by the city hall and my overtime was not paid.',
 'Government employee ako, binawasan sahod namin.',
 'A municipal employee wants to contest a disciplinary suspension under civil service rules.'],
'labor.kasambahay': [
 'I work as a live-in housemaid. What employment benefits should my household employer give?',
 'Kasambahay ako, walang day off na binibigay amo ko.',
 'What rules apply to the salary of a domestic worker employed by a family?'],
'labor.union_cba': [
 'Our union wants to challenge the result of a representation election.',
 'Paano makipag collective bargaining yung union namin?',
 'How does a union challenge the bargaining unit determination for a CBA negotiation?'],
'labor.workers_compensation': [
 'Calculate the disability compensation for an injury I suffered at work.',
 'Naaksidente ako sa trabaho, magkano employees compensation benefit ko?',
 'I need a computation of benefits for a work-related disability claim.'],
'labor.occupational_safety': [
 'Does our factory ventilation system meet occupational safety compliance requirements?',
 'Ano required OSH permits at safety officer compliance ng factory?',
 'What technical workplace standards govern employee exposure to dangerous chemicals?'],
'labor.retirement_pension': [
 'How much SSS pension will I get when I retire?',
 'Pa compute retirement pay ko base sa service years.',
 'Can you calculate my monthly GSIS retirement pension?'],
'labor.pending_case': [
 'My dismissal case is pending at the NLRC. What arguments should I submit at the next hearing?',
 'May pending labor case ako, ano ilalagay ko sa position paper?',
 'Which evidence should I present in the next hearing of my pending labor court case?'],
'labor.case_outcome_prediction': [
 'Will I win my illegal dismissal case?',
 'Sure bang mananalo ako sa kaso laban sa employer?',
 'Predict whether the labor tribunal will decide my termination dispute in my favor.'],
'consumer.banking_credit': [
 'My bank froze my savings account after charging an unexplained fee.',
 'Sobrang laki ng interest sa online lending app ko.',
 'A credit card provider billed me for a transaction I did not authorize.'],
'consumer.insurance': [
 'My insurer rejected my car accident claim. How do I challenge it?',
 'Ayaw bayaran ng insurance yung claim ko.',
 'Can this service advise on an insurance company denying coverage?'],
'consumer.investments': [
 'An investment broker refuses to release my trading funds.',
 'Di ko ma withdraw pera ko sa investment platform.',
 'My securities trading account was suspended. What regulator handles this investment dispute?'],
'consumer.telecommunications': [
 'My internet provider bills me every month even though the broadband service does not work.',
 'Walang signal internet plan namin pero tuloy singil ng telco.',
 'My mobile network added charges to a phone service subscription.'],
'consumer.data_privacy': [
 'An online seller posted a photo of my ID and my home address without permission.',
 'Pinost ng seller personal information ko sa Facebook.',
 'A shop leaked my phone number and address publicly. Where can I raise a privacy complaint?'],
'consumer.medical_malpractice': [
 'I think my surgeon made a mistake during an operation. Can I sue?',
 'Nagkamali doctor sa treatment ko, malpractice ba?',
 'A hospital patient wants legal advice about negligent medical care.'],
'consumer.real_estate': [
 'The developer is years late delivering the condo unit I paid for.',
 'Ayaw ibalik ng landlord deposit ko sa apartment.',
 'A subdivision developer changed the promised house layout after purchase.'],
'consumer.transportation': [
 'The airline cancelled my flight and refused a refund.',
 'Nawala bagahe ko sa flight at ayaw mag compensate airline.',
 'A bus operator refuses to address a passenger fare and service complaint.'],
'consumer.utility_billing': [
 'My electricity company billed me twice for the same meter reading.',
 'Doble singil sa water bill namin ngayong buwan.',
 'The electric utility charged an unexplained amount on my household bill.'],
'consumer.criminal_online_fraud': [
 'I paid a fake online seller who vanished. How do I request a criminal investigation?',
 'Scam seller yung page, nawala matapos ko magbayad. Paano magreport sa police?',
 'An online store disappeared after taking my payment and I need to report suspected cyberfraud.'],
}

CONTROLS = [
 ('ambiguity','How do I get my money back?','clarify'),
 ('ambiguity','They charged me again.','clarify'),
 ('ambiguity','My contract ended.','clarify'),
 ('outside','Write a Python function that sorts numbers.','refer_out_of_scope'),
 ('outside','How do I apply for annulment of my marriage?','refer_out_of_scope'),
 ('outside','My neighbor stole my bicycle. Can I file a theft complaint?','refer_out_of_scope'),
 ('noise','asdf qwer zxvbn','clarify'),
 ('noise','help please','clarify'),
 ('negation','I am not a government employee. My private company has not paid my wages.','retrieve_supported_evidence'),
 ('incidental','I work in a bank as a private employee. HR has not paid my salary.','retrieve_supported_evidence'),
 ('incidental','I work at a private hospital and our overtime is unpaid.','retrieve_supported_evidence'),
 ('incidental','My private company sells insurance. It has not paid my wages.','retrieve_supported_evidence'),
 ('incidental','I bought a phone from a store and its screen does not work.','retrieve_supported_evidence'),
 ('scope_boundary','What is the general purpose of minimum wage laws?','retrieve_supported_evidence'),
 ('mixed','My private employer has not paid my salary. Separately, my bank froze my account.','retrieve_supported_components'),
 ('mixed','The shop refuses a warranty repair and posted my personal information online.','retrieve_supported_components'),
 ('mixed','My employer in a private company owes overtime. Also, a retailer sold me a defective microwave.','retrieve_supported_components'),
 ('mixed','The store sold me a faulty fan. Separately, my landlord will not return my deposit.','retrieve_supported_components'),
 # Reserved controls start here, selected by family rather than random siblings.
 ('ambiguity_final','I need to complain about a payment.','clarify'),
 ('outside_final','What are the requirements for child custody after separation?','refer_out_of_scope'),
 ('outside_final','How do I cook sinigang for four people?','refer_out_of_scope'),
 ('noise_final','zzqq jjkk vvvv','clarify'),
 ('incidental_final','The bank where I am privately employed refuses to give my certificate of employment.','retrieve_supported_evidence'),
 ('negation_final','This is not a banking dispute. My shop sold me a faulty keyboard.','retrieve_supported_evidence'),
 ('mixed_final','I am a private employee and have unpaid wages. I also need advice on my insurance claim.','retrieve_supported_components'),
 ('mixed_final','My retailer will not fix a defective TV. My electric utility is overbilling me too.','retrieve_supported_components'),
]

def main():
    if (HERE/'frozen_manifest.json').exists():raise SystemExit('Already frozen; do not overwrite')
    supported={t for t in TOPICS if t not in {
        'labor.regional_minimum_wage_amounts','labor.ofw','labor.seafarers','labor.government_employment',
        'labor.kasambahay','labor.union_cba','labor.workers_compensation','labor.occupational_safety',
        'labor.retirement_pension','labor.pending_case','labor.case_outcome_prediction',
        'consumer.banking_credit','consumer.insurance','consumer.investments','consumer.telecommunications',
        'consumer.data_privacy','consumer.medical_malpractice','consumer.real_estate','consumer.transportation',
        'consumer.utility_billing','consumer.criminal_online_fraud'}}
    rows={'development':[],'reserved':[]}
    for topic,questions in TOPICS.items():
        for i,q in enumerate(questions):
            yes=topic in supported
            rows['reserved' if i==2 else 'development'].append({'case_id':f'{topic}.{i+1}',
                'topic_id':topic,'question_text':q,'expected_primary':topic.split('.')[0] if yes else 'out_of_scope',
                'expected_scope':'fully_supported' if yes else 'unsupported',
                'expected_route':'retrieve_supported_evidence' if yes else 'refer_out_of_scope',
                'provenance':'AI-authored synthetic diagnostic; not independent human gold'})
    for i,(family,q,route) in enumerate(CONTROLS):
        rows['reserved' if family.endswith('_final') else 'development'].append({
            'case_id':f'control.{i+1}','topic_id':family,'question_text':q,'expected_route':route,
            'provenance':'AI-authored synthetic diagnostic; not independent human gold'})
    checks={}
    for split,cases in rows.items():
        path=HERE/(split+'.jsonl');path.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
        checks[path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'count':len(cases)}
    (HERE/'frozen_manifest.json').write_text(json.dumps({'files':checks,'topic_count':len(TOPICS),
        'provenance':'Synthetic diagnostics authored before baseline; distinct reserved scenarios per topic. Not independent human evaluation.',
        'reserved_policy':'Do not run or inspect reserved predictions before final implementation freeze. Do not tune on final failures.'},indent=2)+'\n')
    print(checks)

if __name__=='__main__':main()
