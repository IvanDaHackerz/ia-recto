"""Frozen synthetic routing/fragment checks; no training or provider requests."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent; ROOT=BASE.parents[1]
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
import joblib
from classifier_runtime import predict_records

def save(path,value):
    with path.open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

# Written and frozen before inference. Each row is a fictional development input.
NEW=r'''
L|1|Probationary worker ako sa private warehouse. Ngayon lang nila binigay ang performance standards. Ano yung general rule?
L|1|A private office hired me on probation. Only near the end did they explain the standards. What does the rule require?
C|1|I bought a toaster from a local shop. It worked yesterday and stopped today. The seller refuses to discuss a replacement. What rule covers this?
C|1|Bagong bili yung blender ko sa appliance store. Gumagana nung una, tapos ayaw na. What consumer rules apply?
C|1|The appliance retailer said the tablet was brand new. It turned out to be refurbished. What consumer rule covers that description?
C|1|Sabi ng seller bago yung laptop pero secondhand pala. Ano ang consumer rule dito?
L|1|Sa private packaging company kami. Delayed yung sweldo. Kailan ba dapat ang payday?
L|1|Sa private grocery ako nagtatrabaho. Kulang yung overtime pay ko. What general rule applies?
L|1|My private employer pays wages once a month. Is that the usual permitted payment interval?
C|1|May warranty card yung bagong washing machine ko. The retailer says I should complain directly to the distributor. What does the warranty rule say?
C|1|An online shop delivered the wrong lamp model. The delivered unit has different features. What consumer rules should I inspect?
L|1|Probationary ako sa private company. Saka lang nila sinabi ang standards nung patapos na ang probation. How does the rule handle that?
O|1|Probationary ako sa government office. Saka lang nila sinabi ang standards. What civil-service procedure applies?
O|1|I am an OFW working in Qatar. My probation standards were communicated late. Which overseas process applies?
O|1|A phone network billed me for a refurbished-device subscription plan. My dispute is about the monthly telecom charges.
O|1|I want the police to investigate a fake online seller who disappeared with my money. What criminal case should I file?
PL|2|Sa private printing company kami. Unpaid ang overtime. Separately, my bank deducted an account fee. Explain only the covered part.
PC|2|An online shop sent me a damaged fan. My neighbor also posted my private address. Please explain the consumer part and where your scope ends.
M|2|My private employer delayed wages. Separately, a local store refuses my warranty claim. Can you explain both concerns?
L|2|My private employer has not paid overtime. Separately, another private employer dismissed me from my weekend job. What rules cover each concern?
C|2|One shop sold me a faulty kettle. A different shop kept my cash change. Please explain each purchase issue.
PC|2|Government employee ako with a salary dispute. Separately, a shop sold me a broken microwave. Explain the purchase issue.
PL|2|My private employer dismissed me. Separately, I want help with an inheritance dispute. Which part is covered?
C|1|I work for a private company. My only concern is a retail seller refusing my blender warranty.
O|1|Sa private insurance company kami. My question is about my personal insurance claim being denied, not employment.
Q|-|Sa private printing company kami.
Q|-|Probationary ako sa private office.
Q|-|They did not follow the standards. What can I do?
L|1|Sa private hotel ako. Hindi binayaran ang overtime, pero hindi ito government employment. What overtime rule applies?
PC|2|My bank froze my account. A store also sold me a used phone as new. Please explain the purchase concern.
C|1|I bought a desk fan from a shop. It worked once and then stopped. I am asking about the product, not my job.
L|1|Private employee ako. Hindi binayaran overtime. Saka may deduction pa sa same payslip for damaged equipment. What conditions should be checked?
'''

def prepare():
    old=json.loads((ROOT/'outputs/explanation-usability-2026-10-25-v1.0.0/live-cases.json').read_text())
    counts={'EX_NEW_003':1,'EX_NEW_005':1,'EX_NEW_008':1,'EX_NEW_011':1,'EX_NEW_012':1,'EX_NEW_016':1,'EX_NEW_017':1,'EX_NEW_019':1,'EX_NEW_024':2}
    cases=[]
    for row in old:
        e=row['source_case'];cases.append({'case_id':row['case_id'],'phase':'diagnostic_replay','question_text':row['question_text'],
            'primary':e['expected_primary'],'scope':e['expected_scope'],'route':e['expected_route'],'components':counts.get(row['case_id']),
            'independent_human_gold':False})
    mapping={'L':('labor','fully_supported','retrieve_supported_evidence'),'C':('consumer','fully_supported','retrieve_supported_evidence'),
        'M':('mixed','fully_supported','retrieve_supported_components'),'PL':('mixed','partially_supported','retrieve_supported_components'),
        'PC':('mixed','partially_supported','retrieve_supported_components'),'O':('out_of_scope','unsupported','refer_out_of_scope'),
        'Q':(None,None,'clarify')}
    for i,line in enumerate(NEW.strip().splitlines(),1):
        g,n,q=line.split('|',2);p,s,r=mapping[g]
        cases.append(dict(case_id=f'NEW_{i:03}',phase='reserved_wording',question_text=q,primary=p,scope=s,route=r,
            components=int(n) if n!='-' else None,independent_human_gold=False))
    assert len(cases)==72
    save(BASE/'cases.json',cases)
    for p in (ROOT/'dataset/pipelines/item10').glob('*.py'):
        dest=BASE/'before_source'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
    shutil.copyfile(ROOT/'CURRENT_ARTIFACTS.json',BASE/'before-current.json')
    save(BASE/'freeze.json',{'cases_sha256':hashlib.sha256((BASE/'cases.json').read_bytes()).hexdigest(),
        'diagnostic_replays':40,'reserved_wording':32,'AI_authored':True,'independent_human_gold':False,
        'expected_labels_and_component_counts_frozen_before_inference':True,'scope':'Routing and segmentation only; no legal accuracy or provider calls.'})
    print('Frozen 40 inspected diagnostic replays and 32 reserved synthetic wording checks.')

def run(name,artifact,include_reserved):
    cases=json.loads((BASE/'cases.json').read_text());freeze=json.loads((BASE/'freeze.json').read_text())
    assert hashlib.sha256((BASE/'cases.json').read_bytes()).hexdigest()==freeze['cases_sha256']
    selected=cases if include_reserved else [c for c in cases if c['phase']=='diagnostic_replay']
    adjudication=json.loads((BASE/'pre-inference-adjudication.json').read_text()) if (BASE/'pre-inference-adjudication.json').exists() else None
    for c in selected:
        if adjudication and c['case_id']==adjudication['case_id']:
            c['original_expected_components']=c['components'];c['components']=adjudication['expected_components']
    b=joblib.load(ROOT/artifact/'classifier.joblib');predictions=predict_records(b,[{'question_text':c['question_text']} for c in selected])
    result=[]
    for c,p in zip(selected,predictions):
        issues=[]
        for f in ['primary','scope']:
            if c[f] is not None and p['predicted_'+f]!=c[f]:issues.append(f)
        if p['routing_action']!=c['route']:issues.append('route')
        a=p['segmentation_audit']
        if c['components'] is not None and len(a['components'])!=c['components']:issues.append('components')
        if not a['all_fragments_accounted_for']:issues.append('fragment_accounting')
        result.append({'case':c,'issues':issues,'prediction':p})
    save(BASE/(name+'.json'),{'artifact':str(artifact),'case_hash':freeze['cases_sha256'],'inputs':len(result),
        'runtime_source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'dataset/pipelines/item10').glob('*.py')},
        'passed':sum(not x['issues'] for x in result),'failures':[{'case_id':x['case']['case_id'],'issues':x['issues']} for x in result if x['issues']],
        'observations':result,'pre_reserved_inference_adjudication':adjudication,'independent_human_questions':0,'llm_calls':0})
    print(name, len(result),'inputs;',sum(not x['issues'] for x in result),'passed')
    for x in result:
        if x['issues']:print(x['case']['case_id'],','.join(x['issues']),x['prediction']['routing_action'],x['prediction']['segmentation_audit']['components'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('--artifact',type=Path);p.add_argument('--reserved',action='store_true');a=p.parse_args()
    prepare() if a.action=='prepare' else run(a.action,a.artifact,a.reserved)
