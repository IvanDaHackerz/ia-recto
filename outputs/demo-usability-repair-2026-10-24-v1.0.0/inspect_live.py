"""Read complete returned claims in dispatch order without repetitive fallback copy."""
import json
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
lo=int(sys.argv[1]) if len(sys.argv)>1 else 1
hi=int(sys.argv[2]) if len(sys.argv)>2 else 46
path=BASE/'release-pass/observations.jsonl'
rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
for number,row in enumerate(rows,1):
    if not lo<=number<=hi:continue
    case=row['case'];print(f"\nROW {number} {case['case_id']} [{case['group']}/{case['topic']}] {case['question_text']}")
    if 'normalized' not in row:print('APPLICATION ERROR',row.get('error'));continue
    packet=row['normalized']['packet'];assessment=row['normalized']['assessment'];exp=packet['explanation']
    print('RESULT',assessment['predicted_primary'],assessment['predicted_scope'],assessment['route'],
        'ISSUES',assessment['issues'],'AI',exp['status'],exp['reason'],exp.get('validation_failure',''),exp.get('failure_code',''))
    for c in (packet.get('result') or {}).get('components',[]):
        print('COMPONENT',c['component_id'],c['query'],'TOP_SOURCES',[h['provision_id'] for h in c['candidates'][:2]])
    for claim in exp.get('claims',[]):
        print('CLAIM',claim['component_id'],claim['text'],'CITES',list(dict.fromkeys(c['provision_id'] for c in claim['citations'])))
    if exp.get('unanswered_components'):print('UNANSWERED',exp['unanswered_components'])
print(f'\nAvailable {len(rows)}/46; read dispatch rows {lo}–{min(hi,len(rows))}.')
