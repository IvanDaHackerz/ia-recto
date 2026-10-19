"""Deterministic referral candidates from known scope topics and the registry."""
from __future__ import annotations
import csv,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
TOPIC_REFERRALS={
 'labor.ofw':['REF_DMW'],'labor.seafarers':['REF_DMW','REF_PAO'],
 'labor.government_employment':['REF_CSC_CCB'],'labor.kasambahay':['REF_DOLE_ARMS'],
 'labor.union_cba':['REF_DOLE_ARMS'],'labor.workers_compensation':['REF_ECC'],
 'labor.occupational_safety':['REF_OSHC'],'labor.retirement_pension':['REF_SSS'],
 'labor.pending_case':['REF_PAO'],'labor.case_outcome_prediction':['REF_PAO'],
 'labor.regional_minimum_wage_amounts':['REF_NWPC'],
 'consumer.insurance':['REF_INSURANCE_COMMISSION'],'consumer.investments':['REF_SEC_IMESSAGE'],
 'consumer.telecommunications':['REF_NTC'],'consumer.data_privacy':['REF_NPC'],
 'consumer.medical_malpractice':['REF_PAO'],'consumer.real_estate':['REF_HSAC_DHSUD'],
 'consumer.utility_billing':['REF_ERC'],'consumer.criminal_online_fraud':['REF_PNP_ACG']}

def select_referrals(components):
    with (ROOT/'dataset/processed/item10/reviewed_v1.0.0/referral_directory.csv').open(encoding='utf-8-sig',newline='') as f:
        directory={r['referral_id']:r for r in csv.DictReader(f)}
    choices={}
    for c in components:
        if c['category']!='excluded':continue
        topic=c.get('constraint');text=c['text'].lower()
        ids=TOPIC_REFERRALS.get(topic,[])
        if topic=='consumer.banking_credit':
            # Lending-company and bank/e-wallet concerns have different agencies.
            if re.search(r'\b(?:bank\w*|credit.card|e.wallet)\b',text):ids=['REF_BSP_CAM']
            elif re.search(r'\b(?:lending|financing|loan.company)\b',text):ids=['REF_SEC_IMESSAGE']
        if topic=='consumer.transportation' and re.search(r'\b(?:bus|public.transport|transport.operator)\b',text):
            ids=['REF_LTFRB']
        for rid in ids:
            r=directory[rid]
            choices[rid]={'referral_id':rid,'agency':r['agency'],'service':r['service'],
                'portal_url':r['portal_url'],'information_url':r['information_url'],
                'topic':topic,'selection_source':'explicit_scope_topic_rule',
                'last_contact_verification':r['last_verified'],'requires_contact_refresh':True,
                'candidate_only':True}
    return list(choices.values())
