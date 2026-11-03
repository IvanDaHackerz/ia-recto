"""Freeze 100 newly authored fictional Philippine scope tests before inference."""
from pathlib import Path
import hashlib,json,re,difflib
from collections import Counter

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
# topic | language style | question. New wording; no personal user messages.
LABOR='''wage_form|taglish|Sa pribadong furniture workshop sa Bulacan ako nagtatrabaho. Gusto ng may-ari na grocery coupons ang kalahati ng sweldo namin. Puwede ba iyon kahit cash ang kailangan namin?
pay_frequency|english|I label bottles for a private company in Iloilo. The next payday is always five weeks after the previous one. What wage-payment rule should I understand?
pay_delay|noisy_taglish|private printing press ung work q. 2 payday na lumipas, sabi ng boss wala pang bayad ung clients kya wait lng kmi sa sahod. ano pwede kong malaman tungkol dito?
loss_deductions|english|A private hardware store wants the whole missing-cash amount taken from whichever cashier was on duty, without checking who caused the shortage. What conditions apply to a wage deduction?
payroll_records|taglish|Empleyado ako ng private garment shop sa Taytay. Walang nakalagay na hours, rate, o deductions sa payroll sheet na pinapapirmahan sa amin. Anong records ang dapat tingnan?
mandatory_briefing|english|At a private cold-storage business in Davao, staff must attend a safety briefing before the attendance clock is switched on. Does being off the clock settle whether that time counts as work?
required_waiting|taglish|Private machine operator ako. Kapag nasira ang makina, bawal kaming umalis dahil anumang oras puwedeng paandarin ulit. Counted ba ang paghihintay na iyon sa oras ng trabaho?
meal_period|english|A private packaging plant in Pampanga gives a short lunch period and says continuous operation justifies it. What conditions govern a shorter meal break and whether it counts as working time?
short_breaks|taglish|Sa private office namin, binabawas sa oras ang dalawang maikling coffee break. Ano ang general rule para sa short rest breaks, hindi sa lunch break?
night_differential|noisy_taglish|pribadong bakery sa Cagayan de Oro aq, 12mn hanggang umaga ung duty. pareho lng hourly rate sa pang umaga. meron bang general rule sa night differential?
ordinary_overtime|english|A private sign-making shop in Cavite requires extra work after the ordinary daily hours to finish a rush order. The manager says a monthly salary automatically includes every extra hour. What is the general overtime rule?
undertime_offset|taglish|Sa pribadong bodega namin, gusto nilang ibawas ang late ko ngayong linggo sa overtime na natapos ko noong nakaraang linggo. Ano ang rule sa pag-offset ng undertime at overtime?
weekly_rest|english|A private convenience store stays open daily, and the owner says that means every employee must also work every day indefinitely. What is the general weekly-rest rule?
religious_rest|taglish|Private retail employee ako sa Marikina. Humingi ako ng rest day na tugma sa religious observance ko pero staffing daw ang problema. Paano tinitingnan ang preference na iyon at ang exceptions?
holiday_pay|english|A privately owned repair business in Baguio closed on a regular holiday. Management says closing the premises automatically removes holiday pay. What coverage conditions and exceptions should be considered?
thirteenth_basic|taglish|Rank-and-file worker ako sa private pet-supply store. Sabi sa amin pang-manager lang daw ang 13th month pay. Ano ang general rule at basic computation na kaya mong ipaliwanag?
thirteenth_separation|english|A rank-and-file employee left a private grocery partway through the year. Does your available evidence explain a proportionate thirteenth-month payment, or only a more general rule?
regular_activity|english|A private food-packaging company repeatedly hires the same people for short contracts to do its normal year-round production. What is the regular-employment activity test, without deciding the workers' status?
project_employment|taglish|Tinanggap ako ng private contractor para raw sa isang project pero walang malinaw na scope na sinabi noong hiring. Ano ang kailangang malinaw tungkol sa project noong umpisa?
seasonal_employment|noisy_taglish|sa pribadong fruit farm aq, tuwing picking season lang may work. seasonal daw kmi. ano ba ung exception na yan, wag muna ideclare kung regular aq o hindi.
probation_standards|english|A private logistics company first told a probationary employee the required performance standards when it announced non-regularization. What does the general rule say about communicating those standards?
probation_duration|taglish|Private office worker ako sa Pasig. Gusto kong maintindihan ang general probationary-employment rule at limit nito, bago ako pumirma sa bagong kontrata. Ano ang sinasabi ng sources?
dismissal_process|english|A private restaurant removed a cook after an accusation, without explaining the charge or giving a chance to respond. What procedural safeguards should be checked, without deciding if the dismissal was illegal?
security_tenure|taglish|Regular employee ako sa private bookstore sa Naga. Puwede raw akong alisin kapag gusto lang ng owner kahit walang dahilan. Ano ang security-of-tenure rule, general information lang?
closure_conditions|english|A private shoe workshop in Lipa plans to shut down. What are the general notice and separation-pay conditions, including the distinction involving serious business losses?
resignation_notice|taglish|Magreresign ako sa private events company. Walang emergency reason na binabanggit, gusto ko lang lumipat ng trabaho. Ano ang ordinary notice rule at ano ang general exceptions?
final_pay|english|I finished employment at a private optical shop in Cebu. The employer says final pay can be kept indefinitely until business improves. What release timeline does the available official statement describe?
certificate_employment|noisy_taglish|umalis na aq sa private salon. humingi aq ng COE pero sabi next quarter na raw nila aasikasuhin. may timeline ba mula nung request ko?
conciliation_purpose|english|A private workshop employee and employer disagree about unpaid wages but want to try resolving the disagreement first. What does SEnA assistance do, and does asking for help itself decide who wins?
conciliation_participants|taglish|May SEnA conference tungkol sa sahod ko sa private company. Paano ang general rule sa pagharap ng lawyer, representative, o agent? Hindi ko hinihinging mag-file ka para sa akin.'''

