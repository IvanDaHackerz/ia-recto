"""Freeze 100 new fictional, AI-authored in-scope application probes."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
GROUPS={
 'labor.wages_payment':[
  'My private printing employer has missed three scheduled paydays even though we finished the orders. What wage-payment rules can you explain?',
  'Private warehouse worker ako. Twice a month daw ang sweldo pero halos isang buwan nang walang pumapasok. Ano yung general rule?',
  'The private bakery gives staff store coupons instead of cash wages. What do the sources say about the form of wage payment?',
  'Sa private factory ako. May bawas sa sahod para sa nawawalang tools pero walang explanation o agreement. Anong wage deduction rules ang relevant?',
  'My private employer says the payroll can be delayed indefinitely because business is slow. Can you explain the general payment schedule and qualifications?',
 ],
 'labor.hours_of_work':[
  'Our private restaurant requires a daily safety briefing before anyone may clock in. Does the recorded working-time rule discuss required briefings?',
  'My private factory supervisor makes us remain beside the idle machine until materials arrive. How do the sources describe waiting time as working time?',
  'Private hotel employee ako. Pinapagawa ang turnover notes after clock-out every shift. Ano ang general information tungkol sa hours worked?',
  'I work at a private office and must answer the reception desk throughout the scheduled meal break. What recorded rules describe hours worked and meal periods?',
  'Sa private warehouse, required kami mag-inspect ng equipment bago magsimula ang paid shift. Counted ba as working time yung required inspection?',
 ],
 'labor.rest_days':[
  'My private grocery employer schedules me every day with no weekly rest period. What general rest-day rules can you explain?',
  'Private factory worker ako. Sinabi ng supervisor na wala muna kaming day off for the entire month. What do the records say about weekly rest?',
  'Our private employer moved the weekly rest day from Sunday to Tuesday. Is there general source information on scheduling rest days?',
  'I work for a private retail company and the manager wants staff to work on their assigned rest day. What conditions and general rules are recorded?',
  'Sa private office namin, binibilang na rest day yung araw na required pa rin kaming magreport for work. Anong weekly-rest information ang pwede kong basahin?',
 ],
 'labor.overtime_pay':[
  'I am a private factory employee working beyond eight hours, but payroll gives only the usual daily wage. Explain the general overtime rule without deciding my individual entitlement.',
  'Private employer ko pinapag-stay kami after shift pero walang overtime pay sa payslip. What can the recorded overtime provisions explain?',
  'The private warehouse counts my short workday against overtime from another day. What do the sources say about offsetting undertime and overtime?',
  'My private employer says a monthly salary automatically includes all extra hours. What general overtime information and qualifications are available?',
  'Private restaurant worker ako. Required kami magwork extra hours to finish a rush order, pero ordinary pay lang. Ano ang general overtime-pay framework?',
 ],
 'labor.holiday_premium_pay':[
  'Our private grocery stayed open on a regular holiday and payroll paid only the ordinary daily amount. What holiday-pay and premium rules are recorded?',
  'My private office closed on Christmas Day and no work was performed. Can you explain the general holiday-pay rule and its exceptions?',
  'Private factory employee ako. Nagtrabaho ako on a regular holiday na assigned rest day ko rin. What recorded holiday-pay information covers that combination?',
  'The private hotel payroll treats every holiday exactly the same. What source information distinguishes regular-holiday pay from other holiday situations?',
  'Private shop worker ako at holiday pay yung concern ko. Sabi ng manager automatically unpaid kapag sarado ang shop on a regular holiday. Ano ang general recorded rule?',
 ],
 'labor.thirteenth_month_pay':[
  'I worked five months at a private cafe before resigning. What information is available about a proportionate thirteenth-month payment?',
  'Private company employee ako at kulang daw ang 13th month dahil hindi buong taon ang service ko. May source information ba kayo tungkol dito?',
  'My private employer says probationary staff never receive thirteenth-month pay. What can your reviewed records establish?',
  'Sa private restaurant ako, basic salary at allowances ang nasa payslip. What source information is available about computing 13th-month pay?',
  'I left a private warehouse job during the year and want to understand thirteenth-month pay generally. Please explain what your available sources can and cannot support.',
 ],
 'labor.employment_contracts':[
  'Our private employer keeps issuing project contracts for the same ordinary office work, without identifying any project. What does the recorded employment-status framework say?',
  'Private company worker ako. Walang written contract pero regular office duties ang ginagawa ko. Can you explain the general source provisions on employment status?',
  'My private employer calls me casual even though my tasks are part of its usual business. What general regular-versus-casual employment information is recorded?',
  'The private factory contract says project-based but never states when the project will finish. What employment-contract and status information can I inspect?',
  'Private retail employee ako. Paulit-ulit ang short employment contracts for the same daily duties. Explain the general status rules without deciding my case.',
 ],
 'labor.termination_due_process':[
  'My private employer removed me permanently from the work schedule without written notice. What dismissal-process information is available?',
  'Private factory employee ako. May accusation against me pero tinanggal agad bago ako nakapagpaliwanag. What recorded due-process rules can you describe?',
  'The private company gave me a dismissal letter but never let me respond to the charges. Can you explain the general notice and opportunity-to-answer requirements?',
  'My private employer says poor sales justify dismissing staff immediately with no process. What general termination information and qualifications are in the sources?',
  'Private hotel worker ako. General information lang tungkol sa employer dismissal ang kailangan ko, including notice and procedure, hindi prediction ng case result.',
 ],
 'labor.final_pay_coe':[
  'I resigned from a private company and HR refuses to issue a certificate of employment. What can your sources explain about COE requests?',
  'Private employer ko ayaw i-release ang final pay kahit completed na yung clearance. What source information is available?',
  'My former private employer says a COE can be withheld because I resigned instead of being dismissed. What do your available records support?',
  'Private warehouse employee ako before. Sinasabi ng HR na next year pa yung final pay. Can you explain any available guidance and source limits?',
  'I need general information about final pay and employment certificates after leaving a private job. Please distinguish what the available records actually cover.',
 ],
 'labor.complaint_referral':[
  'My private employer has not paid salary and I want general information about starting a SEnA request for assistance. What is the recorded process?',
  'Private factory worker ako. Paano generally nagsisimula ang conciliation request sa SEnA for unpaid wages?',
  'I have a private-employment wage dispute and want to know what happens at a SEnA conciliation meeting. Explain the recorded process.',
  'Sa SEnA conference about my private job, confidential ba yung discussion at may rule ba tungkol sa recording? General source information lang.',
  'For a SEnA meeting about my private-employer dispute, what do the sources say about appearing with a lawyer, agent, or representative?',
 ],
 'consumer.general_framework':[
  'What basic consumer-protection objectives are written in the Consumer Act for ordinary household purchases?',
  'Bumibili ako ng ordinary goods from retailers. Explain the general Consumer Act framework and what consumer interests its policy protects.',
 ],
 'consumer.defective_products':[
  'The retailer sold me a new rechargeable lamp, but its charging socket is cracked inside the sealed box. What consumer defect rules can you explain?',
  'Bumili ako ng bagong rice cooker sa appliance shop. Sira pala yung switch at hindi gumagana. Anong consumer information ang relevant?',
  'My newly purchased electric fan from a retailer stops working immediately. Can you explain what the stored product-defect provisions actually cover?',
  'Yung bagong blender galing sa retailer has a broken motor. Hindi ito insurance or repair-service issue; defective product ang concern ko. What rules can I inspect?',
 ],
 'consumer.warranties':[
  'The retailer refuses the written warranty on my washing machine because I bought it at a discounted price. Explain the recorded warranty framework.',
  'May written warranty yung binili kong fan pero ayaw tanggapin ng shop ang warranty claim. What do the sources say about enforcing a warranty?',
  'A retailer says I must provide extra paperwork beyond my warranty card and receipt before it will accept my defective product. What warranty information is recorded?',
  'The shop says only the manufacturer can accept a warranty claim and it will not help me at all. Can you explain the recorded seller and retailer warranty provisions?',
 ],
 'consumer.repair_replace_refund':[
  'The retailer repaired my defective microwave repeatedly and it still fails. What recorded rules concern replacement or refund after repair attempts?',
  'Sira yung bagong electric kettle from an appliance retailer at ayaw nilang palitan o i-refund. Explain the available consumer remedy provisions and their conditions.',
  'A shop offers another repair for a product that remains faulty after several attempts. What does the recorded warranty text say about repair, replacement, or refund?',
  'The retailer took my defective toaster back but refuses to discuss replacement or returning the purchase price. What general remedy information is supported by your records?',
 ],
 'consumer.deceptive_unfair_sales':[
  'A retailer passed off a used laptop as brand new and hid the fact that it had been refurbished. What deceptive-sales rules are recorded?',
  'The shop described a display speaker as a brand-new unit without revealing its prior use. Explain the general consumer rule about that type of sales representation.',
  'The seller hid a mandatory service fee until after I had already paid for a household appliance. What consumer-sales practice information can you explain?',
  'A sales representative says the product has manufacturer approval even though the supplied paperwork says otherwise. What recorded deceptive-sales information is relevant?',
 ],
 'consumer.misleading_advertising':[
  'A retailer advertises a jacket as waterproof, but the delivered label says it must stay dry. What recorded rules concern misleading advertisements?',
  'Yung ad ng shop says solid wood yung table pero yung delivered product says laminated board. Explain the consumer advertising framework.',
  'The online advertisement promises a feature that the product manual says this model does not have. What information is available about false advertising?',
  'A store advertisement describes an ordinary lamp as certified for a safety standard, but the packaging does not support that claim. Explain only the recorded advertising rules.',
 ],
 'consumer.price_tags':[
  'The supermarket shelf tag lists one price, but the cashier charges a higher price for the same item. What price-tag rules can you explain?',
  'Nasa price tag ng appliance yung lower amount pero mas mataas ang singil sa checkout. Anong recorded consumer rule ang relevant?',
  'The grocery says it cannot give exact change and substitutes candy without asking me. What information is recorded about shortchanging?',
  'The cashier keeps the small remaining change because the store has no coins. Can you explain the recorded exact-change framework?',
 ],
 'consumer.product_safety':[
  'The extension cord I bought from a hardware retailer has exposed live wiring near the handle. Explain the recorded consumer product-safety information.',
  'Bagong electric fan from an appliance shop, pero may sparks at amoy sunog kapag ginagamit. What product-safety rules can I inspect?',
  'A retailer sold a toy whose casing becomes dangerously hot during ordinary use. What general product-safety and defect information is supported by the sources?',
  'The kettle from a retailer has exposed metal carrying electricity. What product-safety information can you explain without assuming the outcome of a complaint?',
 ],
 'consumer.service_complaints':[
  'A paid laundry service shrank my curtains and refuses to address the damage. What recorded consumer-service rules are relevant?',
  'Nagbayad ako sa repair service para ayusin yung cabinet pero lalo nilang sinira. What consumer service-quality information can you explain?',
  'The paid furniture repair service returned my chair with new damage and says it has no responsibility. Explain the recorded rules on service imperfections.',
  'A cleaning service damaged the clothes it agreed to clean. What general consumer service-quality provisions and qualifications are available?',
 ],
 'consumer.online_transactions':[
  'The online business seller delivered the wrong model of household fan and refuses replacement. What online consumer remedies are recorded?',
  'Paid na yung desk ko sa online retailer pero paulit-ulit na delayed ang delivery at ayaw i-process ang refund. Explain the available online transaction rules.',
  'An online retailer delivered an incomplete appliance package and ignores my request to correct the order. What source information concerns online consumer remedies?',
  'The online marketplace tells me to complete its internal complaint process before contacting a government agency. What recorded online-consumer redress rules can you explain?',
 ],
 'consumer.complaint_referral':[
  'A retailer ignores my defective-appliance complaint even though I kept the receipt. What general information is available about beginning a DTI consumer complaint?',
  'I want to understand the Consumer Act complaint and investigation process for an ordinary retail purchase. What do the stored provisions describe?',
 ],
 'mixed':[
  'My private employer has missed salary payments. Separately, a retailer refuses the written warranty on my fan. Can you explain the supported rules for both?',
  'Private factory job ko walang overtime pay. Yung online retailer ko naman wrong appliance model ang pinadala. Please handle the two concerns separately.',
  'My private employer dismissed me without written notice. Separately, a shop sold me a refurbished tablet as brand new. Explain the general source information for each.',
  'Our private office requires a briefing before clock-in. A paid laundry service also damaged my clothes. What recorded rules concern each issue?',
  'My private employer gives no weekly rest day. Separately, the grocery cashier charges more than the displayed shelf price. Explain the two topics separately.',
  'Private company employee ako with unexplained wage deductions. May defective blender din akong binili sa retailer. What source information covers each concern?',
  'My private restaurant employer pays only ordinary wages for work on a regular holiday. Separately, an appliance retailer refuses my written warranty. Explain both general frameworks.',
  'I want general SEnA process information for unpaid wages at my private job. Separately, an online seller refuses to replace a faulty kettle. What is supported for each?',
  'The private company labels my ordinary office job project-based. Separately, a store advertisement misstates the features of a speaker. Explain the employment and consumer information separately.',
  'My private employer has delayed wages. Separately, a hardware retailer sold an extension cord with exposed live wiring. Please explain the recorded rules for each concern.',
 ],
}

def main():
    target=HERE/'cases.json';assert not target.exists(),'Never replace frozen questions.'
    cases=[]
    for topic,questions in GROUPS.items():
        primary=topic.split('.')[0]
        for q in questions:
            cid=f'AI100_{len(cases)+1:03d}'
            domains=['consumer','labor'] if primary=='mixed' else [primary]
            expected={'expected_primary':primary,'expected_scope':'fully_supported',
                      'expected_route':'retrieve_supported_components' if primary=='mixed' else 'retrieve_supported_evidence',
                      'expected_domains':domains,'expected_excluded':False,'relevant_ids':[],
                      'concerns':[],'retrieval_judgment':'unjudged','question_text':q,'topic_ids':[topic]}
            cases.append({'case_id':cid,'question_text':q,'family_id':cid,'topic_id':topic,
                          'known_source_gap':topic in {'labor.thirteenth_month_pay','labor.final_pay_coe'},
                          'origin':'AI-authored fictional development question','source_case':expected})
    assert len(cases)==100
    assert len({c['question_text'] for c in cases})==100
    target.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'count':100,'primary_counts':{'labor':50,'consumer':40,'mixed':10},
              'cases_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
              'expectations_frozen_before_inference':True,'independent_human_gold':False,
              'known_source_gap_cases':10,'question_text_contains_personal_chat':False}
    (HERE/'case-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
