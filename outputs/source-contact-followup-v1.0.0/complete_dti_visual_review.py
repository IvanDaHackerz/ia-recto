"""Apply AI page-image comparisons to an immutable, explicitly AI-reviewed copy."""
from __future__ import annotations
import argparse,hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

OVERRIDES={
 ('IV',4):"""Section 4. Powers and Duties of the Adjudication Officer. The Adjudication Officer shall exercise the following powers and duties:
a. Issue Notice of Adjudication;
b. Administer oaths and affirmations;
c. Issue preliminary orders, preventive orders, temporary orders and other processes;
d. Regulate and maintain order in the adjudication proceedings;
e. Issue subpoena duces tecum;
f. Receive evidence of the parties;
g. Rule upon proofs proffered;
h. Rule on any procedural request;
i. Render a decision in accordance with Section 13 of this Rule; and
j. Perform such other functions as would contribute to the just, speedy and cost effective resolution of the case.""",
 ('IV',9):"""Section 9. Filing and Service of Position Papers, Pleadings, Notices, Orders and Decisions.
a. Filing and Service of Position Papers and Other Pleadings. Position Papers shall be accompanied by their supporting affidavits and documentary evidence. They shall be filed in their original copies with the concerned DTI Office within a non-extendable period of ten (10) working days from receipt of NOA, except that photocopies of the supporting documents may be allowed to be filed for good reason that the same bear the signatures or initials of the Adjudication Officer, or, in his/her absence, any Adjudication Officer of the same DTI Office, which signatures or initials shall serve as certification that their originals have been presented to him/her and that the photocopies are faithful reproduction of the originals.
Any subsequent pleadings, if required by the Adjudication Officer for justifiable reason, shall be filed not more than three (3) working days from date of the order requiring their filing.
No position paper or pleading shall be allowed to be filed unless prior service of a copy thereof is made on the adverse party/ies as evidenced by proof of personal service in accordance with Section 6 of this Rule, or by a courier receipt or registry receipt showing that a copy of the position paper or pleading has been deposited with the courier or postal service for delivery to the adverse party/ies.
b. Service of Notices, Orders, Decisions and Final Orders, and Writs. All notices and orders issued by the Adjudication Officer shall be served in accordance with Section 6 of this Rule.
c. Service On Counsel. If a party is represented by a lawyer, an Entry of Appearance shall be submitted and the service of position paper, pleadings as well as notices, orders, decision and other processes of the Adjudication Officer shall be made upon said counsel.""",
 ('IV',11):"""Section 11. Prohibited Pleadings and Motions. For purposes of these Rules, the following pleadings and motions shall not be allowed and acted upon:
a. Motions to Dismiss, except motion to dismiss based on lack of jurisdiction over the subject matter, res judicata, prescription and forum shopping, which should be raised at the earliest possible opportunity;
b. Motion for Judgment on the Pleadings;
c. Motion for Summary Judgment;
d. Motion for Extension to file any required pleading;
e. Counter-claim;
f. Cross-claim;
g. Reply;
h. Rejoinder; and
i. Motion to Intervene""",
}

