"""Build reviewed-page extracts without editing the original Item 7 corpus.

Run with the bundled PDF Python (pypdf). This is a preparation utility; live
retrieval loads the frozen JSON and needs no PDF library or network.
"""
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
RAW='dataset/canonical_sources/raw/labor/reliability_2026_10_26/dole_bwc_handbook_2024_nwpc.pdf'
DEST=ROOT/'dataset/canonical_sources/supplements/labor_basics_v1.0.0.json'
DOC='DOLE_BWC_HANDBOOK_2024'
URL='https://nwpc.dole.gov.ph/wp-content/uploads/2024/11/Workers-Statutory-Monetary-Benefits-Handbook-2024-Edition.pdf'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rows=lambda name:[json.loads(s) for s in (ROOT/f'dataset/processed/item7/{name}.jsonl').read_text(encoding='utf-8').splitlines()]
sha=lambda text:hashlib.sha256(text.encode()).hexdigest()


def main():
    raise ValueError('Rejected draft: handbook is explanatory-only. Use prepare_labor_evidence.py; never promote this proposal.')
    if DEST.exists():raise ValueError('Supplement is immutable; create a new version')
    from pypdf import PdfReader
    reader=PdfReader(ROOT/RAW)
    pages={i+1:(p.extract_text() or '') for i,p in enumerate(reader.pages)}
    def body(n):
        lines=pages[n].splitlines()
        if lines and lines[0].strip().isdigit():lines=lines[1:]
        return '\n'.join(line.rstrip() for line in lines).strip()
    def section(text,start,end=None):
        text=text[text.index(start):]
        return (text[:text.index(end)] if end else text).strip()
    source17,source18,source19=body(17),body(18),body(19)
    night=body(35)+'\n\n'+body(36)
    # Restore the continuous coverage sentence across the PDF page break;
    # retain the printed footnotes separately after that sentence.
    cover50=body(50);main50,notes50=cover50.split('jj See Revised Guidelines',1)
    before_amount=body(51).split('C. Amount',1)[0]
    definition_coverage=main50+'\n'+before_amount+'\n\nSource footnotes:\njj See Revised Guidelines'+notes50
    definitions=[
        ('hours_worked','Hours worked',17,17,section(source17,'1. Hours worked','2. Principles'),['labor.hours_of_work']),
        ('hours_principles','Principles in determining hours worked',18,18,section(source18,'a. All hours are hours worked','3. Treatment'),['labor.hours_of_work']),
        ('waiting_time','Treatment on waiting time',18,18,section(source18,'3. Treatment on waiting time','4. Attendance'),['labor.hours_of_work']),
        ('meetings_attendance','Attendance at lectures, meetings and training',18,18,section(source18,'4. Attendance'),['labor.hours_of_work']),
        ('meal_rest_periods','Meal and Rest Periods',19,19,section(source19,'5. Meal and Rest Periods','D. Monthly'),['labor.hours_of_work']),
        ('night_differential','Night Shift Differential: definition, coverage and rate',35,36,night,['labor.wages_payment','labor.hours_of_work']),
        ('thirteenth_coverage','Thirteenth-month pay: definition and coverage',50,51,definition_coverage,['labor.thirteenth_month_pay']),
        ('thirteenth_amount','Thirteenth-month pay: amount and basic salary',51,51,section(body(51),'C. Amount','D. Computation'),['labor.thirteenth_month_pay']),
        ('thirteenth_timing','Thirteenth-month pay: time of payment',52,52,section(body(52),'E. Time of Payment','F.  Thirteenth'),['labor.thirteenth_month_pay']),
        ('thirteenth_separation','Thirteenth-month pay: resigned or separated employees',52,53,section(body(52),'G. Thirteenth-Month')+'\n'+section(body(53),'month pay should be equal','H. Thirteenth'),['labor.thirteenth_month_pay']),
    ]
    docs,provs,chunks=rows('documents'),rows('provisions'),rows('retrieval_chunks')
    d=copy.deepcopy(next(d for d in docs if d['document_id']=='LAB_CODE_2022'))
    freshness='Recorded 2024 agency handbook only. Verify subsequent law/issuances and individual coverage before current guidance. No regional wage amounts, tax, pension, maternity or special-worker module is added. Original held OCR and MO 28 records remain held.'
    d.update(document_id=DOC,citation='DOLE-BWC Workers’ Statutory Monetary Benefits, 2024 Handbook',
        title='DOLE-BWC Handbook on Workers’ Statutory Monetary Benefits — 2024 edition',
        document_type='agency_handbook',approval_or_edition_date='2024',source_id='DOLE_BWC_HANDBOOK',
        official_source_url=URL,retrieval_url=URL,raw_local_path=RAW,
        verification_status='verified_official_pdf_text;81_pages;publisher_and_selected_pages_ai_visual_compared',
        collection_role='bounded_agency_framework_supplement',legal_status='recorded_2024_agency_guidance_current_applicability_unreviewed',
        status_as_of='2024-11-04',retrieval_use_policy='framework_only',freshness_rule=freshness,
        version_label='2024; selected pages checked by AI on 2026-10-26',
        notes='Official NWPC mirror. Selected working-time/night-differential/thirteenth-month passages only. Text and images were compared by Codex, not an independent human or legal reviewer. No current-law certification.')
    new_provs=[];new_chunks=[]
    for sequence,(key,heading,start,end,text,topics) in enumerate(definitions,1):
        p=copy.deepcopy(next(p for p in provs if p['provision_id']=='LAB_CODE_2022__art_84'))
        locator=f'2024 Handbook, {heading}, PDF pp. {start}–{end}'
        p.update(provision_id=DOC+'__'+key,document_id=DOC,sequence_number=sequence,provision_level='section',
            locator_label=locator,locator_normalized=key,heading=heading,
            hierarchy={'book':None,'title':'2024 Handbook','chapter':heading,'part':None,'rule':None},
            citation_display=d['citation']+', '+heading,verbatim_text=text,normalized_text=text,
            search_text=' '.join((d['title']+' '+heading+' '+text).casefold().split()),
            source_locator={'pdf_page_start':start,'pdf_page_end':end,'printed_page_start':str(start-10),'printed_page_end':str(end-10),
                'html_anchor':None,'source_region':'Selected complete handbook subsection; PDF text and page image comparison',
                'source_char_start':None,'source_char_end':None},
            scope_status='supported',supported_topics=topics,excluded_topics=[],provision_answer_eligible=True,
            answer_use_mode='default_answer',legal_status=d['legal_status'],status_family=d['status_family'],
            status_as_of=d['status_as_of'],relationship_ids=[],quality_flags=[],manual_repairs=[],footnotes=[],review_status='machine_validated')
        c=copy.deepcopy(next(c for c in chunks if c['provision_id']=='LAB_CODE_2022__art_84'))
        c.update(chunk_id=p['provision_id']+'__chunk_0001',document_id=DOC,provision_id=p['provision_id'],
            context_prefix=d['title']+' > '+heading,display_text=text,retrieval_text=d['title']+'\n'+heading+'\n'+text,
            normalized_char_start=0,normalized_char_end=len(text),character_count=len(text),
            scope_status='supported',supported_topics=topics,excluded_topics=[],answer_eligible=True,answer_use_mode='default_answer',
            legal_status=d['legal_status'],status_family=d['status_family'],status_as_of=d['status_as_of'],citation_display=p['citation_display'],quality_flags=[])
        new_provs.append(p);new_chunks.append(c)
    catalog={'document_id':DOC,'local_path':RAW.removeprefix('dataset/canonical_sources/'),'official_source_url':URL,'retrieval_url':URL,
             'verification_status':d['verification_status'],'answer_eligible_candidate':'true'}
    legal={k:d[k] for k in ['document_id','legal_status','status_as_of','retrieval_use_policy','freshness_rule']}
    registry={'source_id':d['source_id'],'authority_level':'primary_official','permitted_use':'answer_and_citation','answer_eligible':'true',
              'organization':'DOLE Bureau of Working Conditions; official NWPC mirror','verification_method':'Publisher attribution, official host, PDF hash, complete relevant page comparison; no independent legal-currentness approval.'}
    mapping=[]
    for pid in ['LAB_CODE_2022__art_84','LAB_CODE_2022__art_85']:
        p=next(p for p in provs if p['provision_id']==pid)
        mapping.append({'provision_id':pid,'parent_text_sha256':sha(p['normalized_text']),'supported_topics':['labor.hours_of_work'],
                        'reason':'Clean machine-extracted basic working-time rule falls within the frozen hours-of-work topic; previous topic mapping missed this heading. No text, legal status or human-review state is changed.'})
    data={'schema_version':'1.0','prepared_on':'2026-10-26','purpose':'Owner-authorized source-gap audit and bounded development recovery',
          'independent_human_or_legal_approval':False,'raw_sha256':{RAW:hashlib.sha256((ROOT/RAW).read_bytes()).hexdigest()},
          'documents':[d],'provisions':new_provs,'chunks':new_chunks,'canonical':[catalog],'legal_status':[legal],'registry':[registry],
          'scope_mapping_repairs':mapping,
          'visual_comparison':{'reviewer':'Codex AI','pdf_pages':[17,18,19,35,36,50,51,52,53],'independent_human_review':False,
            'notes':['Selected complete subsections; regional wage tables, commission-case discussion, tax, pension and special-worker modules omitted.',
                     'Thirteenth-month definition/coverage sentence restored across page break; page-40 footnotes retained after the completed coverage list.',
                     'Extracted line wrapping and spacing are preserved; no source sentence was paraphrased.']},
          'remaining_holds':['DOLE_LA_06_20 original scanned advisory still requires the original source-review sign-off.',
                             'Stored MO_28_1986 wording/copy remains non-answer-eligible. The separate official agency handbook is not a replacement official MO 28 copy.',
                             'Current-year or present-law applicability still requires scoped trusted legal review.']}
    DEST.parent.mkdir(exist_ok=True)
    DEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Prepared',len(new_provs),'bounded handbook records and',len(mapping),'clean scope-map repairs; original corpus files unchanged.')


if __name__=='__main__':main()
