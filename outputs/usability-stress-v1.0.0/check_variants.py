"""Metamorphic robustness checks, paired with their base development questions."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
cases=[]
for name in ['development_cases.json','reserved_cases.json']:
 for c in json.loads((H/name).read_text(encoding='utf-8')):
  variants={'uppercase':c['q'].upper(),'spacing':re.sub(' ', '   ',c['q']),
    'light_typing':re.sub(r'\b(employer|salary|company|shop|warranty|government|contract|private)\b',lambda m:{'employer':'employr','salary':'salry','company':'cmpny','shop':'shp','warranty':'wrrnty','government':'governmnt','contract':'cntrct','private':'prvate'}[m.group().lower()],c['q'],flags=re.I)}
  for kind,q in variants.items():cases.append({**c,'id':c['id']+'_'+kind,'base_id':c['id'],'variation':kind,'q':q})
target=H/'variant_cases.json'
if target.exists():
 if json.loads(target.read_text(encoding='utf-8'))!=cases:raise ValueError('Frozen variants changed')
else:target.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Frozen paired variants:',len(cases),hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
raise SystemExit(subprocess.call([sys.executable,str(H/'evaluate.py'),'--raw','--cases','variant_cases.json','--out','variants-first-pass.json']))
