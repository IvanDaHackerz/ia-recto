"""Second unused-wording check, frozen before predictions; synthetic only."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
GROUPS={
'labor':[
 'Our employer skipped this payroll entirely. What general wage payment rules can we read?',
 'My private office requires staff to remain available through their lunch break. Does that count toward work time?',
 'Do employees normally get a weekly rest period when the business is open every day?',
 'Our company requires overtime on ordinary workdays. What additional pay rules should we inspect?',
 'What are the general rules for a private employee who works on a regular holiday?',
 'After leaving my job midyear, I want to understand proportionate thirteenth month pay.',
 'HR calls our contracts probationary. What does this employment status generally mean?',
 'My company sent a dismissal notice without letting me respond to allegations. What procedure applies?',
],
'consumer':[
 'A newly purchased toaster from a shop is faulty. What protections might apply?',
 'The shop promised to cover a repair under warranty and now refuses to honor it.',
 'The appliance merchant has tried repairs repeatedly. What rules cover a request for a replacement?',
 'A retailer sold an old laptop as brand new. What counts as a deceptive sale?',
 'A seller advertised a feature that its rice cooker does not actually have.',
 'The cashier gave me candy rather than the remaining change from my purchase.',
 'A household product from a retailer has exposed sharp metal edges. What general product safety protections apply?',
 'An online merchant sent a different model and is refusing to accept a return.',
],
'out_of_scope':[
 'I am employed by a municipal office and want to dispute a salary deduction.',
 'My overseas employment agency changed the job I was promised.',
 'My bank froze a transfer and charged me a transaction fee.',
 'The insurer says damage is excluded from my insurance policy.',
 'A telecommunications company disconnected our service but kept billing us.',
 'My electricity utility disputes the reading on our bill.',
],
'clarify':[
 'I want my money back but do not know what to do.',
 'Can you help with this contract?',
 'Someone charged extra. What now?',
 'qzxw zzpp pqqr',
],
'outside_safe':[
 'Please help me bake bread for my family.',
 'We are separating and need advice on custody of our children.',
 'What JavaScript code would reverse an array?',
 'How do inheritance and probate work after a parent dies?',
],
}
def freeze():
 dest=HERE/'second_reserve.jsonl';assert not dest.exists()
 rows=[{'case_id':f'second.{label}.{i}','expected_primary':label if label not in {'clarify','outside_safe'} else None,
  'expected_routes':['clarify','refer_out_of_scope'] if label=='outside_safe' else ['clarify' if label=='clarify' else 'refer_out_of_scope' if label=='out_of_scope' else 'retrieve_supported_evidence'],
  'question_text':q} for label,questions in GROUPS.items() for i,q in enumerate(questions)]
 dest.write_text(''.join(json.dumps(r)+'\n' for r in rows))
 (HERE/'second_reserve_frozen.json').write_text(json.dumps({'count':len(rows),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
  'provenance':'AI-authored unused-wording synthetic check, authored after first reserve exposed failures; not independent human gold.'},indent=2)+'\n')
 print(len(rows))
def run():
 sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
 import joblib
 from classifier_runtime import predict_records
 frozen=json.loads((HERE/'second_reserve_frozen.json').read_text());path=HERE/'second_reserve.jsonl'
 assert hashlib.sha256(path.read_bytes()).hexdigest()==frozen['sha256']
 current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text());bundle=joblib.load(ROOT/current['classifier']/'classifier.joblib')
 frozen_code=json.loads((HERE/'implementation_final_frozen.json').read_text())
 assert current['classifier']==frozen_code['classifier']
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in frozen_code['runtime_files_sha256'].items())
 rows=[json.loads(l) for l in path.read_text().splitlines()];records=[]
 for row,prediction in zip(rows,predict_records(bundle,rows)):
  passed=prediction['routing_action'] in row['expected_routes'] and (row['expected_primary'] is None or row['expected_primary']==prediction['predicted_primary'])
  records.append({'case':row,'passed':passed,'actual':prediction})
  if not passed:print(row['case_id'],prediction['predicted_primary'],prediction['routing_action'],prediction['reason'])
 result={'classifier':current['classifier'],'passed':sum(r['passed'] for r in records),'total':len(records),'network_calls':0,'records':records}
 dest=HERE/'second-reserve-results.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n')
 print(result['passed'],'/',result['total'])
if __name__=='__main__':freeze() if sys.argv[1]=='freeze' else run()
