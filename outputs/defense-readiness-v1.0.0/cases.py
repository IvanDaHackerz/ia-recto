"""New fictional development questions, frozen before this study's inference."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
GROUPS={
'labor':[
('wages','Restaurant staff ako sa private business. Every month lang kami pinapasweldo kahit wala namang disaster. Anong schedule ang nasa labor rules?'),
('wages','My private employer says the missing cash in our till will be divided equally among everyone on duty. What conditions apply to deductions?'),
('wages','Private employee ako. May payroll issue: hindi pa pumapasok yung sahod namin. Bank transfer lang yung payment method, hindi bank fees ang reklamo ko.'),
('hours','Private warehouse worker here. We have to wait at the site until the supervisor releases us. Does the required waiting count as working time?'),
('hours','Sa private company ako. Required yung meeting bago magbukas, pero off the clock daw yun. What rules cover time worked?'),
('rest','Six days na sunod-sunod ang duty sa private shop. How does the weekly rest period work?'),
('rest','I work for a private firm. Management keeps changing my weekly rest day. Who sets the schedule under the recorded rule?'),
('overtime','Private employee ako. Dalawang oras akong pinatapos ng inventory after my ordinary eight-hour shift. Anong overtime rule ang relevant?'),
('overtime','Our private employer says a short workday yesterday cancels out our extra hours today. What does the law say about offsetting undertime?'),
('holiday','Private retail employee ako. Sarado ang shop sa regular holiday; no work happened. What holiday-pay rule and coverage exceptions should I check?'),
('holiday','At a private company, what pay rule applies when a covered employee works on a regular holiday?'),
('status','My private employer calls me a project worker, but the contract never identifies the project. Please explain the recorded employment-status test without deciding my case.'),
('status','Private employee ako, seasonal daw yung work ko. How is seasonal work treated under the regular-employment rule?'),
('status','Private employee ako. My contract says casual, but my tasks are part of the usual business. What does the recorded definition actually require?'),
('status','I am on probation at a private company. What does the recorded rule say about telling me the standards for regular employment?'),
('dismissal','Private worker ako. Pinauwi ako nang tuluyan after an accusation, without a written explanation of what I allegedly did. What notice safeguards are recorded?'),
('dismissal','A private company says my position is redundant. I want the general termination framework, not a prediction that I will win.'),
('dismissal','My private employer dismissed me for misconduct. Does a stated cause automatically remove the need for notice and an opportunity to respond?'),
('sena','Private employee ako with unpaid wages. What is the role of conciliation before a labor dispute reaches the proper office?'),
('sena','Can you explain what a mediator does at SEnA for a private-sector wage dispute? I am not asking you to file anything.'),
('final_pay','I resigned from a private company. How soon must they release my final pay?'),
('thirteenth','Private employee ako. May rule ba about 13th month pay?'),
('coe','Former private employee ako. Ayaw ibigay yung certificate of employment ko. What source covers this?'),
('breaks','Private employee ako. What is the recorded meal-period rule during an ordinary workday?'),
],
'consumer':[
('quality','I bought a new electric fan from a store. The motor never runs, but there was no injury or fire. Which product-quality remedy framework is relevant?'),
('quality','Kakabili ko ng kettle sa retail store. Leaking yung base, unusable sya. Hindi safety damages ang tanong ko; ano yung defect-remedy framework?'),
('quality','The new cabinet I bought from a shop arrived with missing hinges. What general consumer-quality rules can I inspect?'),
('warranty','A retail shop says only the manufacturer handles the written warranty. What role does the retailer have when a customer brings a warranty claim?'),
('warranty','I bought an appliance from a factory showroom and have its written warranty. What does the recorded warranty provision say about honoring a claim?'),
('warranty','May warranty card yung blender na binili ko sa shop, pero ayaw nila tanggapin ang complaint. Anong recorded warranty process ang relevant?'),
('remedies','If a defective consumer product remains unfixed after the applicable correction period, what choices does the recorded provision describe?'),
('remedies','Can a buyer and supplier agree to change the usual correction period for a product imperfection? Please keep the limits in the source.'),
('remedies','My store-bought fan is defective. Is a refund the only remedy listed in the recorded product-imperfection rule?'),
('price','Sa grocery, mas mataas yung checkout charge kaysa price label sa shelf. What price rule covers that?'),
('price','The cashier kept the small change because they said they had no coins. It was a regular store purchase. What consumer rule applies?'),
('price','A shop sells items too small for individual price tags. Does using a nearby price list change the rule against charging more than the displayed price?'),
('ads','An online retailer advertises a laptop as brand-new but the unit was refurbished. What general deceptive-representation rule fits this allegation?'),
('ads','A furniture shop advertised solid wood but delivered particle board. Which general advertising rules apply, without assuming the allegation is proved?'),
('ads','The sales page claims a household device has government approval. I cannot verify that claim. How should the recorded deceptive-sales rule be explained?'),
('service','I paid a laundry business for cleaning, but the clothes came back unclean. No one was injured. What service-quality rules are relevant?'),
('service','Nagbayad ako sa appliance repair shop pero hindi nila ginawa yung agreed repair. Consumer service issue lang ito. What recorded remedies can I read?'),
('service','I paid a commercial cleaning service, but the work did not match the agreed description. What source explains service imperfections?'),
('online','An online store sent a cheaper model than the one in my order. What conformity remedies are recorded for online retail?'),
('online','Online retail purchase ito. The merchant wants me to pay the shipping to return the wrong item. What does the recorded return rule say?'),
('online','I have an online shopping complaint. What does the recorded rule say about using the platform complaint process before going to a government agency?'),
('complaint','I want to complain to DTI about a defective household appliance I bought. What general complaint framework is in the corpus?'),
('safety','A store-bought charger overheats during normal use and burned the table. What is the recorded product-safety liability framework?'),
('framework','As a person buying household goods from ordinary shops, what consumer interests does the Consumer Act protect?'),
],
'mixed':[
('two_supported','Private employee ako; unpaid yung ordinary overtime ko. Separately, the grocery cashier kept my change. Please handle each concern.'),
('two_supported','My private employer deducts inventory losses from everyone. I also bought a defective kettle from a shop. Explain the two relevant frameworks separately.'),
('two_supported','I have a private-sector dismissal concern, and a retailer refuses to receive my written warranty claim. Which parts can this project handle?'),
('two_supported','Private employee ako with missing holiday pay. My online retailer also sent the wrong product. I want separate source-based information.'),
('two_supported','My private employer has not paid my salary. Also, an online store advertised a new laptop but shipped a used one.'),
('two_supported','May overtime concern ako sa private job ko, tapos may kulang na sukli sa grocery purchase ko. Both issues matter.'),
('two_supported','At a private company I was dismissed without written notice. Separately, a laundry business ruined the agreed cleaning service. What topics fit your scope?'),
('two_supported','Private shop employee ako asking about weekly rest. Separately, I bought a charger from another retailer that overheats. Please distinguish the concerns.'),
],
'partial':[
('labor_excluded','My private employer has not paid wages. Separately, my bank charged account fees that I want to dispute.'),
('consumer_excluded','The appliance store refuses my warranty claim. My landlord also kept the rental deposit.'),
('labor_excluded','Private employee ako with unpaid overtime. My insurance company separately denied a medical claim.'),
('consumer_excluded','My online retailer sent the wrong model. Separately, my telecom provider has an internet billing dispute.'),
('labor_excluded','I was dismissed by a private employer without notice. I also need advice about child custody.'),
('consumer_excluded','The grocery cashier did not give my change, and a hospital separately overcharged for a medical procedure.'),
('all_three','Private employee ako with unpaid wages. A store also sold me a defective fan, and my landlord kept my deposit.'),
('consumer_excluded','Government employee ako with an overtime complaint. Separately, I bought a defective rice cooker from a retail shop.'),
],
'outside':[
('bank','My bank increased the transfer fee on my savings account. Can you resolve this banking dispute?'),
('insurance','My insurer denied my vehicle insurance claim. What should I file?'),
('rent','My landlord refuses to return the security deposit for my apartment.'),
('government','Government employee ako. I want to dispute my overtime pay.'),
('overseas','OFW ako working overseas. Hindi pa binabayaran yung sahod ko.'),
('privacy','A shop publicly posted my ID and phone number. I am only asking about the privacy breach, not a defective purchase.'),
('medical','I want to sue a doctor over a medical procedure. This is not an ordinary retail purchase.'),
('criminal','Someone stole my bicycle. What criminal case should I file?'),
]}

def build():
    if (BASE/'cases.json').exists():raise SystemExit('Frozen input already exists')
    cases=[]
    for group,items in GROUPS.items():
        for topic,question in items:
            number=len(cases)+1
            domains=([group] if group in {'labor','consumer'} else ['labor','consumer'] if group=='mixed' or topic=='all_three'
                     else ['labor'] if topic=='labor_excluded' else ['consumer'] if group=='partial' else [])
            cases.append({'case_id':f'DEF_{number:03d}','question_text':question,'topic':topic,'group':group,
                          'split':'confirmation' if number%3==0 else 'discovery',
                          'expected_primary':'out_of_scope' if group=='outside' else 'mixed' if group in {'mixed','partial'} else group,
                          'expected_scope':'unsupported' if group=='outside' else 'partially_supported' if group=='partial' else 'fully_supported',
                          'expected_route':'refer_out_of_scope' if group=='outside' else 'retrieve_supported_components' if group in {'mixed','partial'} else 'retrieve_supported_evidence',
                          'expected_domains':sorted(domains),'AI_authored':True,'independent_human_gold':False})
    # This study has 72 cases; none of the confirmation observations may guide fixes.
    raw=(json.dumps(cases,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    (BASE/'cases.json').write_bytes(raw)
    (BASE/'manifest.json').write_text(json.dumps({'count':len(cases),'sha256':hashlib.sha256(raw).hexdigest(),
        'discovery':sum(c['split']=='discovery' for c in cases),'confirmation':sum(c['split']=='confirmation' for c in cases),
        'authorship':'AI-generated fictional development questions','expectations_frozen_before_inference':True,
        'confirmation_policy':'Inspect only after the repair batch; disclose any later tuning as development reuse.'},indent=2)+'\n',encoding='utf-8')
    print('Frozen',len(cases),'new cases')

if __name__=='__main__':build()
