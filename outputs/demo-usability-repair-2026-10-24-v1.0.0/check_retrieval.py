import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'dataset/pipelines/item10'),str(ROOT/'dataset/pipelines/item11')]
import joblib
from retrieval import LegalRetriever
bundle=joblib.load(ROOT/'outputs/item10-classifier-v1.5.56/classifier.joblib')
retriever=LegalRetriever(ROOT/'outputs/item11-retrieval-v1.3.47')
cases=json.loads((HERE/'live-cases.json').read_text(encoding='utf-8'))
rows=[]
for c in cases:
    result=retriever.retrieve_question(c['question_text'],bundle,'bm25',5)
    rows.append({'case':c,'result':result})
    if c.get('development_replay'):
        print(c['case_id'],result['classification']['routing_action'],[(x['allowed_domain'],[(h['provision_id'],h['heading']) for h in x['hits'][:2]]) for x in result['components']],flush=True)
(HERE/'retrieval-replay.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
