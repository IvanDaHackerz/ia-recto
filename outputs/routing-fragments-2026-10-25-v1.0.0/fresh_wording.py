"""Second reserved synthetic wording check, frozen before its first inference."""
import hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
DATA=r'''
L|1|Probationary employee ako sa private warehouse. Noong last week lang nila ipinakita yung standards. What should I understand about that?
L|1|A private office put me on probation. They explained the standards only near the end. What does the rule say?
L|1|Private factory staff ako. Minsan isang buwan lang ang sahod. Tama ba yung pagitan ng payday?
C|1|I bought a portable fan from an appliance shop. It ran briefly and then stopped. The seller refuses to discuss a replacement. What consumer rule applies?
C|1|The gadget shop called this laptop brand new, but it was refurbished. What does the consumer framework say about that description?
C|1|Sabi ng retailer brand new yung tablet, pero used pala. What consumer rules should I read?
C|1|May warranty card ako sa bagong oven. The retailer says I should complain to the distributor. What responsibility does the retailer have?
C|1|An online shop delivered the wrong headphones. The delivered model has different features. If I choose replacement, what return rules apply?
L|1|Our private office shut for a regular holiday. The employees were told no work means no pay. What is the general holiday rule?
L|1|Sa private packaging company kami. Hindi binayaran ang overtime ko. What general rule applies?
M|2|My private employer delayed wages. Separately, an appliance store refuses my warranty claim. Please explain the two concerns.
PL|2|My private employer deducted missing equipment from my salary. Separately, my bank charged a loan penalty. Which issue can this project explain?
PC|2|Government employee ako disputing salary. Separately, a local store delivered a broken fan. Explain the purchase concern.
O|1|Seafarer ako. My question is about the employment terms for my overseas vessel assignment.
O|1|Probationary ako sa government office. Saka lang nila sinabi yung standards. What civil-service procedure applies?
O|1|The insurer denied my personal policy claim. Can you tell me the insurance complaint process?
O|1|My landlord kept the rental deposit. Which housing remedy applies?
Q|-|Sa private packaging company ako.
Q|-|They did not meet the requirements. What can I do?
L|1|Sa private hotel ako. Unpaid ang overtime, pero hindi ito government employment. What overtime rule applies?
C|1|I work for a private company. My only concern is a retailer refusing the warranty on a broken kettle I bought.
C|2|A local shop sold me a faulty oven. A different shop kept my cash change. Please explain each purchase issue.
L|2|My private employer dismissed me. A different private employer has not paid wages from my other job. What rules cover each concern?
PC|2|An online store sent a damaged lamp. My neighbor also published my personal information. Please explain the consumer part and where your scope ends.
'''
def prepare():
    mapping={'L':('labor','fully_supported','retrieve_supported_evidence'),'C':('consumer','fully_supported','retrieve_supported_evidence'),
        'M':('mixed','fully_supported','retrieve_supported_components'),'PL':('mixed','partially_supported','retrieve_supported_components'),
        'PC':('mixed','partially_supported','retrieve_supported_components'),'O':('out_of_scope','unsupported','refer_out_of_scope'),'Q':(None,None,'clarify')}
    cases=[]
    for i,line in enumerate(DATA.strip().splitlines(),1):
        g,n,q=line.split('|',2);p,s,r=mapping[g]
        cases.append(dict(case_id=f'FRESH_{i:03}',question_text=q,primary=p,scope=s,route=r,components=int(n) if n!='-' else None))
    assert len(cases)==24
    with (BASE/'fresh-cases.json').open('x',encoding='utf-8') as f:f.write(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
    with (BASE/'fresh-freeze.json').open('x',encoding='utf-8') as f:json.dump({'cases_sha256':hashlib.sha256((BASE/'fresh-cases.json').read_bytes()).hexdigest(),
        'inputs':24,'AI_authored':True,'independent_human_gold':False,'first_inference_not_yet_performed':True,'labels_and_counts_frozen_before_inference':True},f,indent=2)
    print('Frozen 24 further fictional wording checks before inference.')
def run(artifact, output_name='fresh-results.json'):
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
    import joblib
    from classifier_runtime import predict_records
    cases=json.loads((BASE/'fresh-cases.json').read_text());freeze=json.loads((BASE/'fresh-freeze.json').read_text())
    assert hashlib.sha256((BASE/'fresh-cases.json').read_bytes()).hexdigest()==freeze['cases_sha256']
    predictions=predict_records(joblib.load(ROOT/artifact/'classifier.joblib'),[{'question_text':c['question_text']} for c in cases]);rows=[]
    for c,p in zip(cases,predictions):
        a=p['segmentation_audit'];issues=[]
        for f in ['primary','scope']:
            if c[f] is not None and p['predicted_'+f]!=c[f]:issues.append(f)
        if p['routing_action']!=c['route']:issues.append('route')
        if c['components'] is not None and len(a['components'])!=c['components']:issues.append('components')
        if not a['all_fragments_accounted_for']:issues.append('fragment_accounting')
        rows.append({'case':c,'issues':issues,'prediction':p})
    result={'artifact':artifact,'inputs':len(rows),'passed':sum(not r['issues'] for r in rows),'observations':rows,
        'AI_authored':True,'independent_human_questions':0,'llm_calls':0,'cases_sha256':freeze['cases_sha256']}
    with (BASE/output_name).open('x',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['passed'],'/',len(rows),'fresh wording checks passed')
    for r in rows:
        if r['issues']:print(r['case']['case_id'],r['issues'],r['prediction']['segmentation_audit']['components'])
if __name__=='__main__':prepare() if sys.argv[1]=='prepare' else run(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'fresh-results.json')
