"""Run the same fresh questions with providers disabled; keep all observations."""
from pathlib import Path
import json,sys,time
from unittest.mock import patch
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];sys.path.insert(0,str(ROOT))
from backend.application.service import ApplicationService
from backend.normalization import ConditionalNormalizer
from backend.normalization_metrics import assess,summarize_path

def main():
 out=BASE/(sys.argv[1] if len(sys.argv)>1 else 'local-baseline');out.mkdir(exist_ok=False)
 cases=json.loads((BASE/'first-pass/cases.json').read_text(encoding='utf-8'))
 service=ApplicationService(normalizer=ConditionalNormalizer())
 rows=[]
 with patch('urllib.request.OpenerDirector.open',side_effect=RuntimeError('Network forbidden in local baseline')):
  with (out/'observations.jsonl').open('x',encoding='utf-8') as f:
   for c in cases:
    start=time.monotonic()
    p=service.chat({'question_text':c['question_text'],'use_ai':False,'save_history':False})
    r={'case':c,'baseline':{'packet':p,'assessment':assess(c,p)},'elapsed_ms':(time.monotonic()-start)*1000}
    rows.append(r);f.write(json.dumps(r,ensure_ascii=False)+'\n');f.flush()
 summary=summarize_path(rows,'baseline')
 (out/'metrics.json').write_text(json.dumps(summary,indent=2)+'\n')
 (out/'errors.json').write_text(json.dumps([r for r in rows if r['baseline']['assessment']['issues']],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'inputs':len(rows),'primary':summary['primary']['accuracy'],'scope':summary['scope']['accuracy'],'routes':summary['route_match'],'issues':summary['issue_counts']},indent=2))
if __name__=='__main__':main()