CONSUMER='''warranty_presentment|english|A shop in Antipolo sold me a desk lamp with a written warranty. It says it will not even receive the warranty claim because I kept only the receipt. What should be presented and what is the seller's role?
warranty_forwarding|taglish|May written warranty ang air fryer na binili ko sa local retailer. Sabi nila distributor lang ang puwedeng tumanggap ng claim at ayaw nila itong ipasa. Ano ang general obligation ng retailer?
warranty_terms|english|An appliance seller in Cabanatuan gave an express warranty but its written card does not say who will honor it, what is covered, or how long it lasts. What warranty information does the law require?
discounted_warranty|noisy_taglish|sale ung binili kong bagong keyboard sa store, may warranty card nmn. sira agad ung ilang keys pero sabi discount item kaya bawal claim. ano general warranty rules dito?
immediate_seller|english|I bought a blender directly from the manufacturer's showroom in Metro Manila. Staff say they have exactly the same role as an ordinary retailer when I present a warranty claim. How do the recorded roles differ?
product_quality|taglish|Bumili ako ng bagong folding table sa shop sa Angeles. Hindi kumakapit ang lock kaya hindi magamit nang normal. Ano ang general consumer rules sa product imperfection at remedies?
correction_period|english|A retailer in Bacolod has kept trying to correct a defect in a newly bought electric fan. What is the general correction-period pathway before choosing other remedies, and are there exceptions?
quantity_imperfection|taglish|Sealed pack ng tiles ang binili ko sa hardware. Mas kaunti ang laman kaysa quantity sa label at receipt. Ano ang remedies para sa quantity imperfection?
repair_parts|english|A repair shop in Dumaguete installed a used replacement component without asking me, although I brought the item for an ordinary paid repair. What rule concerns replacement parts and consumer authorization?
service_guarantee|taglish|Pinagawa ko ang rice cooker sa repair firm at binayaran ang service, pero bumalik agad ang parehong sira. Ano ang general service-guaranty rule, kung covered ang repair firm?
used_as_new|english|A store in Valenzuela advertised a speaker as brand-new, but it had an old user's account and clear repair marks when delivered. What is the general deceptive-sales rule without declaring this seller guilty?
false_certification|taglish|Sabi ng salesperson certified ang electric kettle pero ayaw nilang ipakita ang basehan ng certification claim. Ano ang general rule sa claims tungkol sa approval o certification, nang hindi muna sinasabing fake iyon?
misrepresented_features|english|A shop in General Santos promised a printer had a feature listed on its display card, but that model does not have it. What kind of consumer rule concerns misrepresented characteristics?
misleading_advertisement|english|A local advertisement in Batangas promises a vacuum cleaner can do a task that its product description says it cannot do. What does the general misleading-advertisement rule look at?
price_comparisons|taglish|May malaking 'half price' poster ang shop pero may duda ako kung tunay ang dating price na ginagamit nilang comparison. Ano ang general rule sa price comparisons sa advertisement?
price_ceiling|noisy_taglish|sa grocery sa Lucena, iba ung nasa shelf tag at mas mataas ung sa cashier. sabi lumang tag lang un pero ayaw sundin ung displayed price. ano rule dito?
tag_display|english|A homewares shop in Tagum displays goods without individual tags and says staff will quote prices after a buyer commits. What are the general price-display requirements and any permitted display alternatives?
exact_change|taglish|Bumili ako sa local bakery sa Tarlac. Candy ang gustong ibigay bilang sukli kahit cash ang hinihingi ko. Ano ang rule sa exact change at puwede bang ipawaive iyon?
unsafe_product|english|A newly bought extension cord from a retail shop in Rizal sparks during normal use. I want general product-safety information, not a damages computation or an automatic ruling against anyone. What source should I understand?
supplier_liability|english|A store sold a packaged desk fan without a clear maker or importer identity, and it developed a safety problem. How do the recorded rules distinguish supplier liability from manufacturer or importer liability?
laundry_quality|taglish|May bayad na laundry service sa San Pablo pero may permanent marks ang damit pagbalik at hindi nila inayos ang reklamo. Ano ang general remedies sa service-quality imperfection?
repair_quality|noisy_taglish|nagbayad aq sa repair shop sa Malolos para ayusin ung speaker. same issue pa rin pag uwi, ayaw iredo o ibalik bayad. ano options under general consumer service rules?
service_reperformance|english|A paid furniture-repair business in Roxas City left a chair unusable and refuses to repeat the service. What does the service-quality rule say about proper performance or other remedies?
consumer_complaint|taglish|Gusto kong magreklamo sa DTI tungkol sa sirang small appliance na binili sa tindahan sa Legazpi. Anong basic consumer-complaint information at limitation ang kaya mong ibigay?
online_wrong_item|english|A Philippine online merchant sent a different size of cabinet from the one in my order. What remedy conditions apply, and when does return of the original goods become relevant?
online_return_cost|taglish|Nag-avail ako ng replacement dahil iba ang model na ipinadala ng online shop sa akin. Sino ang sasagot sa return ng original item, at paano kung may napagkasunduang return period?
online_redress|english|I have filed a complaint about a faulty charger through a Philippine shopping platform's internal redress system and it remains unresolved. What prerequisite and exhaustion rule is recorded?
online_primary_liability|english|An e-retailer based in the Philippines says only the delivery platform can ever be responsible for a purchase problem. What is the recorded distinction between merchant and platform liability, without deciding the facts?
dti_procedure|english|A seller in Calamba refuses to discuss a faulty home appliance after I gave the receipt and described the problem. What basic DTI complaint process or referral information can this system provide?
change_of_mind_boundary|taglish|Ako mismo ang pumili ng wrong color ng storage box sa tindahan. Walang sira o maling delivery; nagbago lang ang gusto ko. Automatic ba ang refund sa consumer rules na hawak mo, o may limit ang masasabi mo?'''

