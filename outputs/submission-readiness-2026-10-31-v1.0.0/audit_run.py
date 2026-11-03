"""Read-only, denominator-inclusive audit of a preserved synthetic AI run."""
from collections import Counter
import json,sys
from pathlib import Path
from sklearn.metrics import f1_score
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def audit(name):
    run=BASE/name
    cases=json.loads((run/'cases.json').read_text(encoding='utf-8'))
    rows=[json.loads(x) for x in (run/'observations.jsonl').read_text(encoding='utf-8').splitlines()]
    protocol=json.loads((run/'protocol.json').read_text(encoding='utf-8'))
    recorded={x['chunk_id']:x for x in map(json.loads,(ROOT/protocol['retrieval']/'records.jsonl').read_text(encoding='utf-8').splitlines())}
    by_id={r['case']['case_id']:r for r in rows}
    failures=[];counts=Counter();expected={k:[] for k in ['primary','scope']};predicted={k:[] for k in expected}
    answer_lines=['# Recorded answers — '+name,'','AI-authored fictional development questions. Post-repair results reuse the opened questions. These outputs are not professional legal approval.','']
    if name in {'repaired','final-targeted','final-confirmation'}:answer_lines += ['Historical intermediate runtime. Later engineering review added source-condition checks and an interpretation hold. See the guard revalidation and REPORT.md; do not treat this file as a set of approved final answers.','']
    for c in cases:
        rid=c['case_id'];r=by_id.get(rid,{})
        answer_lines += ['## '+rid,'',c['question_text'],'']
        for k in expected:expected[k].append(c['source_case']['expected_'+k])
        if 'normalized' not in r:
            counts['pending' if not r else 'request_errors']+=1
            for k in predicted:predicted[k].append('__error__')
            answer_lines += ['Recorded failure: '+r.get('error','pending'),''];continue
        counts['packets']+=1
        a=r['normalized']['assessment'];p=r['normalized']['packet'];e=p['explanation']
        for k in expected:
            predicted[k].append(a['predicted_'+k]);counts[k+'_correct']+=bool(a[k+'_correct'])
        counts['route_correct']+=bool(a['route_correct']);counts['domain_correct']+=bool(a['domain_correct'])
        counts['status_'+e['status']]+=1
        counts['reason_'+e['reason']]+=1
        if a['retrieval']:
            counts['judged_cases']+=1;counts['all_known_relevant_hit_at_5']+=all(x['hit_at_5'] for x in a['retrieval'])
        if c['source_case']['expected_primary']=='out_of_scope':
            counts['outside_cases']+=1;counts['outside_candidates']+=a['candidate_count'];counts['outside_claims']+=len(e['claims'])
        per_component={comp['component_id']:{h['chunk_id']:h for h in comp['candidates']} for comp in (p.get('result') or {}).get('components',[])}
        counts['claims']+=len(e['claims'])
        for claim in e['claims']:
            if not e.get('automated_support_checked'):failures.append([rid,'unchecked_claim'])
            if not claim['citations']:failures.append([rid,'uncited_claim'])
            for cite in claim['citations']:
                counts['citations']+=1;s=per_component.get(claim['component_id'],{}).get(cite['chunk_id'])
                if not s:failures.append([rid,'citation_not_retrieved']);continue
                if s['parent_text']!=recorded[cite['chunk_id']]['parent_text']:failures.append([rid,'retrieved_text_does_not_match_pinned_record'])
                if s['parent_text'][cite['start']:cite['end']]!=cite['quote']:failures.append([rid,'quote_offset_mismatch'])
                if any(cite[k]!=s[k] for k in ['document_id','provision_id']):failures.append([rid,'source_identity_mismatch'])
            answer_lines += [claim['text'],'','Citations: '+', '.join(x['citation_label'] for x in claim['citations']),'']
        answer_lines += [f"Recorded outcome: {a['predicted_primary']} / {a['predicted_scope']} / {a['route']}; explanation {e['status']} ({e['reason']}).",'']
    result={'run':name,'denominator':len(cases),'observed_rows':len(rows),'counts':dict(counts),
        'inclusive_scores':{k:{'correct':counts[k+'_correct'],'denominator':len(cases),'fraction':counts[k+'_correct']/len(cases)} for k in ['primary','scope','route','domain']},
        'inclusive_macro_f1':{k:float(f1_score(expected[k],predicted[k],labels=sorted(set(expected[k])),average='macro',zero_division=0)) for k in expected},
        'citation_integrity_failures':failures,'independent_human_questions':0,'legal_answer_accuracy_measured':False,
        'denominator_note':'Missing packets count as errors in every inclusive score. F1 uses the fixed expected classes, with request errors treated as missed labels.'}
    save(BASE/(name+'-audit.json'),result)
    (BASE/(name+'-ANSWERS.md')).write_text('\n'.join(answer_lines),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':audit(sys.argv[1])
