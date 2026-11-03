"""Isolated context-preface experiment; never modifies the active AI-run code."""
import importlib.util,sys,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
spec=importlib.util.spec_from_file_location('clause_classifier',BASE/'proposed-context/clause_classifier.py')
mod=importlib.util.module_from_spec(spec);sys.modules['clause_classifier']=mod;spec.loader.exec_module(mod)
import joblib
from classifier_runtime import predict_records
b=joblib.load(ROOT/'outputs/item10-classifier-v1.5.70/classifier.joblib')
for name,cases in [('fresh',json.loads((BASE/'first-pass/cases.json').read_text(encoding='utf-8'))),('historical',[json.loads(x) for x in (ROOT/'outputs/local-pipeline-cases-v1.1.0/cases.jsonl').read_text(encoding='utf-8').splitlines()])]:
 rows=[]
 for c,p in zip(cases,predict_records(b,[{'question_text':c['question_text']} for c in cases])):
  e=c['source_case'];problems=[k for k,a,v in [('primary',p['predicted_primary'],e['expected_primary']),('scope',p['predicted_scope'],e['expected_scope']),('route',p['routing_action'],e['expected_route'])] if v is not None and a!=v]
  rows.append({'id':c['case_id'],'issues':problems,'components':mod.segment_question(c['question_text'])['components']})
 (BASE/f'context-probe-{name}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(name,len(rows),sum(not r['issues'] for r in rows),flush=True)
 for r in rows:
  if r['issues'] or name=='fresh' and r['id'] in ['RD31_002','RD31_005','RD31_009','RD31_013','RD31_015']:print(r,flush=True)
