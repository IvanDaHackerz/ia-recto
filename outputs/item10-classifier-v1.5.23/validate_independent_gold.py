"""Validate human-supplied gold intake; never manufacture authorship or approval."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def normalized(text):return ' '.join(re.findall(r'\w+',text.casefold()))

def validate(rows,known_texts=()):
    errors=[];seen=set();known={normalized(t) for t in known_texts}
    primary={'labor','consumer','mixed','out_of_scope'}
    scope={'fully_supported','partially_supported','unsupported'}
    valid_pairs={('labor','fully_supported'),('consumer','fully_supported'),
        ('mixed','fully_supported'),('mixed','partially_supported'),('out_of_scope','unsupported')}
    families={}
    for i,r in enumerate(rows,1):
        prefix=r.get('question_id') or str(i);text=r.get('question_text') or ''
        def fail(message):errors.append({'question_id':prefix,'issue':message})
        if not text.strip():fail('Question has not been supplied')
        if r.get('origin')!='independent_human_written':fail('Independent human authorship is not attested')
        if r.get('ai_assisted_writing') is not False:fail('AI writing must not be labeled independent human writing')
        if not r.get('author_id') or not r.get('annotator_id'):fail('Author and annotator IDs are required')
        if not r.get('written_at') or not r.get('annotated_at'):fail('Actual writing and annotation dates are required')
        if r.get('derived_from_question_id'):fail('An existing development example cannot become a fresh holdout')
        if r.get('used_for_tuning') is not False:fail('Previously used tuning data cannot become a fresh holdout')
        if not r.get('scenario_family_id'):fail('Scenario family is required')
        if r.get('language_style') not in {'en','en_tl'}:fail('Unsupported/missing evaluated language')
        pair=(r.get('primary_label'),r.get('scope_label'))
        if pair not in valid_pairs:fail('Missing or inconsistent human labels')
        fact=normalized(text)
        if fact and fact in known:fail('Exact normalized overlap with an existing project question')
        if fact and fact in seen:fail('Duplicate question in intake')
        seen.add(fact)
        if r.get('question_id') in families:fail('Duplicate question ID')
        families[r.get('question_id')]=r.get('scenario_family_id')
    if len(rows)<100:errors.append({'issue':'At least 100 completed independent questions are required'})
    if set(r.get('primary_label') for r in rows)!=primary:errors.append({'issue':'All four primary classes must be represented'})
    if set(r.get('scope_label') for r in rows)!=scope:errors.append({'issue':'All three scope classes must be represented'})
    return {'passed':not errors,'rows':len(rows),'errors':errors,
        'human_provenance_is_self_attestation_not_machine_proof':True,
        'near_duplicate_and_label_quality_review_still_required':True,
        'locks_or_opens_test':False,'deployment_allowed':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    rows=[json.loads(l) for l in a.input.read_text(encoding='utf-8').splitlines() if l.strip()]
    known=[]
    for folder in ['dataset/processed/item9','dataset/processed/item10']:
        for file in (ROOT/folder).rglob('*.jsonl'):
            if file.resolve()==a.input.resolve():continue
            for line in file.read_text(encoding='utf-8').splitlines():
                r=json.loads(line)
                if r.get('question_text'):known.append(r['question_text'])
    result=validate(rows,known);result['input_sha256']=hashlib.sha256(a.input.read_bytes()).hexdigest()
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'rows':len(rows),'errors':len(result['errors'])}))
    raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
