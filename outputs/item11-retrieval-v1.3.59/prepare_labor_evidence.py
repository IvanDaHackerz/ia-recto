"""Prepare bounded official excerpts; original handbook/OCR/MO holds stay intact."""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'dataset/canonical_sources/supplements'
RAW='dataset/canonical_sources/raw/labor/reliability_2026_10_26/'
def main():
 from pypdf import PdfReader
 dest=BASE/'labor_basics_v1.0.1.json'
 if dest.exists():raise ValueError('Immutable supplement already exists')
 old=json.loads((BASE/'labor_basics_v1.0.0.json').read_text(encoding='utf-8'))
 out={k:copy.deepcopy(old[k]) for k in ['schema_version','prepared_on','independent_human_or_legal_approval']}
 out.update(documents=[],provisions=[],chunks=[],canonical=[],legal_status=[],registry=[],raw_sha256={})
 out['verification_only_handbook_extracts']=old['provisions']
 out['rejected_proposal']='v1.0.0 attempted duplicate handbook authority and was rejected by loader; never built or selected. Handbook remains explanatory-only.'
 read=lambda name:[json.loads(s) for s in (ROOT/f'dataset/processed/item7/{name}.jsonl').read_text(encoding='utf-8').splitlines()]
 provs=read('provisions');out['scope_mapping_repairs']=[]
 for pid in ['LAB_CODE_2022__art_84','LAB_CODE_2022__art_85']+[f'LAB_IRR_1989__rule_i_hours_of_work__section_{i}' for i in range(3,8)]:
  p=next(p for p in provs if p['provision_id']==pid)
  out['scope_mapping_repairs'].append({'provision_id':pid,'parent_text_sha256':hashlib.sha256(p['normalized_text'].encode()).hexdigest(),'supported_topics':['labor.hours_of_work'],'reason':'Missed basic working-time topic mapping only; preserve source text, quality flags and review state.'})
 newsraw=RAW+'dole_final_pay_coe_2026_browser_capture.json'
 news=json.loads((ROOT/newsraw).read_text(encoding='utf-8'))
 scraw=RAW+'sc_volume_298.pdf';page=PdfReader(ROOT/scraw).pages[578].extract_text()
 quote=page[page.index('The Rules and Regulations Implementing P.D. No. 851'):page.index('In connection with and in implementation of Memorandum Order')].strip()
 entries=[('DOLE_FINAL_PAY_COE_NEWS_2026','DOLE agency statement on final pay and COE (22 January 2026)',newsraw,news['source_url'],'2026-01-22','\n\n'.join(news['paragraphs']),['labor.final_pay_coe'],'Final pay and certificate of employment timelines',None,
 'Recorded official agency statement describing LA 06-20, not a verified full advisory. Better company policy is a summary: check favorable individual or collective agreements too. Do not infer automatic entitlement to every final-pay component. Verify later issuances and worker coverage before current guidance.'),
 ('SC_110068_1993_STATUTORY_QUOTES','Thirteenth-month statutory quotations in Philippine Duplicators, G.R. 110068 (1993)',scraw,'https://elibrary.judiciary.gov.ph/assets/pdf/philrep_ebooks/Volume_298.pdf','1993-11-11',quote,['labor.thirteenth_month_pay'],'Thirteenth-month pay: quoted definition and rank-and-file payment rule',579,
 'Complete statutory definitions and operative MO 28 quotation only, from an official 1993 decision; not the whole MO, syllabus or case ruling. Original PD 851/MO 28 dependency remains held. Do not infer complete exemptions, minimum service, commission treatment or current applicability. Check later law and worker coverage before current guidance.')]
 for did,title,raw,url,date,text,topics,heading,pdfpage,note in entries:
  d=copy.deepcopy(old['documents'][0]);d.update(document_id=did,citation=title,title=title,source_id=did,document_type='official_corroborating_excerpt',issuer='Supreme Court of the Philippines' if pdfpage else 'Department of Labor and Employment',raw_local_path=raw,raw_file_format='pdf' if pdfpage else 'json',official_source_url=url,retrieval_url=url,approval_or_edition_date=date,status_as_of=date,collection_role='bounded_official_corroborating_excerpt',legal_status='recorded_official_quotation_current_applicability_unreviewed',freshness_rule=note,notes=note,verification_status='verified_official_selected_text;machine_extracted;AI_compared;independent_review_pending',version_label=date+'; selected text checked 2026-10-26')
  p=copy.deepcopy(old['provisions'][0]);p.update(provision_id=did+'__recorded_rule',document_id=did,heading=heading,locator_label='Recorded official excerpt',locator_normalized='recorded_rule',citation_display=title+(', Philippine Reports 298, p. 556' if pdfpage else ''),verbatim_text=text,normalized_text=text,search_text=' '.join((title+' '+heading+' '+text).casefold().split()),supported_topics=topics,legal_status=d['legal_status'],status_as_of=date,source_locator={'pdf_page_start':pdfpage,'pdf_page_end':pdfpage,'printed_page_start':'556' if pdfpage else None,'printed_page_end':'556' if pdfpage else None,'html_anchor':None if pdfpage else 'rendered-agency-policy-paragraphs','source_region':'Selected complete statutory quotations; AI page-image comparison' if pdfpage else 'Generic agency policy paragraphs 1, 2, 5; rendered browser accessibility capture','source_char_start':None,'source_char_end':None},hierarchy={'book':None,'title':title,'chapter':heading,'part':None,'rule':None},extraction_method='pdf_text' if pdfpage else 'html_structural')
  c=copy.deepcopy(old['chunks'][0]);c.update(chunk_id=p['provision_id']+'__chunk_0001',provision_id=p['provision_id'],document_id=did,context_prefix=title+' > '+heading,display_text=text,retrieval_text=title+'\n'+heading+'\n'+text,normalized_char_start=0,normalized_char_end=len(text),character_count=len(text),supported_topics=topics,legal_status=d['legal_status'],status_as_of=date,citation_display=p['citation_display'])
  out['documents'].append(d);out['provisions'].append(p);out['chunks'].append(c)
  out['canonical'].append({'document_id':did,'local_path':raw.removeprefix('dataset/canonical_sources/'),'official_source_url':url,'retrieval_url':url,'verification_status':d['verification_status'],'answer_eligible_candidate':'true'})
  out['legal_status'].append({k:d[k] for k in ['document_id','legal_status','status_as_of','retrieval_use_policy','freshness_rule']})
  out['registry'].append({'source_id':did,'authority_level':'primary_official','permitted_use':'answer_and_citation','answer_eligible':'true'})
  out['raw_sha256'][raw]=hashlib.sha256((ROOT/raw).read_bytes()).hexdigest()
 out['remaining_holds']=['Original DOLE_LA_06_20 OCR and MO_28_1986 suspect copy remain held.','Handbook remains explanatory-only.','Independent human/legal and current-applicability review remains pending.']
 dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Prepared two bounded official excerpts and seven clean scope-map repairs.')
if __name__=='__main__':main()