MIXED='''both|english|My private café employer in Iligan pays wages through store-only vouchers. Separately, a local hardware shop charged more than its shelf price for a toolbox. Please handle the two issues separately.
both|taglish|Private warehouse employee ako sa Navotas at hindi nila binabayaran ang required extra hours. Hiwalay naman, defective ang bagong desk lamp ko at ayaw tanggapin ng retailer ang warranty claim. Ano ang general rules sa bawat concern?
both|english|A private manufacturer in Biñan keeps us working without a weekly rest day. An unrelated paid laundry business also returned damaged clothes. What can the system explain about each issue?
both|noisy_taglish|pribadong stockroom helper aq sa Mandaue, kinaltas ung nawawalang gamit kahit di pa inimbestigahan. hiwalay na shop ung nagbigay ng candy kapalit ng sukli ko. pakiseparate ung sagot.
both|english|I was dismissed by a private printing business without a chance to respond. Separately, an online furniture merchant delivered the wrong cabinet model. Explain the relevant rules without deciding either dispute.
both|taglish|Hindi pa nire-release ng private employer ko sa Olongapo ang final pay. Ibang transaction naman ang bayad kong appliance repair na hindi naayos. Ano ang general information para sa dalawang reklamo?
both|english|A private employer in Tacloban says my monthly salary removes any entitlement to night differential. A separate shop advertised a used monitor as new. Which rules concern these independent situations?
both|taglish|Private rank-and-file worker ako sa Dasmariñas at may tanong sa 13th month pay. Hiwalay na online seller ang ayaw tumanggap ng complaint ko tungkol sa wrong item. Ano ang kaya mong ipaliwanag sa bawat isa?
both|english|I was told probation standards only when a private employer ended my probation. Separately, a local retailer insists every express warranty can omit its duration. Please distinguish the employment and purchase questions.
both|noisy_taglish|private restaurant crew aq sa Laoag, ung late ko dati ibabawas daw sa OT ko. hiwalay, ung package ng tiles sa hardware kulang kumpara sa quantity sa label. anong rules sa dalawa?
both|english|A private contractor did not identify my supposed project at hiring. An unrelated electronics retailer refuses to forward my warranty claim to its distributor. What general rules apply to those separate concerns?
both|taglish|Private factory worker ako sa San Fernando. Bawal umalis habang waiting sa machine restart pero ayaw i-count ang oras. Ibang issue ang mas mataas na checkout price ng grocery kaysa displayed tag. Pakilinaw pareho.
labor_excluded|english|A private company's payroll in Zamboanga is released only every six weeks. Separately, my bank charged a credit-card annual fee. Explain the wage concern and identify the boundary for the banking issue.
labor_excluded|taglish|Private hotel employee ako sa Dumaguete at hindi ko makuha ang COE na nirequest ko. Hiwalay, kailangan ko ng rules sa claim ng car insurance ko. Alin ang covered ng project?
labor_excluded|english|My private employer in Bataan has no weekly day off for its staff. Separately, my sibling working for a foreign employer in Qatar asks about an overseas contract. Keep the two concerns distinct.
labor_excluded|noisy_taglish|empleyado aq ng private furniture shop sa Koronadal, walang night differential ung night duty. hiwalay ung reklamo ko sa internet provider na laging nawawala connection. ano lang kaya ng system?
labor_excluded|english|A private business in Las Piñas wants to deduct alleged stock loss without checking responsibility. Separately, I want a personalized estimate of my retirement pension. Which part can you explain?
labor_excluded|taglish|Private retail worker ako sa Vigan at may issue sa unpaid regular holiday. Ibang concern ang refund ng condo reservation na binayaran ko. Ihiwalay ang labor issue sa real-estate issue.
consumer_excluded|english|A retail shop in Puerto Princesa says my written product warranty disappears because the item was on sale. Separately, I dispute a charge for a hospital procedure. What is within the project scope?
consumer_excluded|taglish|Sira ang bagong desk fan na binili ko sa local shop sa Meycauayan. Hiwalay, may reklamo ako sa electric utility bill namin. Alin lang ang ordinary consumer-product concern dito?
consumer_excluded|english|A paid laundry service in San Jose del Monte refuses to redo a poorly performed service. Separately, a lending app is charging me loan interest I want to dispute. Explain only what the system covers.
consumer_excluded|noisy_taglish|online shop sa Pinas nagpadala ng ibang model ng blender sa order q. hiwalay ung nalaman kong personal data leak sa isang app. ano ang supported part?
consumer_excluded|english|A local repair shop in Talisay fitted different parts without my authorization. Separately, I want advice on whether to buy shares in a company. Separate the consumer service issue from the investment question.
both_excluded|english|A private employer in Tanauan withheld ordinary wages. An unrelated shop also charged above its displayed price. Separately, I need help dividing inherited land among siblings. Which concerns can this project handle?
both_excluded|taglish|Private employee ako sa Cainta, may issue sa probation standards. Hiwalay na retailer ang ayaw ipasa sa distributor ang warranty complaint ko. May concern din ako sa mobile-network bill. Pakihiwalay ang covered at hindi covered.'''

