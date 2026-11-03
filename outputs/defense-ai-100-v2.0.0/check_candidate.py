"""Unpaid source-candidate scope checks; does not alter the active stack."""
import json,sys,joblib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
sys.path.insert(0,str(BASE/'candidate-source'))
from classifier_runtime import predict_records
from clause_classifier import segment_question
cs=json.loads((BASE/'live-cases.json').read_text(encoding='utf-8'))
b=joblib.load(ROOT/'outputs/item10-classifier-v1.5.49/classifier.joblib')
rows=[]
for c,p in zip(cs,predict_records(b,cs)):
    e=c['source_case'];issues=[k for k,v in [('primary',p['predicted_primary']),('scope',p['predicted_scope']),('route',p['routing_action'])] if v!=e['expected_'+k]]
    rows.append({'id':c['case_id'],'issues':issues,'prediction':p})
    if issues:print(c['case_id'],issues,p['routing_action'],p['predicted_primary'],p['predicted_scope'],[(x['text'],x['category'],x['constraint']) for x in p['component_evidence']])
print('Matched',sum(not r['issues'] for r in rows),'of',len(rows))
out=BASE/sys.argv[1]
if out.exists():raise SystemExit('Preserve previous candidate results')
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
import test_concern_repairs
test_concern_repairs.ConcernRepairTests.RUN=ROOT/'outputs/item10-classifier-v1.5.49'
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(test_concern_repairs))
sys.exit(not result.wasSuccessful())
