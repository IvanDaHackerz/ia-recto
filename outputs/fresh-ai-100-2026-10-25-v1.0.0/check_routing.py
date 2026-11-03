"""Replay frozen development inputs; this is not independent validation."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
import joblib
from classifier_runtime import predict_records

def main():
    bundle=joblib.load(ROOT/(sys.argv[1] if len(sys.argv)>1 else 'outputs/item10-classifier-v1.5.52/classifier.joblib'))
    cases=json.loads((HERE/'live-cases.json').read_text(encoding='utf-8'))
    predictions=predict_records(bundle,cases)
    rows=[]
    for c,p in zip(cases,predictions):
        expected=c['source_case'];issues=[k for k,actual in [('primary',p['predicted_primary']),('scope',p['predicted_scope']),('route',p['routing_action'])] if expected['expected_'+k]!=actual]
        rows.append({'id':c['case_id'],'question':c['question_text'],'issues':issues,'prediction':p})
        if issues:print(c['case_id'],issues,p['predicted_primary'],p['predicted_scope'],p['routing_action'],json.dumps(p.get('segmentation_audit',{}).get('components',[]),ensure_ascii=False))
    (HERE/'routing-replay.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('TOTAL',len(rows),'label errors',sum(bool(set(r['issues'])&{'primary','scope'}) for r in rows),'route errors',sum('route' in r['issues'] for r in rows))

if __name__=='__main__':main()