OUTSIDE='''banking|english|My savings bank in Cebu imposed a new maintaining-balance fee. Can this project tell me whether that banking charge is lawful?
lending|noisy_taglish|ung lending app ko sobrang taas ng interest at penalties, ano exact legal rate sa loan q sa Pilipinas?
insurance|taglish|Ayaw bayaran ng insurer ang travel-insurance claim ko matapos makansela ang trip. Paano ko sila hahabulin under insurance rules?
investments|english|I want a recommendation on which Philippine stock to buy next week and how much profit to expect. Can you choose one for me?
telecommunications|taglish|Postpaid mobile plan ko ang reklamo: may bill kahit matagal na disconnected. Ano ang telecom regulation at paano ko ipapa-adjust?
privacy|english|A mobile application disclosed private account details without permission. What data-privacy complaint and compensation can I pursue?
medical|english|I think a doctor's treatment at a hospital was negligent. Can you determine medical-malpractice liability and the damages I should claim?
real_estate|taglish|Nagbayad ako ng reservation sa condo developer at ayaw ibalik matapos akong umatras. Ano ang real-estate buyer rules dito?
transport|english|An airline changed my domestic flight and charged a rebooking fee. What passenger-rights regulation settles my refund?
utility|noisy_taglish|sobrang laki ng water bill namin sa bahay, parang mali reading ng meter. anong utility billing rule ang dapat sundin?
government_work|taglish|Permanent government employee ako sa city hall. Gusto kong malaman ang overtime at dismissal rules sa civil service, hindi private employment.
domestic_worker|english|I work as a live-in kasambahay for a family in Quezon City. What specific domestic-worker salary and rest rules govern my job?
seafarer|english|My question concerns a seafarer's overseas deployment contract and a shipboard injury compensation computation. Is that part of this project's legal coverage?
criminal_fraud|taglish|Humingi ng pera ang pekeng online seller tapos nawala ang account. Gusto ko ng criminal investigation at tulong para makilala ang scammer, hindi ordinary product replacement.
pending_case_prediction|english|I already have a labor case pending in court. Based on my side of the story, tell me if I will win and the exact damages the judge will award.'''

