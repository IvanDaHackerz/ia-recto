"""Validate cleaned workbooks, source preservation, labels, provenance and splits."""
from __future__ import annotations
import argparse, csv, json, re
from collections import Counter,defaultdict
from pathlib import Path
import openpyxl  # Reading/verification only; workbooks are authored with Artifact Tool.
from consolidate_reviews import ROOT, HERE, OUTPUT, PAYLOAD, sha, read_csv, write_json, effective_group

def load_jsonl(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]
def value(v):return '' if v is None else v
def native_signature(ws):
    return {'tables':sorted((t.name,t.ref,t.tableStyleInfo.name if t.tableStyleInfo else None) for t in ws.tables.values()),
        'freeze_panes':str(ws.freeze_panes),'state':ws.sheet_state,
        'merged_ranges':sorted(str(r) for r in ws.merged_cells.ranges),
        'validations':sorted((str(v.sqref),v.type,v.formula1,v.formula2,v.operator) for v in ws.data_validations.dataValidation),
        'conditional_formatting':sorted(str(r) for r in ws.conditional_formatting),
        'hidden_columns':sorted(k for k,v in ws.column_dimensions.items() if v.hidden),
        'hidden_rows':sorted(k for k,v in ws.row_dimensions.items() if v.hidden),
        'filter_ref':ws.auto_filter.ref,'protection_enabled':ws.protection.sheet}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    errors=[];checks={};warnings=[]
    def check(name,condition):
        checks[name]=bool(condition)
        if not condition:errors.append(name)
    plan=json.loads((HERE/'review_cleanup_decisions.json').read_text(encoding='utf-8'))
    manifest=json.loads((OUTPUT/'dataset_manifest.json').read_text(encoding='utf-8'))
    payload=json.loads(PAYLOAD.read_text(encoding='utf-8'))
    accepted=load_jsonl(OUTPUT/'classifier_questions.jsonl');excluded=load_jsonl(OUTPUT/'excluded_questions.jsonl')
    allrows=accepted+excluded; seed={r['question_id']:r for r in read_csv(ROOT/'dataset/processed/item9/classifier_questions.csv')}
    topics={r['topic_id']:r for r in read_csv(ROOT/'dataset/data_contract/topic_taxonomy.csv')}
    refs={r['referral_id']:r for r in read_csv(OUTPUT/'referral_directory.csv')}
    check('seed_unchanged',sha(ROOT/'dataset/processed/item9/classifier_questions.csv')==plan['seed_sha256'])
    check('cleanup_reference_sources_unchanged',all(sha(ROOT/p)==expected for p,expected in plan['support_sources_sha256'].items()))
    check('complete_unique_question_ids',len(allrows)==len(seed)==672 and len({r['question_id'] for r in allrows})==672 and {r['question_id'] for r in allrows}==set(seed))
    check('included_excluded_reconcile',len(accepted)==661 and len(excluded)==11)
    expected_excluded={item['question_id'] for b in payload['workbooks'] for item in b['rows'] if item['original_cells']['N']=='Rejected'}
    check('all_human_rejections_retained',expected_excluded=={r['question_id'] for r in excluded})
    check('accepted_have_approved_outcome',all(r['review_outcome'] in ['Approved','Revised approved'] for r in accepted))
    check('excluded_never_in_model_split',all(r['review_outcome']=='Rejected' and r['split']=='excluded' for r in excluded))
    texts=[re.sub(r'\W+',' ',r['question_text'].casefold()).strip() for r in accepted]
    check('no_exact_normalized_duplicates',len(texts)==len(set(texts)))
    check('nonempty_text_and_reviewers',all(r['question_text'].strip() and r['human_reviewer'].strip() for r in allrows))
    check('source_provenance_preserved',all(r['original_question_text']==seed[r['question_id']]['question_text'] and r['original_split']==seed[r['question_id']]['split'] and r['scenario_group_id']==seed[r['question_id']]['scenario_group_id'] and r['original_language_style']==seed[r['question_id']]['language_style'] for r in allrows))
    check('ai_cleanup_disclosed',all(r['annotation_status']=='human_reviewed_owner_authorized_cleanup' and r['consolidation_actor']=='Codex (project-owner-authorized cleanup)' and r['original_review'] for r in allrows))
    resolutions=read_csv(OUTPUT/'audit_resolutions.csv')
    findings=read_csv(ROOT/'outputs/item10-review-audit/action_list.csv')
    check('all_audit_findings_resolved_with_provenance',len(resolutions)==len(findings)==82 and all(r['resolution_status']=='resolved' and r['resolution'] and r['actor'] for r in resolutions))
    group_splits=defaultdict(set);original_groups=defaultdict(set)
    label_errors=[];route_errors=[];ref_errors=[]
    for r in accepted:
        qid=r['question_id'];sup=r['supported_topic_ids'];exc=r['excluded_topic_ids']
        group_splits[effective_group(r['scenario_group_id'])].add(r['split']);original_groups[r['scenario_group_id']].add(r['split'])
        if any(t not in topics or topics[t]['scope_status']!='supported' for t in sup) or any(t not in topics or topics[t]['scope_status']!='excluded' for t in exc):label_errors.append(qid);continue
        domains={topics[t]['domain'] for t in sup}
        expected=('out_of_scope','unsupported','decline_and_refer') if not sup else ('mixed','partially_supported','partial_answer_and_refer') if exc else ('mixed','fully_supported','answer_multiple_supported_domains') if len(domains)==2 else (next(iter(domains)),'fully_supported','answer')
        if (r['primary_label'],r['scope_label'])!=expected[:2]:label_errors.append(qid)
        if r['routing_action']!=expected[2]:route_errors.append(qid)
        if any(x not in refs for x in r['referral_ids']):ref_errors.append(qid)
        if 'labor.seafarers' in exc:
            text=r['question_text'].casefold()
            if 'overseas deployment' in text and 'REF_DMW' not in r['referral_ids']:ref_errors.append(qid)
            if 'onboard pay' in text and 'REF_PAO' not in r['referral_ids']:ref_errors.append(qid)
    check('labels_match_supported_excluded_topics',not label_errors)
    check('routing_matches_scope',not route_errors)
    check('known_and_context_appropriate_seafarer_referrals',not ref_errors)
    check('underlying_scenarios_stay_in_one_split',all(len(s)==1 for s in group_splits.values()))
    check('original_scenario_groups_stay_in_one_split',all(len(s)==1 for s in original_groups.values()))
    check('languages_valid',all(r['language_style'] in ['en','en_tl'] for r in accepted))
    check('all_topics_represented',set(topics)=={t for r in accepted for t in r['supported_topic_ids']+r['excluded_topic_ids']})
    check('all_labels_scopes_languages_in_each_split',all({r['primary_label'] for r in accepted if r['split']==sp}=={'labor','consumer','mixed','out_of_scope'} and {r['scope_label'] for r in accepted if r['split']==sp}=={'fully_supported','partially_supported','unsupported'} and {r['language_style'] for r in accepted if r['split']==sp}=={'en','en_tl'} for sp in ['train','validation','test']))
    # Verify all typed CSV fields agree with JSONL, not merely row counts.
    for name,records in [('classifier_questions',accepted),('excluded_questions',excluded)]:
        csvrows=read_csv(OUTPUT/(name+'.csv'))
        serialized=[{k:'|'.join(v) if isinstance(v,list) else json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,dict) else str(v) for k,v in r.items()} for r in records]
        check(name+'_csv_jsonl_agree',csvrows==serialized)
    workbook_results=[]
    for batch in payload['workbooks']:
        orig=ROOT/'outputs/item10-review-workbooks'/batch['file'];clean=ROOT/'outputs/item10-review-cleaned'/batch['file']
        check(batch['file']+':original_unchanged',sha(orig)==batch['sha256'])
        x=openpyxl.load_workbook(orig,data_only=False);y=openpyxl.load_workbook(clean,data_only=False);cached=openpyxl.load_workbook(clean,data_only=True)
        check(batch['file']+':sheet_order_preserved',x.sheetnames==y.sheetnames)
        differences=[];native_differences=[]
        for n in x.sheetnames:
            if native_signature(x[n])!=native_signature(y[n]):native_differences.append(n)
            if n in ['Instructions','Topic Guide','Source Data','Progress']:
                for row in x[n]:
                    for cell in row:
                        if n=='Progress' and cell.coordinate=='A3':continue # Shortened subtitle to fit.
                        if value(cell.value)!=value(y[n][cell.coordinate].value):differences.append(n+'!'+cell.coordinate)
        check(batch['file']+':source_reference_and_progress_formulas_preserved',not differences)
        check(batch['file']+':native_tables_dropdowns_panes_preserved',not native_differences)
        q=y['Review Queue'];qc=cached['Review Queue'];row_errors=[];field_errors=[]
        for item in batch['rows']:
            rn=item['row'];c=item['cells']
            for col in 'ABCDEFGHIJKLMNOP':
                if col=='O':continue # Formula is compared independently.
                actual=value(q[f'{col}{rn}'].value);expected=c[col]
                # Original No. cells are numeric; compare their numeric meaning.
                if col=='A':same=float(actual)==float(expected)
                else:same=actual==expected
                if not same:field_errors.append(f'{col}{rn}')
            if q[f'O{rn}'].value!=x['Review Queue'][f'O{rn}'].value:field_errors.append(f'O{rn}')
            if qc[f'Q{rn}'].value!='Ready' or not str(q[f'Q{rn}'].value).startswith('=IF('):row_errors.append(rn)
            if c['N'] in ['Needs group discussion','Rejected'] and not c['P']:row_errors.append(rn)
            if c['H']=='Revise wording' and (not c['I'] or c['N']!='Revised approved'):row_errors.append(rn)
            if c['H']!='Revise wording' and c['I']:row_errors.append(rn)
            if c['J']=='Labels correct' and any(c[k] for k in 'KLM'):row_errors.append(rn)
        check(batch['file']+':cleaned_fields_match_adjudication',not field_errors)
        check(batch['file']+':all_rows_ready_and_consistent',not row_errors)
        check(batch['file']+':ready_counts_recalculate',cached['Progress']['B8'].value==len(batch['rows']) and cached['Progress']['B9'].value==0 and cached['Progress']['B13'].value==1)
        workbook_results.append({'file':batch['file'],'rows':len(batch['rows']),'ready':len(batch['rows'])-len(set(row_errors)),'field_errors':field_errors,'native_differences':native_differences,'unexpected_cell_changes':differences})
    warnings.extend(manifest['limitations'])
    training_topics={t for r in accepted if r['split']=='train' for t in r['supported_topic_ids']+r['excluded_topic_ids']}
    if set(topics)-training_topics:warnings.append('Some topic IDs are absent from training: '+str(sorted(set(topics)-training_topics)))
    check('training_gate_remains_explicit',manifest['training_ready'] is False and len(manifest['remaining_prerequisites'])==2)
    rebuild=json.loads((OUTPUT/'reproducibility_check.json').read_text(encoding='utf-8'))
    check('data_rebuild_is_deterministic',rebuild['status']=='passed' and len(rebuild['file_hashes'])>=7)
    report={'status':'passed' if not errors else 'failed','checks':checks,'errors':errors,'warnings':warnings,'counts':manifest['counts'],'workbooks':workbook_results,'training_ready':False}
    if manifest['status']=='frozen_reviewed_seed':
        if not all(sha(OUTPUT/name)==expected for name,expected in manifest['files_sha256'].items()):errors.append('Frozen data file checksum mismatch')
        if not all(sha(ROOT/'outputs/item10-review-cleaned'/name)==expected for name,expected in manifest['cleaned_workbooks_sha256'].items()):errors.append('Frozen cleaned workbook checksum mismatch')
        print(json.dumps({'status':'passed' if not errors else 'failed','checks':len(checks),'errors':errors,'frozen_snapshot_unchanged':not errors,'training_ready':False},indent=2))
        return 0 if not errors else 1
    write_json(OUTPUT/'validation_report.json',report)
    if args.freeze and not errors:
        manifest['status']='frozen_reviewed_seed'
        manifest['files_sha256']={p.name:sha(p) for p in sorted(OUTPUT.iterdir()) if p.is_file() and p.name!='dataset_manifest.json'}
        manifest['cleaned_workbooks_sha256']={b['file']:sha(ROOT/'outputs/item10-review-cleaned'/b['file']) for b in payload['workbooks']}
        write_json(OUTPUT/'dataset_manifest.json',manifest)
    print(json.dumps({'status':report['status'],'passed_checks':sum(checks.values()),'total_checks':len(checks),'errors':errors,'training_ready':False,'warnings':warnings},indent=2))
    return 0 if not errors else 1

if __name__=='__main__':raise SystemExit(main())
