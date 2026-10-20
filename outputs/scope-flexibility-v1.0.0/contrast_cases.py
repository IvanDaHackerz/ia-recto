"""Second inspected diagnostic round: contrastive boundaries and language."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
CASES={
'labor':[
 'My employer is an insurance company and has not paid my wages.',
 'I work for a private hospital. I have no weekly rest day.',
 'I work at a private school and get deductions from my salary without an explanation.',
 'My private employer serves government clients and owes me overtime.',
 'Kulang ang suweldo ko sa kumpanya, san magtatanong?',
 'ndi pa binibigay sweldo ko ng boss ko',
 'My employer pays by bank transfer but has stopped sending my wages.',
 'My manager makes us work during lunch. Does that count as working time?',
 'We need to report for mandatory training on our day off at the company.',
 'HR says no COE until I sign a waiver. What are the general rules?',
 'My employer wants me to resign immediately. What basic notice rules should I know?',
 'What does probationary employment mean?',
 'Can employees ask about overtime pay even without a written employment contract?',
 'Sa pribadong kumpanya ako, kulang 13th month na binigay sa akin.',
],
'consumer':[
 'The store repair work was poor and I paid for it. What can I ask about?',
 'I paid a laundry employee for cleaning but the clothes came back stained.',
 'A retail shop employee refused my defective product warranty.',
 'The product is a book about retirement pensions, but the seller sent a damaged copy.',
 'I bought a mobile phone, not a service plan. The handset is defective.',
 'The shop sold me a defective electricity meter for my hobby project.',
 'Ang binili kong laruan may sirang gulong, ayaw palitan sa tindahan.',
 'The repair business promised to fix my computer but returned it still broken.',
 'A seller advertised a discount that did not exist at checkout.',
 'Hindi tama sukli sa supermarket, san magreklamo?',
 'An online store is late shipping an order but I can still contact it. Is this a consumer complaint?',
 'May resibo ako pero di tumatanggap ng warranty yung tindahan.',
 'The seller wants me to pay for a defect that was already there when I bought the item.',
 'What is meant by an implied warranty on consumer goods?',
],
'out_of_scope':[
 'I am a government hospital nurse and my overtime pay is unpaid.',
 'I am a household domestic worker. My employer has not paid my wages.',
 'I am an OFW working overseas for a private company. My wages are late.',
 'I am a seafarer employed by a private shipping company. HR refuses my COE.',
 'The online lending company says my loan interest doubles next week.',
 'Our telecommunications provider has no service but keeps billing us.',
 'My private employer withheld my SSS pension contribution. What pension benefits can I claim?',
 'An insurance company denied coverage for my broken appliance under a separate insurance policy.',
 'A public hospital doctor injured me during treatment.',
 'My phone service plan has a billing dispute. I did not buy a phone handset.',
 'My bank deducted a charge from my salary account without permission.',
 'My employer posted my personal address publicly. I want privacy advice.',
 'Can you tell me whether I will win against my private employer?',
 'What is the exact minimum wage rate this month in my region?',
],
'mixed_partial':[
 'My private company owes unpaid salary and my landlord refuses my rental deposit.',
 'The shop sold me a faulty keyboard and leaked my home address.',
 'My private employer owes overtime and my insurer rejected a claim.',
 'I have a broken appliance warranty dispute. Separately, my telecom bill is wrong.',
],
'clarify':[
 'refund pls',
 'bayad ko di ko nakuha ano gagawin',
 'The service is bad. What should I do?',
 'Can you check my papers?',
 '???????????',
],
}
if __name__=='__main__':
 import sys
 ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
 import joblib
 from classifier_runtime import predict_records
 b=joblib.load(ROOT/(sys.argv[2] if len(sys.argv)>2 else 'outputs/item10-classifier-v1.5.16')/'classifier.joblib')
 records=[]
 for label,texts in CASES.items():
  for text,result in zip(texts,predict_records(b,[{'question_text':t} for t in texts])):
   expected='clarify' if label=='clarify' else 'refer_out_of_scope' if label=='out_of_scope' else 'retrieve_supported_components' if label=='mixed_partial' else 'retrieve_supported_evidence'
   passed=result['routing_action']==expected and (label=='clarify' or result['predicted_primary']==('mixed' if label=='mixed_partial' else label))
   records.append({'question_text':text,'expected_label':label,'expected_route':expected,'passed':passed,'actual':result})
   if not passed:print(label,'=>',result['predicted_primary'],result['routing_action'],result['reason'],repr(text))
 dest=HERE/(sys.argv[1]+'.json');assert not dest.exists()
 dest.write_text(json.dumps({'provenance':'AI-authored inspected contrast development cases; not final evaluation','passed':sum(r['passed'] for r in records),'total':len(records),'records':records},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(sum(r['passed'] for r in records),'/',len(records))
