"""Reproduce owner-authorized Item 10 cleanup without changing returned reviews or Item 9."""
from __future__ import annotations
import csv, hashlib, json, re, zipfile, posixpath
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
VERSION = '1.0.0'
DATE = '2026-10-17'
ACTOR = 'Codex (project-owner-authorized cleanup)'
OUTPUT = ROOT / 'dataset/processed/item10' / ('reviewed_v' + VERSION)
PAYLOAD = ROOT / 'tmp/item10_workbook_build/cleanup_payload.json'
NS = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
ARRAYS = ['supported_topic_ids','excluded_topic_ids','referral_ids']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in rows:
            w.writerow({k:'|'.join(row[k]) if isinstance(row[k],list) else json.dumps(row[k],ensure_ascii=False,sort_keys=True) if isinstance(row[k],dict) else row[k] for k in fields})
def write_json(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def read_xlsx(path):
    result={}
    with zipfile.ZipFile(path) as z:
        ss=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            ss=[''.join(t.text or '' for t in x.findall('.//m:t',NS)) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
        rel={e.attrib['Id']:e.attrib['Target'] for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for s in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS):
            t=rel[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            t=t.lstrip('/') if t.startswith('/') else posixpath.normpath('xl/'+t)
            cells={}
            for c in ET.fromstring(z.read(t)).findall('.//m:sheetData/m:row/m:c',NS):
                value=c.find('m:v',NS);v=value.text or '' if value is not None else ''
                if c.attrib.get('t')=='s':v=ss[int(v)]
                elif c.attrib.get('t')=='inlineStr':v=''.join(e.text or '' for e in c.findall('.//m:t',NS))
                cells[c.attrib['r']]=v
            result[s.attrib['name']]=cells
    return result
def normalize(text): return re.sub(r'\s+',' ',str(text)).strip()
def effective_group(group):
    p=group.split(':')
    return ':'.join(p[:2]+p[-1:]) if p[0] in ['single','outside'] else group

def main():
    existing_manifest=OUTPUT/'dataset_manifest.json'
    if existing_manifest.exists() and json.loads(existing_manifest.read_text(encoding='utf-8')).get('status')=='frozen_reviewed_seed':
        raise ValueError('This reviewed version is frozen. Create a new version for further changes; do not overwrite the snapshot.')
    plan=json.loads((HERE/'review_cleanup_decisions.json').read_text(encoding='utf-8'))
    seed_path=ROOT/'dataset/processed/item9/classifier_questions.csv'
    if sha(seed_path)!=plan['seed_sha256']:raise ValueError('Item 9 changed after audit; re-audit before cleanup.')
    for relative,expected in plan['support_sources_sha256'].items():
        if sha(ROOT/relative)!=expected:raise ValueError(f'Cleanup reference changed: {relative}; re-audit before rebuilding.')
    seed={r['question_id']:r for r in read_csv(seed_path)}
    refs=read_csv(ROOT/'dataset/processed/item9/referral_directory.csv')
    for r in refs:
        if r['referral_id']=='REF_DMW':
            r['topic_ids']='labor.ofw|labor.seafarers'
            r['when_to_use']='Overseas employment, recruitment, welfare, or repatriation concerns, including overseas seafarer deployment. Use qualified legal assistance for a disputed contract or money claim.'
        if r['referral_id']=='REF_PAO':
            r['topic_ids']+='|labor.seafarers'
            r['when_to_use']+=' Includes seafarer employment/pay disputes; eligibility and the appropriate forum require assessment.'
        r['routing_review_as_of']=DATE
        r['contact_reverification_status']='carried_forward_from_item9_not_rechecked'
    all_rows=[];changes=[];workbooks=[];seen=set()
    for src in plan['workbooks']:
        path=ROOT/'outputs/item10-review-workbooks'/src['file']
        if sha(path)!=src['sha256']:raise ValueError(f'Returned workbook changed: {path.name}')
        wb=read_xlsx(path);q=wb['Review Queue'];reviewer=wb['Instructions']['B3']
        batch=[]
        for addr,qid in q.items():
            if not re.fullmatch(r'B\d+',addr) or int(addr[1:])<6:continue
            if qid not in seed or qid in seen:raise ValueError(f'Unknown/duplicate ID {qid}')
            seen.add(qid);rn=int(addr[1:]);s=seed[qid]
            old={col:q.get(f'{col}{rn}','') for col in 'ABCDEFGHIJKLMNOPQ'}
            c=dict(old);reasons=[]
            def setcell(col,value,reason):
                if c[col]!=value:c[col]=value;reasons.append(reason)
            def note(text):
                if text not in c['P']:setcell('P',(c['P']+' | ' if c['P'] else '')+'Consolidation: '+text,text)
            # Source display is restored only from the unchanged Item 9 record.
            setcell('C',s['question_text'],'Restore original question from Item 9 source.')
            setcell('D','Taglish' if s['language_style']=='en_tl' else 'English','Restore original display language.')
            for col in 'I K L M P'.split():
                setcell(col,normalize(c[col]),'Normalize whitespace without changing meaning.')
            repair=plan['repairs'].get(qid,{})
            for col,value in repair.get('cells',{}).items():setcell(col,value,repair['reason'])
            if repair.get('reason'):note(repair['reason'])
            if c['I'] and c['H']=='Keep as written':setcell('H','Revise wording','Use the replacement already entered by the reviewer.')
            # Retain every human rejection. Resolve the rationale without pretending
            # that same-split paraphrases are leakage or exact textual duplicates.
            if c['N']=='Rejected':
                setcell('H','Reject wording','Retain the human rejection and exclude the variant.')
                setcell('I','','Rejected rows have no active replacement.')
                setcell('J','Labels correct','Discard invalid label overrides on excluded rows.')
                for col in 'KLM':setcell(col,'','Discard invalid label overrides on excluded rows.')
                note('Rejection retained as conservative variant selection. Similarity is not proof of exact duplication or split leakage; original reviewer rationale is preserved in provenance.')
            else:
                revised=c['H']=='Revise wording' or c['J']=='Change labels'
                setcell('N','Revised approved' if revised else 'Approved','Align the accepted outcome with the recorded changes.')
            primary=c['K'] if c['J']=='Change labels' else s['primary_label']
            scope=c['L'] if c['J']=='Change labels' else s['scope_label']
            text=c['I'] if c['H']=='Revise wording' else s['question_text']
            final_refs=repair.get('referral_ids',s['referral_ids'].split('|'))
            language=repair.get('language_style',s['language_style'])
            changed_columns=[col for col in c if c[col]!=old[col] and col not in 'OQ']
            if changed_columns:
                changes.append({'file':path.name,'row':rn,'question_id':qid,'actor':ACTOR,'changed_cells':{col+str(rn):{'before':old[col],'after':c[col]} for col in changed_columns},'reasons':list(dict.fromkeys(reasons))})
            final=dict(s)
            final.update(question_text=text,language_style=language,primary_label=primary,scope_label=scope,
                referral_ids=final_refs,dataset_version=VERSION,status_as_of=DATE,human_reviewer=reviewer,
                annotation_status='human_reviewed_owner_authorized_cleanup',review_notes=c['P'],
                review_outcome=c['N'],original_question_text=s['question_text'],original_language_style=s['language_style'],
                original_split=s['split'],original_dataset_version=s['dataset_version'],original_status_as_of=s['status_as_of'],
                source_workbook=path.name,source_row=rn,source_workbook_sha256=src['sha256'],
                original_review={k:old[k] for k in 'HIJKLMNP'},consolidation_actor=ACTOR,
                consolidation_changed=bool(changed_columns),consolidation_reasons=list(dict.fromkeys(reasons)),
                leakage_group_id=effective_group(s['scenario_group_id']))
            for key in ARRAYS:
                if isinstance(final[key],str):final[key]=list(filter(None,final[key].split('|')))
            all_rows.append(final);batch.append({'row':rn,'question_id':qid,'cells':c,'original_cells':old})
        workbooks.append({'file':path.name,'reviewer':reviewer,'rows':batch,'sha256':src['sha256']})
    if seen!=set(seed):raise ValueError('Returned workbooks do not cover all seed IDs.')
    accepted=[r for r in all_rows if r['review_outcome']!='Rejected']
    excluded=[r for r in all_rows if r['review_outcome']=='Rejected']
    # New split version. Original IDs/splits remain intact in the source workbooks
    # and explicit original_split field; all same-fact intent variants stay together.
    groups=defaultdict(list)
    for r in accepted:groups[r['leakage_group_id']].append(r)
    strata=defaultdict(list)
    for g,rs in groups.items():
        labels={(r['primary_label'],r['scope_label']) for r in rs}
        if len(labels)!=1:raise ValueError(f'Conflicting labels within scenario {g}')
        strata[next(iter(labels))].append(g)
    split_map={}
    for label,gs in sorted(strata.items()):
        ordered=sorted(gs,key=lambda g:hashlib.sha256(('item10-split-20261017|'+g).encode()).hexdigest())
        n=len(ordered);nv=max(1,round(n*.15));nt=max(1,round(n*.15));ntrain=n-nv-nt
        for i,g in enumerate(ordered):split_map[g]='train' if i<ntrain else 'validation' if i<ntrain+nv else 'test'
    for r in all_rows:
        r['split']=split_map.get(r['leakage_group_id'],'excluded')
        r['split_policy_version']='underlying_scenario_stratified_70_15_15_v1'
        if r in excluded:r['split']='excluded'
    OUTPUT.mkdir(parents=True,exist_ok=True);PAYLOAD.parent.mkdir(parents=True,exist_ok=True)
    accepted.sort(key=lambda r:r['question_id']);excluded.sort(key=lambda r:r['question_id'])
    for name,records in [('classifier_questions',accepted),('excluded_questions',excluded)]:
        write_csv(OUTPUT/(name+'.csv'),records)
        (OUTPUT/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records),encoding='utf-8')
    write_csv(OUTPUT/'referral_directory.csv',refs)
    write_json(OUTPUT/'consolidation_changes.json',changes)
    byid={r['question_id']:r for r in all_rows}
    resolutions=[]
    for finding in read_csv(ROOT/'outputs/item10-review-audit/action_list.csv'):
        r=byid[finding['question_id']]
        category=finding['category']
        result='Corrected review decisions and outcome; cleaned workbook row is Ready.'
        if category=='source_changed':result='Restored original question and display language from the unchanged Item 9 source.'
        elif category=='incompatible_labels':result=f"Restored scope-consistent {r['primary_label']}/{r['scope_label']}; rejected variants remain excluded."
        elif category=='topic_adjudication':result='Declined the topic suggestion; consumer.price_tags includes exact-change concerns.'
        elif category=='referral_adjudication':result='Accepted a context-specific referral correction: '+'|'.join(r['referral_ids'])+'.'
        elif category in ['wording_quality','scenario_changed']:result='Repaired wording while preserving the original scenario: '+r['question_text']
        elif category=='language_metadata':result='Final language recorded as '+r['language_style']+'; original language retained separately.'
        elif category=='rejection_adjudication':result='Human rejection retained as conservative variant selection. Exact-duplicate/leakage claims were not adopted; original rationale remains in provenance.'
        elif category=='unexpected_correction':result='Topic suggestion declined or referral suggestion accepted as recorded in the cleanup decisions and final referrals.'
        resolutions.append(dict(finding,resolution_status='resolved',resolution=result,actor=ACTOR))
    write_csv(OUTPUT/'audit_resolutions.csv',resolutions)
    write_json(PAYLOAD,{'version':VERSION,'date':DATE,'workbooks':workbooks,'referrals':refs})
    manifest={'dataset_version':VERSION,'status_as_of':DATE,'status':'pending_validation','source_seed_sha256':sha(seed_path),
        'source_workbooks':plan['workbooks'],'support_sources_sha256':plan['support_sources_sha256'],'cleanup_decisions_sha256':sha(HERE/'review_cleanup_decisions.json'),
        'consolidation_actor':ACTOR,'authorization':'Project owner: i trust you. please repair and do the cleanup yourself with discretion of course.',
        'counts':{'reviewed':len(all_rows),'included':len(accepted),'excluded':len(excluded),'changed_rows':len(changes),
            'labels':dict(Counter(r['primary_label'] for r in accepted)),'scopes':dict(Counter(r['scope_label'] for r in accepted)),
            'languages':dict(Counter(r['language_style'] for r in accepted)),'splits':dict(Counter(r['split'] for r in accepted)),
            'leakage_groups':len(groups)},
        'split_policy':{'version':'underlying_scenario_stratified_70_15_15_v1','random_seed':'item10-split-20261017',
            'method':'SHA256-ranked whole underlying scenarios stratified by primary and scope labels; group targets 70/15/15; original IDs and splits retained.',
            'original_scenario_group_ids_preserved':True},
        'training_ready':False,'remaining_prerequisites':['Independent human-written and labeled gold set prepared and locked','Team/adviser performance targets and abstention policy recorded'],
        'limitations':['One human reviewer per seed row; owner-authorized AI cleanup is disclosed, not a second independent human annotation.',
            'Synthetic partitions still share generator style; new split grouping removes full-scenario overlap but does not prove real-world generalization.',
            'Inherited agency contact details retain their Item 9 verification dates; this cleanup is a routing review, not a contact-directory freshness certification.']}
    write_json(OUTPUT/'dataset_manifest.json',manifest)
    print(json.dumps(manifest['counts'],indent=2))

if __name__=='__main__':main()
