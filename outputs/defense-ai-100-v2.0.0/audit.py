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
FIRST_FINDINGS={}

def run(target):
    observations=[json.loads(line) for line in (target/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
    protocol=json.loads((target/'protocol.json').read_text(encoding='utf-8'))
    current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text(encoding='utf-8'))
    index=ROOT/protocol['retrieval']
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
