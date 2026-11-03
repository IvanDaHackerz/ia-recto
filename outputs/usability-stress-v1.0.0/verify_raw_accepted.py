"""Recheck raw classifier expectations on the final package, with zero AI calls."""
import json,sys,joblib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
from classifier_runtime import predict_records
b=joblib.load(ROOT/'outputs/item10-classifier-v1.5.36/classifier.joblib')
for name,out in [('all_cases.json','raw-packaged-v36.json'),('variant_cases.json','variants-packaged-v36.json')]:
 cases=json.loads((H/name).read_text(encoding='utf-8'));pred=predict_records(b,[{'question_text':c['q']} for c in cases]);fail=[]
 for c,p in zip(cases,pred):
  flow='clarify' if p['routing_action']=='clarify' else 'referral' if p['routing_action']=='refer_out_of_scope' else 'local_sources'
  if any(p['predicted_'+k]!=c[k] for k in ['primary','scope'] if k in c) or flow!=c['flow']:
   fail.append({'id':c['id'],'q':c['q'],'primary':p['predicted_primary'],'scope':p['predicted_scope'],'flow':flow,'reason':p['reason']})
 result={'count':len(cases),'classifier':b['model_version'],'failures':fail}
 (H/out).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
 if fail:raise SystemExit(1)
