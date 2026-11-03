"""Source-integrity audit and disclosed AI reading notes; no legal certification."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.application.source_issues import issue_for
BASE=Path(__file__).resolve().parent
FIRST_FINDINGS={
6:'Normal-hours ceiling does not answer counted briefing time; second paragraph repeats the gap.',
13:'Repeated rest-day material and unrequested religious scheduling detail.',
16:'Payroll-record content is incidental to the overtime question.',
24:'Contains a recorded historical holiday-list consequence; current applicability is unreviewed.',
31:'Reads an employment-status rule into the described contract without enough qualification.',
32:'Personal regular-status conclusion and an unrequested probation discussion.',
34:'Reverses the project exception and regular-versus-casual distinction.',
36:'A rest-day schedule passage does not explain permanent removal from employment.',
39:'The poor-sales discussion and cause/process distinctions need narrower source support.',
46:'The final-settlement sentence omits the payment-by-results limitation in that paragraph.',
53:'Mixes safety-defect and quality-imperfection regimes; conditions require closer checking.',
54:'Changes the responsible actor from manufacturer/producer/importer to seller.',
56:'Omits material conditions from the product-imperfection remedy summary.',
57:'Adds an individualized finding about the discounted sale beyond the conditional warranty framework.',
61:'Describes the agreed correction interval as necessarily longer, which the source does not establish.',
62:'Adds fault-based price-difference allocation not established by its cited replacement text.',
63:'Describes a choice as only two remedies while the source lists a third option and qualifications.',
65:'Turns allegations into a definite deceptive-sale characterization.',
67:'Treats the particular hidden fee as a legal finding; repeats nearby policy.',
68:'Declares the disputed approval representation deceptive without adjudicative qualification.',
69:'Makes a likely case outcome finding about the particular advertisement.',
70:'Applies a lumber-tag requirement to a finished table and declares a violation.',
71:'Treats the alleged missing advertised feature as an established false-ad finding.',
72:'Absence of packaging proof does not itself establish false certification.',
73:'Duplicated price-tag paragraphs; awkward exception attachment.',
76:'Duplicated shortchanging paragraphs rather than one focused answer.',
77:'Classifies the particular cord as legally defective instead of describing the conditional test.',
81:'Introduces a hypothetical seller promise unrelated to the asserted laundry-quality issue.',
82:'Conflates monetary updating with compensation for losses.',
83:'Repeats the service rule and blends safety/quality descriptions.',
85:'Reverses the consumer-fault reimbursement direction.',
87:'Needs closer preservation of return and reimbursement qualifications.',
89:'Adds a logging step and receipt-specific procedure not established by the cited general source.',
93:'Adds a definite procedural/legal characterization of the particular dismissal.',
96:'Overgeneralizes loss/damage deductions to all wage deductions and omits prerequisites.',
97:'Conflates a basic holiday-pay exception with worked-holiday premium treatment.',
100:'Changes manufacturer/producer/importer defenses into seller defenses.',
}

def run(target):
    observations=[json.loads(line) for line in (target/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
    protocol=json.loads((target/'protocol.json').read_text(encoding='utf-8'))
    current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text(encoding='utf-8'))
    index=ROOT/current['retrieval']
    records={r['chunk_id']:r for r in [json.loads(x) for x in (index/'records.jsonl').read_text(encoding='utf-8').splitlines()]}
    checks=[];notes=[]
    for o in observations:
        case=o['case'];packet=o.get('normalized',{}).get('packet')
        if not packet:
            notes.append({'case_id':case['case_id'],'error':o.get('error'),'AI_reading':'No returned packet'})
            continue
        components={c['component_id']:c for c in (packet.get('result') or {}).get('components',[])}
        explanation=packet['explanation']
        for claim in explanation.get('claims',[]):
            component=components.get(claim['component_id'])
            for cite in claim['citations']:
                record=records.get(cite['chunk_id'])
                exact=bool(record and record['parent_text'][cite['start']:cite['end']]==cite['quote'])
                correct_ids=bool(record and all(cite[k]==record[k] for k in ['provision_id','document_id']))
                eligible=bool(record and not issue_for(record) and component and component['allowed_domain'] in record['domains'])
                checks.append({'case_id':case['case_id'],'claim_id':claim['claim_id'],'chunk_id':cite['chunk_id'],
                    'exact_span':exact,'source_identity':correct_ids,'domain_and_hold_check':eligible})
        number=int(case['case_id'][-3:])
        notes.append({'case_id':case['case_id'],'AI_status':explanation['status'],'reason':explanation['reason'],
            'classification_issues':o['normalized']['assessment']['issues'],
            'AI_reading_finding':FIRST_FINDINGS.get(number) if target.name=='first-pass' and explanation['status']=='generated' else None,
            'reading_is_independent_human_or_legal_review':False})
    report={'cases':len(observations),'citations_checked':len(checks),
        'exact_spans_passed':sum(r['exact_span'] for r in checks),
        'identities_passed':sum(r['source_identity'] for r in checks),
        'domain_and_hold_checks_passed':sum(r['domain_and_hold_check'] for r in checks),
        'checks':checks,'AI_reading_notes':notes,
        'meaning':'Exact-source integrity and AI engineering review are separate from semantic correctness and current-law/legal review.',
        'independent_human_reviews':0,'legal_accuracy':None}
    (target/'source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['cases','citations_checked','exact_spans_passed','identities_passed','domain_and_hold_checks_passed']}))

if __name__=='__main__':run(Path(sys.argv[1]))
