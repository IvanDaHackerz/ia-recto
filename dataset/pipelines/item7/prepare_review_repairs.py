"""Prepare source-grounded AI repair proposals without promoting pending sources."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]

def dti_sections(pages):
    """A line-wrapped cross-reference is not a new section or a Rule heading."""
    chunks=[];spans=[];offset=0
    for p in pages:
        text=p['text']
        # The stamped footer is outside the legal text; preserve the raw OCR input.
        text=re.split(r'(?im)^\s*CERTIFIED\s+TRUE\b',text)[0].strip()
        chunks.append(text);spans.append((offset,offset+len(text),p['pdf_page']));offset+=len(text)+2
    text='\n\n'.join(chunks)
    rule_pattern=re.compile(r'(?m)^RULE[ \t]+[IVXLCil|0-9]+[ \t]*\n[ \t]*(TITLE and SCOPE|INITIAL COMPLAINTS|MEDIATION|ADJUDICATION|OTHER PROVISIONS)[ \t]*$',re.I)
    rule_names={'title and scope':'I','initial complaints':'II','mediation':'III','adjudication':'IV','other provisions':'V'}
    rules=[(m.start(),m.end(),rule_names[m.group(1).lower()]) for m in rule_pattern.finditer(text)]
    boundaries=list(re.finditer(r'(?im)^(?:Section|Sec\.)[ \t]+(?P<num>\d+)\.[ \t]+(?P<head>[^\n]+)',text))
    result=[]
    for i,m in enumerate(boundaries):
        previous=[r for r in rules if r[0]<m.start()]
        rule=previous[-1][2] if previous else None
        end=boundaries[i+1].start() if i+1<len(boundaries) else len(text)
        next_rules=[r[0] for r in rules if m.end()<r[0]<end]
        if next_rules:end=min(next_rules)
        touched=[page for a,b,page in spans if b>m.start() and a<end]
        result.append({'rule':rule,'section':int(m.group('num')),'candidate_text':text[m.start():end].strip(),
            'pdf_page_start':min(touched),'pdf_page_end':max(touched),
            'review_status':'ai_structure_repaired_pending_text_review','answer_eligible':False})
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    if a.output_dir.exists():raise ValueError('Do not overwrite a review packet')
    a.output_dir.mkdir(parents=True)
    provisions=rows(ROOT/'dataset/processed/item7/provisions.jsonl')
    proposals=[]
    for r in provisions:
        if r['document_id']!='DOLE_LA_06_20':continue
        text=r['normalized_text']
        if r['provision_id'].endswith('__i'):
            text=text.replace('13" month','13th month').replace('(9) Income tax','(g) Income tax')
        if r['provision_id'].endswith('__iv'):
            text=text.split('Be guided accordingly.')[0].strip()
        image_names=['finalpay-1.png','finalpay-2.png'] if r['provision_id'].endswith('__i') else ['finalpay-2.png']
        images=[ROOT/'tmp/pdfs/pre-item12'/name for name in image_names]
        proposals.append({'provision_id':r['provision_id'],'original_text_sha256':hashlib.sha256(r['normalized_text'].encode()).hexdigest(),
            'original_text':r['normalized_text'],'proposed_text':text,'source_locator':r['source_locator'],
            'review_actor':'Codex','review_origin':'AI visual comparison of preserved official PDF pages',
            'page_image_sha256':{str(f.relative_to(ROOT)):sha(f) for f in images},
            'independent_human_review':False,'legal_professional_review':False,'answer_eligible':False,
            'decision':'text_compared_by_ai_pending_required_human_source_review'})
    pages=[r for r in rows(ROOT/'tmp/item7_ocr/ocr_output.jsonl') if r['document_id']=='DTI_DAO_20_02']
    candidates=dti_sections(pages)
    (a.output_dir/'final_pay_text_repairs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in proposals),encoding='utf-8')
    (a.output_dir/'dti_structure_repairs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in candidates),encoding='utf-8')
    pending=[r for r in provisions if r['review_status']=='human_review_required']
    triage=[]
    for r in pending:
        priority='core_source_review' if r['document_id'] in {'DOLE_LA_06_20','DTI_DAO_20_02','DOLE_DO_249_25'} else 'scope_or_historical_triage_first'
        triage.append({'provision_id':r['provision_id'],'document_id':r['document_id'],
            'citation':r['citation_display'],'priority':priority,'source_locator':r['source_locator'],
            'quality_flags':r['quality_flags'],'current_text':r['normalized_text'],
            'human_reviewer':None,'human_decision':None,'answer_eligible':False})
    (a.output_dir/'source_review_intake.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in triage),encoding='utf-8')
    summary={'original_source_records_modified':False,'independent_human_approval_recorded':False,
        'pending_provisions':len(pending),'final_pay_ai_visual_proposals':len(proposals),
        'dti_original_provisions':sum(r['document_id']=='DTI_DAO_20_02' for r in provisions),
        'dti_structure_candidates':len(candidates),'all_candidates_remain_gated':True,
        'ocr_input_sha256':sha(ROOT/'tmp/item7_ocr/ocr_output.jsonl')}
    (a.output_dir/'source_repair_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
if __name__=='__main__':main()
