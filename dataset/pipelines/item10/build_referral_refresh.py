"""Field-level AI official-source review; preserve frozen directory and uncertainty."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
EVIDENCE={
 'REF_DOLE_ARMS':('https://arms.dole.gov.ph/',{'portal_url':'https://arms.dole.gov.ph/'},'Official portal describes filing and tracking RFAs; phone not reverified on this page.'),
 'REF_DTI_CARE':('https://fairtrade.dti.gov.ph/faq/how-to-file-a-consumer-complaint/',{'portal_url':'https://consumercare.dti.gov.ph/','email':'consumercare@dti.gov.ph','phone':'(02) 7215 1165','office_address':'5th Floor, Trade and Industry Building, 361 Sen. Gil J. Puyat Ave., 1200 Makati City'},'Phone is the FTEB general office number. Filing guidance on this page expressly addresses Metro Manila; regional offices may differ.'),
 'REF_PAO':('https://pao.gov.ph/contact-us/',{'phone':'(02) 8929-9436 local 106/107 (office hours); local 159 (outside office hours)','office_address':'4th & 5th Floors, DOJ Agencies Building, NIA Road corner East Avenue, Diliman, Quezon City'},'Email is masked in retrieved official content; it has not been reverified. Qualification for PAO assistance remains conditional.'),
 'REF_DMW':('https://dmw.gov.ph/contact-us',{'portal_url':'https://dmw.gov.ph/contact-us','email':'info@dmw.gov.ph','phone':'1348','office_address':'BFO Building, Ortigas Avenue corner EDSA, Mandaluyong City 1550'},'1348 is labeled an emergency hotline by DMW; do not present it as an online filing portal.'),
 'REF_MARINA_STCW':('https://marina.gov.ph/marina-directory/',{'phone':'(02) 8240-9950 extension 2','office_address':'3rd Floor, MARINA Building, Bonifacio Drive corner 20th Street, Port Area, Manila'},'Certification Division contact only. Do not use for seafarer wage complaints. Masked email is not reverified.'),
 'REF_CSC_CCB':('https://csc.gov.ph/programs/ccb',{'portal_url':'https://www.contactcenterngbayan.gov.ph/','phone':'CSC hotline: 8932-0111; SMS: 0908-8816565'},'Government frontline-service feedback; this is not confirmation that CCB adjudicates government employment/pay disputes. Email is masked.'),
 'REF_ECC':('https://ecc.gov.ph/directory/',{'phone':'(02) 8899-4251 local 239','office_address':'4th & 5th Floors, ECC Building, 355 Sen. Gil Puyat Avenue, 1209 Makati City'},'Public Assistance Center number. Masked email is not reverified.'),
 'REF_OSHC':('https://oshc.dole.gov.ph/contact-us-2/',{'email':'oed@oshc.dole.gov.ph','phone':'(02) 8929-6036; (02) 8929-6030','office_address':'North Avenue corner Sen. Miriam P. Defensor-Santiago Avenue, Diliman, Quezon City 1105'},'Official contact page checked; another official page mentions temporary trunkline disruption, so email is preferable if calls fail.'),
 'REF_SSS':('https://www.sss.gov.ph/usssaptayo-portal/',{'email':'usssaptayo@sss.gov.ph','phone':'1455','office_address':'SSS Building, East Avenue, Diliman, Quezon City'},'Official uSSSap Tayo information page confirms these channels.'),
 'REF_NWPC':('https://nwpc.dole.gov.ph/connect-with-us/',{'portal_url':'https://nwpc.dole.gov.ph/connect-with-us/'},'Use the official RTWPB directory for regional wage enquiries; this does not add current regional wage amounts to the model.'),
 'REF_BSP_CAM':('https://www.bsp.gov.ph/Pages/Forms/DispForm.aspx?ID=1870',{'email':'consumeraffairs@bsp.gov.ph','phone':'(02) 5306-2584'},'Official indexed BSP-CAM content corroborates channels. Concerns should first be raised with the supervised institution.'),
 'REF_SEC_IMESSAGE':('https://www.sec.gov.ph/lending-companies-and-financing-companies/complaints/',{'portal_url':'https://imessage.sec.gov.ph/'},'SEC explicitly identifies iMessage for financing/lending complaints; its official contact directory also identifies iMessage for EIPD matters.'),
 'REF_INSURANCE_COMMISSION':('https://site.insurance.gov.ph/contact-us/',{'email':'publicassistance@insurance.gov.ph','phone':'(02) 8523-8461 local 103/127; Globe 0917 116-0007; Smart 0999 993-0637','office_address':'1071 United Nations Avenue, Ermita, Manila 1000'},'Replaces reliance on the BSP cross-agency directory with the Insurance Commission own page.'),
 'REF_NPC':('https://privacy.gov.ph/contactus/',{'portal_url':'https://privacy.gov.ph/file-a-complaint/','phone':'(02) 5322-1322 local 114 or 115; Smart 0970 818 0555; Globe 0905 506 1478','office_address':'25th-27th Floors, The Upper Class Tower, Quezon Avenue corner Scout Reyes Street, Quezon City'},'Complaint phone verified. Email remains masked; formal filing requirements are separate from contact verification.'),
 'REF_NTC':('https://www.ntc.gov.ph/wp-content/uploads/2025/CITIZENS_CHARTER/7-FEEDBACK-03282025.pdf',{},'Official 2025 charter located, but consumer-service channels are not sufficiently reverified. Do not turn an administrative-feedback email into a telecom complaint filing address.'),
 'REF_HSAC_DHSUD':('https://hsac.gov.ph/wp-content/uploads/1-Citizens-Charter-2025_1st-Edition_final.pdf',{},'Newer official charter identifies info@hsac.gov.ph as ARTA Lead feedback. This is not proof of a housing-case filing email; old complaint@hsac.gov.ph is withheld.'),
 'REF_LTFRB':('https://www.ltfrb.gov.ph/wp-content/uploads/2024/11/Fare-Guide_Traditional-PUJ-Provisional-Fare-Increase_08Oct2023.pdf',{},'Official historical guide corroborates hotline 1342, but it has not been confirmed for October 2026. Do not renew verification from an old fare guide.'),
 'REF_ERC':('https://erc.gov.ph/ERC-Offices',{'portal_url':'https://ccts.erc.ph','phone':'(02) 8689-5372 local 5345, 5577, 5398 or 5397','office_address':'Exquadra Tower, 1 Jade Drive, Ortigas Center, Brgy. San Antonio, Pasig City 1605'},'Official ERC directory links this online filing system. Email is masked and remains unverified.'),
 'REF_PNP_ACG':('https://batanesppo.pro2.pnp.gov.ph/cybersecurity-advisory/',{},'Official 2026 PNP advisory corroborates reporting to the nearest ACG or eGov app. No national contact phone/email or functional national ACG portal was confirmed.'),
}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    out=a.output_dir.resolve()
    if out.exists():raise ValueError('Use a new refresh version')
    source=ROOT/'dataset/processed/item10/reviewed_v1.0.0/referral_directory.csv'
    with source.open(encoding='utf-8-sig',newline='') as f:original=list(csv.DictReader(f))
    assert {r['referral_id'] for r in original}==set(EVIDENCE)
    records=[]
    for r in original:
        url,fields,note=EVIDENCE[r['referral_id']]
        field_evidence={k:{'verified_on':'2026-10-17','evidence_url':url} for k in fields}
        if r['referral_id']=='REF_NPC':
            field_evidence['portal_url']['evidence_url']='https://privacy.gov.ph/file-a-complaint/'
        records.append({'referral_id':r['referral_id'],'agency':r['agency'],'service':r['service'],
            'original_record':r,'checked_on':'2026-10-17','review_actor':'Codex','review_origin':'AI review of official web pages/indexed official content',
            'verification_source_url':url,'confirmed_fields':fields,
            'field_verification':field_evidence,
            'unverified_fields_withheld':[k for k in ['portal_url','email','phone','office_address'] if k not in fields],
            'complete_contact_verification':len(fields)==4,'note':note,
            'jurisdiction_or_filing_requirements_certified':False,'deployment_allowed':False})
    out.mkdir(parents=True)
    (out/'directory.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'records':len(records),'records_with_confirmed_fields':sum(bool(r['confirmed_fields']) for r in records),
        'records_without_confirmed_operational_fields':[r['referral_id'] for r in records if not r['confirmed_fields']],
        'confirmed_field_count':sum(len(r['confirmed_fields']) for r in records),
        'frozen_directory_modified':False,'all_contacts_verified':False,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'default_classifier_directory_replaced':False,'human_or_legal_approval_supplied':False}
    (out/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))
if __name__=='__main__':main()