def main():
 if (BASE/'live-cases.json').exists():raise ValueError('Frozen inputs already exist; do not overwrite')
 all_rows=[]
 for group,block in [('L',LABOR),('C',CONSUMER),('M',MIXED),('O',OUTSIDE)]:
  entries=block.splitlines()
  assert len(entries)=={'L':30,'C':30,'M':25,'O':15}[group]
  for topic,style,q in (line.split('|',2) for line in entries):
   n=len(all_rows)+1;partial=group=='M' and topic!='both'
   domains=(['labor','consumer'] if group=='M' and topic in ['both','both_excluded'] else
            ['labor'] if group=='L' or (group=='M' and topic=='labor_excluded') else
            ['consumer'] if group=='C' or (group=='M' and topic=='consumer_excluded') else [])
   target={'expected_primary':{'L':'labor','C':'consumer','M':'mixed','O':'out_of_scope'}[group],
           'expected_scope':'unsupported' if group=='O' else 'partially_supported' if partial else 'fully_supported',
           'expected_route':'refer_out_of_scope' if group=='O' else 'retrieve_supported_components' if group=='M' else 'retrieve_supported_evidence',
           'expected_domains':domains,'relevant_ids':[],'concerns':[],
           'retrieval_judgment':'no_candidates' if group=='O' else 'unjudged'}
   all_rows.append({'case_id':f'RD31_{n:03d}','family_id':f'RD31_{n:03d}','group':group,'topic':topic,
                    'language_style':style,'question_text':q,'AI_authored':True,'independent_human_gold':False,
                    'development_replay':False,'source_case':target,
                    'input_provenance':'New fictional wording authored by Codex before this run; purposive scope test, no independent human/legal gold.'})
 assert len(all_rows)==100
 old={}
 def collect(value,path):
  if isinstance(value,dict):
   if isinstance(value.get('question_text'),str):old.setdefault(' '.join(value['question_text'].casefold().split()),str(path))
   for k,v in value.items():
    if k not in ['packet','result','sources','parent_text']:collect(v,path)
  elif isinstance(value,list):
   for v in value:collect(v,path)
 names={'live-cases.json','cases.json','cases.jsonl','benchmark_queries.jsonl','concern_cases.jsonl','training_atoms.jsonl','unique_training_atoms.jsonl'}
 for p in (ROOT/'outputs').rglob('*'):
  if p.name not in names or BASE in p.parents:continue
  try:
   if p.suffix=='.json':collect(json.loads(p.read_text(encoding='utf-8')),p.relative_to(ROOT))
   else:
    for line in p.read_text(encoding='utf-8').splitlines():collect(json.loads(line),p.relative_to(ROOT))
  except (ValueError,UnicodeError):continue
 texts=[' '.join(r['question_text'].casefold().split()) for r in all_rows]
 assert len(set(texts))==100 and not set(texts)&set(old),'Duplicate question wording'
 nearest=[]
 for row,text in zip(all_rows,texts):
  candidates=difflib.get_close_matches(text,old,n=1,cutoff=.72)
  if candidates:
   other=candidates[0];nearest.append({'case_id':row['case_id'],'similarity':difflib.SequenceMatcher(None,text,other).ratio(),'old_text':other,'old_file':old[other]})
 save=lambda n,v:(BASE/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 save('freshness-audit.json',{'previous_unique_question_texts_checked':len(old),'exact_duplicates':0,'new_unique_wordings':100,'nearest_text_overlaps':nearest,'limitations':'New wording within established scope is not a guarantee of new semantic families, human authorship or statistical independence.'})
 save('live-cases.json',all_rows)
 h=hashlib.sha256((BASE/'live-cases.json').read_bytes()).hexdigest()
 save('live-case-manifest.json',{'created_on':'2026-10-31','cases_sha256':h,'input_forms':100,
      'groups':dict(Counter(r['group'] for r in all_rows)),'language_styles':dict(Counter(r['language_style'] for r in all_rows)),
      'new_question_texts':100,'independent_human_questions':0,'expectations_frozen_before_inference':True,
      'sampling':'Purposive Philippine scope coverage; not a random population sample or an independent human/legal holdout.',
      'legal_accuracy_measured':False,'external_destination':'Configured Together.ai provider; fictional questions and eligible public legal-source excerpts only.'})
 save('acceptance-criteria.json',{'purpose':'Submission-readiness engineering check, not professional legal approval',
      'criteria':['All 100 inputs produce a readable response or a clearly recorded failure',
                  'Topic, scope and supported-domain expectations remain frozen',
                  'Outside-scope concerns do not receive substantive legal explanations',
                  'Returned citations belong to their concern and equal stored source spans',
                  'AI text addresses the question and preserves actors, exceptions and limits',
                  'Fallbacks and provider errors are counted, not silently discarded',
                  'No model weights, confidence thresholds or UI redesign without a demonstrated defect'],
      'AI_enabled_for_every_input':True,'fresh_wording':True,'independent_human_gold':False,
      'full_batch_then_review':True,'no_relabeling_after_inference':True})
 lines=['# 100 fresh submission-readiness questions','',
        'AI-authored fictional development tests. Expected topic/scope/routes frozen before inference. English, Taglish and noisy typing.','']
 for r in all_rows:lines += [f"## {r['case_id']} · {r['group']} · {r['topic']}",'',r['question_text'],'']
 (BASE/'QUESTIONS.md').write_text('\n'.join(lines),encoding='utf-8')
 print(json.dumps({'questions':100,'groups':dict(Counter(r['group'] for r in all_rows)),
                   'styles':dict(Counter(r['language_style'] for r in all_rows)),
                   'previous_unique_questions_checked':len(old),'exact_duplicates':0,'near_matches':len(nearest)},indent=2))

if __name__=='__main__':main()
