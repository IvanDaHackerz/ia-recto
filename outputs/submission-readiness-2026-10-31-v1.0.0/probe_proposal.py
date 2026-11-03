"""Pure proposed-component diagnostics; not a signed runtime/evaluation package."""
import importlib.util,sys,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
for name in ['scope_constraints','classifier_runtime','clause_classifier']:
 spec=importlib.util.spec_from_file_location(name,BASE/'proposed-runtime/item10'/f'{name}.py')
 mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
import joblib
from classifier_runtime import predict_records
from clause_classifier import segment_question

def probe(cases):
 b=joblib.load(ROOT/'outputs/item10-classifier-v1.5.67/classifier.joblib')
 predictions=predict_records(b,[{'question_text':c['question_text']} for c in cases])
 report=[]
 for c,p in zip(cases,predictions):
  e=c['source_case'];domains=sorted({x['category'] for x in p.get('component_evidence',[]) if x['category'] in {'labor','consumer'}}) if p['routing_action'].startswith('retrieve_') else []
  problems=[k for k,a,b in [('primary',p['predicted_primary'],e['expected_primary']),('scope',p['predicted_scope'],e['expected_scope']),('route',p['routing_action'],e['expected_route']),('domains',domains,sorted(e['expected_domains']))] if a!=b and b is not None]
  report.append({'case_id':c['case_id'],'question_text':c['question_text'],'issues':problems,'prediction':p,'expected':e})
 return report

fresh=json.loads((BASE/'first-pass/cases.json').read_text(encoding='utf-8'))
old=[json.loads(l) for l in (ROOT/'outputs/local-pipeline-cases-v1.1.0/cases.jsonl').read_text(encoding='utf-8').splitlines()]
for name,cases in [('fresh',fresh),('historical',old)]:
 rows=probe(cases);(BASE/f'proposed-{name}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(name,{'inputs':len(rows),'all_expected':sum(not r['issues'] for r in rows)},flush=True)
 for r in rows:
  if r['issues']:print(r['case_id'],r['issues'],r['prediction']['reason'],r['prediction']['predicted_primary'],r['prediction']['predicted_scope'],flush=True)