def correct(row):
    key=(row['rule'],row['section']);text=row['candidate_text'];changes=[]
    if key in OVERRIDES:
        text=OVERRIDES[key];changes.append('Restored list labels/missing text and removed OCR debris by page-image comparison')
    if key==('II',3):
        text=text.replace('concemed','concerned').replace('issued pursuant to\n\nIn the event','issued pursuant to\nSection 3, Rule III hereof.\n\nIn the event')
        text=text.replace('Rule Ill hereof.','Rule III hereof.')
        changes.append('Restored omitted cross-reference visible on PDF page 3; corrected rn/l OCR glyphs')
    if key==('III',5):
        text=re.sub(r'\s+Co\s*$','',text);changes.append('Removed trailing OCR debris')
    if key==('III',6):
        text=text.replace('$2006','S2006').replace("CFA'if",'CFA if')
        text=text.replace('\n\nWhen no settlement','\n\nb. When no settlement').replace('\n\nMediation is terminated','\n\nb. Mediation is terminated')
        changes.append('Restored subsection b labels and corrected source-series glyph')
    if key==('IV',1):
        start=text.index('1.1 Essential Requirements.');end=text.index('1.2. Formal Requirements.')
        text=text[:start]+"""1.1 Essential Requirements. All formal complaints shall be duly verified, dated and signed, and shall set forth/attach the following:
a. Names and addresses of the parties;
b. An allegation that the complaint went through mediation process pursuant to Rule 3 hereof and the same was certified for adjudication.
c. Concise statement of material facts and circumstances constituting the cause/s of action, including the date, time and place of commission of the act/s or omission/s complained of;
d. Certificate to File Action, Sworn statements of witnesses and/or object or documentary evidence, if any;
e. The reliefs prayed for, and the preliminary or preventive measure/s sought, if any; and
f. A certification of non-forum shopping.

"""+text[end:]
        changes.append('Reattached essential-requirement list labels using PDF pages 5-6')
    if key==('IV',5):
        text=text.replace('Rule Ill,','Rule III,');changes.append('Corrected Roman numeral OCR glyph')
    if key==('IV',6):
        text=text.replace('retum  receipt','return receipt');changes.append('Corrected rn/m OCR glyph')
    if key==('V',1):
        text=text.replace('$2013','S2013');changes.append('Corrected source-series OCR glyph')
    if key==('V',3):
        text=text.split('\n\nIssued this')[0].strip();changes.append('Separated issuance/signature block from effectivity provision')
    return text,changes

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    a.output_dir=a.output_dir.resolve()
    if a.output_dir.exists():raise ValueError('Use a new version')
    source=ROOT/'outputs/pre-item12-repair-2026-10-17/source-repairs/dti_structure_repairs.jsonl'
    records=[json.loads(l) for l in source.read_text(encoding='utf-8').splitlines()]
    a.output_dir.mkdir(parents=True);images=a.output_dir/'page_images';images.mkdir()
    for page in range(1,12):
        original=ROOT/f'tmp/pdfs/pre-item12/dti20-{page:02d}.png'
        shutil.copy2(original,images/original.name)
    result=[]
    raw=ROOT/'dataset/canonical_sources/raw/consumer/regulations/dao_20_02_mediation_adjudication.pdf'
    for r in records:
        text,changes=correct(r)
        evidence={str((images/f'dti20-{page:02d}.png').relative_to(ROOT)).replace('\\','/'):
                  sha(images/f'dti20-{page:02d}.png')
                  for page in range(r['pdf_page_start'],r['pdf_page_end']+1)}
        result.append({**r,'document_id':'DTI_DAO_20_02',
            'provision_id':f"DTI_DAO_20_02__rule_{r['rule'].lower()}__section_{r['section']}",
            'citation_display':f"DTI DAO 20-02, Rule {r['rule']}, Section {r['section']}",
            'normalized_text':text,'corrections':changes,'review_status':'ai_visual_compared',
            'review_actor':'Codex','reviewed_at':'2026-10-17','independent_human_review':False,
            'legal_professional_review':False,'human_review_required':True,
            'answer_eligible':False,'official_pdf_sha256':sha(raw),'page_image_sha256':evidence})
    assert len(result)==29 and len({r['provision_id'] for r in result})==29
    (a.output_dir/'provisions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result),encoding='utf-8')
    manifest={'status':'AI page-image comparison complete; required independent review remains pending',
        'provisions':29,'pages_compared':11,'changed_provisions':sum(bool(r['corrections']) for r in result),
        'parent_candidate_sha256':sha(source),'original_canonical_modified':False,
        'human_reviews_completed':0,'default_index_modified':False,'answer_generation_allowed':False}
    (a.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (a.output_dir/'checksums.json').write_text(json.dumps({str(f.relative_to(a.output_dir)).replace('\\','/'):sha(f)
        for f in a.output_dir.rglob('*') if f.is_file()},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest))
if __name__=='__main__':main()
