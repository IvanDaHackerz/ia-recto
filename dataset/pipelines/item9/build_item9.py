#!/usr/bin/env python3
"""Build the Item 9 classifier seed set and versioned referral directory."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


STATUS_DATE = "2026-09-29"
DATASET_VERSION = "1.0.0"


SCENARIOS: dict[str, list[str]] = {
    "labor.wages_payment": [
        "my private employer has not paid my wages for two weeks",
        "my employer deducted money from my pay without explaining why",
        "the company pays us only once every six weeks",
        "my payslip shows a wage amount different from what I received",
    ],
    "labor.hours_of_work": [
        "I regularly work ten-hour shifts",
        "my employer does not give us a meal break during an eight-hour shift",
        "I must stay at the workplace while waiting for customers",
        "the company changed us to a compressed workweek",
    ],
    "labor.rest_days": [
        "I work seven days every week without a rest day",
        "my employer requires me to work on my scheduled rest day",
        "the company keeps changing my weekly rest day without notice",
        "I was not given any day off for several weeks",
    ],
    "labor.overtime_pay": [
        "I work beyond eight hours but receive no overtime pay",
        "my supervisor requires overtime but calls it voluntary",
        "I do not understand how my overtime pay should be computed",
        "the company offsets my overtime with earlier undertime",
    ],
    "labor.holiday_premium_pay": [
        "I worked on a regular holiday but received only my normal wage",
        "I worked on a special non-working day and received no premium",
        "a holiday fell on my rest day and I was required to work",
        "my employer says monthly-paid workers never receive holiday pay",
    ],
    "labor.thirteenth_month_pay": [
        "my employer did not give me thirteenth-month pay",
        "I resigned before December and want to know if I still qualify for thirteenth-month pay",
        "the company plans to release thirteenth-month pay after the usual deadline",
        "my employer excluded part of my basic salary from the thirteenth-month computation",
    ],
    "labor.employment_contracts": [
        "I started work without receiving a written employment contract",
        "my fixed-term contract keeps getting renewed for the same regular work",
        "my probationary contract does not state the standards for regularization",
        "my employer changed important contract terms after I started",
    ],
    "labor.termination_due_process": [
        "I was dismissed without written notice or a chance to explain",
        "the company says my position is redundant but gave no details",
        "I was accused of misconduct and immediately terminated without a hearing",
        "my employer made conditions unbearable so I felt forced to resign",
    ],
    "labor.final_pay_coe": [
        "my former employer has delayed my final pay",
        "my previous company refuses to issue a certificate of employment",
        "the employer will not release my final pay until an indefinite clearance process is finished",
        "unexpected deductions were taken from my final pay",
    ],
    "labor.complaint_referral": [
        "I need to know where to file a basic private employment complaint",
        "I want to request assistance through SEnA",
        "I need to know what records to prepare before asking DOLE for help",
        "I want to know whether a labor concern can first go through conciliation",
    ],
    "consumer.general_framework": [
        "a store refuses to explain my basic consumer rights",
        "I want to know whether the Consumer Act covers my purchase",
        "a business says consumer-protection rules do not apply to its service",
        "I need to understand the basic duties of a seller toward consumers",
    ],
    "consumer.defective_products": [
        "a newly purchased appliance stopped working after two days",
        "a toy I bought has a dangerous manufacturing defect",
        "a sealed food product was spoiled when I opened it",
        "the replacement product has the same defect as the first one",
    ],
    "consumer.warranties": [
        "the seller refuses to honor the written warranty",
        "the shop rejected my warranty claim because I lost the original receipt",
        "the service center shortened the warranty period shown on the product",
        "the seller says only the manufacturer is responsible for the warranty",
    ],
    "consumer.repair_replace_refund": [
        "the seller repaired the defective product several times but it still fails",
        "the store refuses replacement for an item that was defective on delivery",
        "a shop uses a no-refund policy for every defective product",
        "I want to know when repair, replacement, or refund may be requested",
    ],
    "consumer.deceptive_unfair_sales": [
        "the seller added hidden charges after I agreed to buy",
        "a store advertised one product but pressured me to buy a more expensive one",
        "the salesperson concealed an important defect before the sale",
        "a business advertised a fake discount based on an invented original price",
    ],
    "consumer.misleading_advertising": [
        "an advertisement made claims that the actual product cannot meet",
        "an online advertisement omitted a required charge until checkout",
        "the product delivered is materially different from the promotional advertisement",
        "a sales promotion used misleading conditions that were not clearly disclosed",
    ],
    "consumer.price_tags": [
        "the cashier charged more than the price displayed on the shelf",
        "products in the store have no visible price tags",
        "the business displays one cash price and a higher card price without explanation",
        "the cashier did not give me the correct change",
    ],
    "consumer.product_safety": [
        "a product appears unsafe and has no warning label",
        "I was injured while using a consumer product as instructed",
        "a recalled product is still being sold in a local shop",
        "a children's product has small dangerous parts but no safety warning",
    ],
    "consumer.service_complaints": [
        "a repair shop damaged my item instead of fixing it",
        "I paid for a service that the business never provided",
        "a service provider refuses to correct clearly defective work",
        "a prepaid service was cancelled by the business without returning my payment",
    ],
    "consumer.online_transactions": [
        "an online seller sent an item different from the listing",
        "an online merchant does not disclose its business identity or contact details",
        "a marketplace seller refuses to address a defective delivered product",
        "an online platform will not explain the complaint process for my purchase",
    ],
    "consumer.complaint_referral": [
        "I need to know how to file a consumer complaint with DTI",
        "I want to know what documents are needed for a DTI consumer complaint",
        "I need help understanding DTI consumer mediation",
        "the seller ignored my complaint and I want to know the next government office to contact",
    ],
    "labor.regional_minimum_wage_amounts": [
        "I need the exact current minimum wage for my city and industry",
        "I want the latest regional wage-order amount",
        "I need a peso-by-peso minimum wage computation for my province",
        "I want to know whether a newly issued wage order already applies to my workplace",
    ],
    "labor.ofw": [
        "my overseas employer withheld my salary and passport",
        "my recruitment agency charged me unexpected deployment fees",
        "I was dismissed while working abroad",
        "my family needs help repatriating an overseas Filipino worker",
    ],
    "labor.seafarers": [
        "my seafarer employment contract has a dispute about onboard pay",
        "I need help with a MARINA seafarer certificate",
        "a shipping company disputes my sea-service record",
        "I have a complaint involving a seafarer's overseas deployment",
    ],
    "labor.government_employment": [
        "I am a government employee challenging an administrative penalty",
        "a public office denied my civil-service promotion",
        "I work for a government agency and dispute my salary grade",
        "I want to complain about unfair treatment in a government position",
    ],
    "labor.kasambahay": [
        "I am a kasambahay whose employer keeps my wages",
        "my household employer will not give me a weekly rest day",
        "I need help with a domestic worker employment agreement",
        "a kasambahay was dismissed without receiving earned pay",
    ],
    "labor.union_cba": [
        "our union disputes the conduct of a certification election",
        "management and the union disagree over a collective bargaining provision",
        "union members challenge the bargaining representative",
        "we need advice about a complex CBA deadlock",
    ],
    "labor.workers_compensation": [
        "I need an employees' compensation disability computation",
        "my occupational disease claim was denied",
        "I want to appeal an employees' compensation benefit decision",
        "I need to know whether a workplace injury qualifies for EC benefits",
    ],
    "labor.occupational_safety": [
        "my workplace lacks required safety equipment",
        "employees are exposed to dangerous chemicals without protection",
        "I want a technical occupational-safety inspection",
        "the employer has no workplace safety officer",
    ],
    "labor.retirement_pension": [
        "I need an exact SSS retirement pension computation",
        "my pension contribution record is incomplete",
        "I want to dispute the amount of my retirement benefit",
        "I need help deciding between pension benefit options",
    ],
    "labor.pending_case": [
        "I need advice about a labor case already pending before a tribunal",
        "my NLRC case has an upcoming hearing",
        "I want someone to prepare arguments for my pending dismissal case",
        "I need an interpretation of an order issued in my ongoing case",
    ],
    "labor.case_outcome_prediction": [
        "I want to know whether I will definitely win my labor case",
        "I need a percentage prediction of success in an illegal-dismissal complaint",
        "I want the system to decide who will win my employment dispute",
        "I need a guaranteed prediction before filing a case",
    ],
    "consumer.banking_credit": [
        "my bank charged an unauthorized credit-card transaction",
        "I dispute interest and fees on a bank loan",
        "an online lending company uses abusive collection practices",
        "my bank ignored my complaint about an electronic transfer",
    ],
    "consumer.insurance": [
        "my insurance company denied my claim",
        "I dispute the benefits under a life-insurance policy",
        "an HMO refuses to cover a medical expense",
        "I want to complain about an insurance broker",
    ],
    "consumer.investments": [
        "I lost money in an investment scheme promising guaranteed returns",
        "a company sold me an unregistered investment product",
        "I want to report a suspected securities scam",
        "an online platform refuses to return my investment funds",
    ],
    "consumer.telecommunications": [
        "my mobile provider keeps billing me for a cancelled plan",
        "an internet provider gives consistently poor service",
        "I receive unwanted telecommunications charges",
        "I need to complain about a lost phone or SIM being used",
    ],
    "consumer.data_privacy": [
        "a company disclosed my personal information without permission",
        "an online seller posted my identification documents publicly",
        "I want to report a personal-data breach",
        "a business refuses to delete personal information it no longer needs",
    ],
    "consumer.medical_malpractice": [
        "I believe a doctor committed medical malpractice",
        "a hospital procedure caused an injury and I want damages",
        "I want to file a professional complaint against a physician",
        "I need an assessment of negligent medical treatment",
    ],
    "consumer.real_estate": [
        "a subdivision developer failed to deliver the promised property",
        "I have a condominium turnover dispute",
        "a real-estate developer changed the approved project plan",
        "I want to file a housing adjudication complaint",
    ],
    "consumer.transportation": [
        "a public transport operator charged an improper fare",
        "I want to complain about a ride-hailing franchise issue",
        "a bus operator violated passenger-service rules",
        "I need a regulatory complaint against a transport operator",
    ],
    "consumer.utility_billing": [
        "my electricity bill contains an unexplained charge",
        "a water utility disconnected service despite a disputed bill",
        "I want to challenge a utility rate computation",
        "the electric distribution company ignored my billing complaint",
    ],
    "consumer.criminal_online_fraud": [
        "an online scammer stole money through a fake store",
        "I sent money to a fraudulent social-media account",
        "someone used phishing to take over my online account",
        "I need to report an online transaction that appears to be criminal fraud",
    ],
}


REFERRALS: list[dict[str, str]] = [
    {"referral_id":"REF_DOLE_ARMS","agency":"Department of Labor and Employment","service":"DOLE Assistance for Request Management System / SEnA","topic_ids":"labor.complaint_referral|labor.kasambahay|labor.union_cba","when_to_use":"Private-sector labor requests for assistance and excluded labor categories accepted by SEnA.","first_step":"File or track a Request for Assistance through DOLE ARMS, or call DOLE Hotline 1349.","portal_url":"https://arms.dole.gov.ph/","information_url":"https://dole.gov.ph/news/dole-digitization-expands-access-to-labor-services-nationwide/","email":"","phone":"1349","office_address":"","verification_source_url":"https://arms.dole.gov.ph/","verification_status":"verified_current_portal","last_verified":STATUS_DATE},
    {"referral_id":"REF_DTI_CARE","agency":"Department of Trade and Industry","service":"Consumer Complaints Assistance and Resolution System","topic_ids":"consumer.complaint_referral|consumer.service_complaints","when_to_use":"Ordinary consumer-product, service, and online-transaction complaints within DTI jurisdiction.","first_step":"Use the DTI CARe portal or contact ConsumerCare before escalation.","portal_url":"https://consumercare.dti.gov.ph/","information_url":"https://fairtrade.dti.gov.ph/faq/how-to-file-a-consumer-complaint/","email":"consumercare@dti.gov.ph","phone":"1-DTI (1-384)","office_address":"DTI Fair Trade Enforcement Bureau, 361 Sen. Gil J. Puyat Ave., Makati City","verification_source_url":"https://fairtrade.dti.gov.ph/faq/how-to-file-a-consumer-complaint/","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_PAO","agency":"Public Attorney's Office","service":"Legal counselling and assistance for qualified clients","topic_ids":"labor.pending_case|labor.case_outcome_prediction|consumer.medical_malpractice","when_to_use":"A question needs individualized legal advice, representation, case strategy, or another remedy outside the information system.","first_step":"Review PAO qualification and regional contact information, then contact the appropriate PAO office.","portal_url":"https://pao.gov.ph/contact-us/","information_url":"https://pao.gov.ph/transparency/mission-and-vision/","email":"pao_executive@yahoo.com","phone":"(02) 8929-9436 local 106/107","office_address":"DOJ Agencies Building, NIA Road corner East Avenue, Diliman, Quezon City","verification_source_url":"https://pao.gov.ph/contact-us/","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_DMW","agency":"Department of Migrant Workers","service":"OFW information and assistance","topic_ids":"labor.ofw","when_to_use":"Overseas Filipino worker employment, recruitment, welfare, or repatriation concerns.","first_step":"Contact the DMW hotline or the appropriate Migrant Workers Office.","portal_url":"https://dmw.gov.ph/contact-us","information_url":"https://dmw.gov.ph/contact-us","email":"info@dmw.gov.ph","phone":"1348","office_address":"Blas F. Ople Building, Ortigas Avenue corner EDSA, Mandaluyong City","verification_source_url":"https://dmw.gov.ph/contact-us","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_MARINA_STCW","agency":"Maritime Industry Authority","service":"MARINA STCW Administration Office","topic_ids":"labor.seafarers","when_to_use":"Seafarer certification, training, STCW, and maritime professional concerns.","first_step":"Contact the MARINA STCW Administration Office; overseas employment concerns may also require DMW.","portal_url":"https://stcw.marina.gov.ph/contact-us/","information_url":"https://stcw.marina.gov.ph/contact-us/","email":"stcw_cert@marina.gov.ph","phone":"(02) 8240-9950","office_address":"MARINA Building, Bonifacio Drive corner 20th Street, Port Area, Manila","verification_source_url":"https://stcw.marina.gov.ph/contact-us/","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_CSC_CCB","agency":"Civil Service Commission","service":"Contact Center ng Bayan","topic_ids":"labor.government_employment","when_to_use":"Government employment and public-service concerns outside private-sector labor scope.","first_step":"Use Contact Center ng Bayan or contact the appropriate CSC regional office.","portal_url":"https://contactcenterngbayan.gov.ph/","information_url":"https://csc.gov.ph/programs/ccb","email":"email@contactcenterngbayan.gov.ph","phone":"(02) 8932-0111; SMS 0908-881-6565","office_address":"","verification_source_url":"https://csc.gov.ph/programs/ccb","verification_status":"verified_official_service_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_ECC","agency":"Employees' Compensation Commission","service":"Employees' Compensation Program public assistance","topic_ids":"labor.workers_compensation","when_to_use":"Employees' compensation, occupational disease, work-injury benefit, disability, and appeal concerns.","first_step":"Contact the ECC Public Assistance Center or the appropriate regional extension unit.","portal_url":"https://ecc.gov.ph/contact-us/","information_url":"https://ecc.gov.ph/directory/","email":"info@ecc.gov.ph","phone":"(02) 8899-4251 local 239","office_address":"ECC Building, 355 Sen. Gil J. Puyat Ave., Makati City","verification_source_url":"https://ecc.gov.ph/directory/","verification_status":"verified_official_directory","last_verified":STATUS_DATE},
    {"referral_id":"REF_OSHC","agency":"Occupational Safety and Health Center","service":"Occupational safety and health information","topic_ids":"labor.occupational_safety","when_to_use":"Technical workplace-safety, health, training, or exposure concerns outside the MVP.","first_step":"Contact OSHC or the relevant regional extension unit.","portal_url":"https://oshc.dole.gov.ph/contact-us-2/","information_url":"https://oshc.dole.gov.ph/contact-us-2/","email":"oed@oshc.dole.gov.ph","phone":"(02) 8929-6036; (02) 8929-6030","office_address":"North Avenue corner Sen. Miriam P. Defensor-Santiago Avenue, Diliman, Quezon City","verification_source_url":"https://oshc.dole.gov.ph/contact-us-2/","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_SSS","agency":"Social Security System","service":"SSS member assistance","topic_ids":"labor.retirement_pension","when_to_use":"Private-sector social-security contribution, retirement, pension, and benefit questions.","first_step":"Use My.SSS or contact the SSS hotline for member-specific records and computations.","portal_url":"https://www.sss.gov.ph/contact-us/","information_url":"https://www.sss.gov.ph/contact-us/","email":"usssaptayo@sss.gov.ph","phone":"1455","office_address":"SSS Main Building, East Avenue, Diliman, Quezon City","verification_source_url":"https://www.sss.gov.ph/contact-us/","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_NWPC","agency":"National Wages and Productivity Commission","service":"Current regional wage information","topic_ids":"labor.regional_minimum_wage_amounts","when_to_use":"Exact current regional wage rates and wage-order coverage.","first_step":"Check the current wage order and regional wage-board information on the NWPC website.","portal_url":"https://nwpc.dole.gov.ph/","information_url":"https://nwpc.dole.gov.ph/","email":"","phone":"","office_address":"","verification_source_url":"https://nwpc.dole.gov.ph/","verification_status":"official_domain_only_contact_not_recorded","last_verified":STATUS_DATE},
    {"referral_id":"REF_BSP_CAM","agency":"Bangko Sentral ng Pilipinas","service":"BSP Consumer Assistance Mechanism","topic_ids":"consumer.banking_credit","when_to_use":"Unresolved complaints involving BSP-supervised banks, e-money issuers, payment systems, and other supervised institutions.","first_step":"Complain first to the financial institution, then escalate through BSP Online Buddy or the BSP consumer-assistance channel.","portal_url":"https://www.bsp.gov.ph/","information_url":"https://www.bsp.gov.ph/Pages/Forms/DispForm.aspx?ID=1870","email":"consumeraffairs@bsp.gov.ph","phone":"(02) 5306-2584","office_address":"BSP Complex, A. Mabini Street, Malate, Manila","verification_source_url":"https://www.bsp.gov.ph/Pages/Forms/DispForm.aspx?ID=1870","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_SEC_IMESSAGE","agency":"Securities and Exchange Commission","service":"SEC iMessage complaints","topic_ids":"consumer.investments|consumer.banking_credit","when_to_use":"Investment scams and complaints involving registered or unauthorized lending and financing companies.","first_step":"Use SEC iMessage; the applicable SEC department depends on whether the concern involves lending, financing, or investments.","portal_url":"https://imessage.sec.gov.ph/","information_url":"https://www.sec.gov.ph/lending-companies-and-financing-companies/complaints/","email":"","phone":"","office_address":"","verification_source_url":"https://www.sec.gov.ph/lending-companies-and-financing-companies/complaints/","verification_status":"verified_current_portal","last_verified":STATUS_DATE},
    {"referral_id":"REF_INSURANCE_COMMISSION","agency":"Insurance Commission","service":"Public Assistance and Mediation Division","topic_ids":"consumer.insurance","when_to_use":"Insurance, pre-need, HMO, mutual-benefit, and insurance-broker complaints.","first_step":"Contact the Insurance Commission Public Assistance and Mediation Division.","portal_url":"https://www.insurance.gov.ph/","information_url":"https://www.bsp.gov.ph/Pages/InclusiveFinance/PYMContacts.aspx","email":"publicassistance@insurance.gov.ph","phone":"(02) 8523-8461 local 103 or 127","office_address":"","verification_source_url":"https://www.bsp.gov.ph/Pages/InclusiveFinance/PYMContacts.aspx","verification_status":"contact_corroborated_on_official_bsp_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_NPC","agency":"National Privacy Commission","service":"Privacy complaint filing","topic_ids":"consumer.data_privacy","when_to_use":"Misuse, disclosure, breach, or improper processing of personal information.","first_step":"Review the NPC complaint requirements and use the current complaint-assisted form.","portal_url":"https://privacy.gov.ph/file-a-complaint/","information_url":"https://privacy.gov.ph/file-a-complaint-2/","email":"complaints@privacy.gov.ph","phone":"(02) 5322-1322 local 114 or 115","office_address":"25th-27th Floors, The Upper Class Tower, Quezon Ave. corner Scout Reyes St., Quezon City","verification_source_url":"https://privacy.gov.ph/contactus/","verification_status":"verified_current_contact_page","last_verified":STATUS_DATE},
    {"referral_id":"REF_NTC","agency":"National Telecommunications Commission","service":"Consumer Welfare and Protection complaints","topic_ids":"consumer.telecommunications","when_to_use":"Telecommunications billing, poor service, spam, SIM, and related subscriber complaints.","first_step":"Submit a written complaint to the NTC or the appropriate regional office.","portal_url":"https://www.edge.ntc.gov.ph/","information_url":"https://www.ntc.gov.ph/wp-content/uploads/2025/CITIZENS_CHARTER/7-FEEDBACK-03282025.pdf","email":"administrative@ntc.gov.ph","phone":"(02) 8924-4028; (02) 8924-4046","office_address":"Sen. Miriam P. Defensor-Santiago Ave., East Triangle, Diliman, Quezon City","verification_source_url":"https://www.ntc.gov.ph/wp-content/uploads/2025/CITIZENS_CHARTER/7-FEEDBACK-03282025.pdf","verification_status":"verified_official_citizens_charter","last_verified":STATUS_DATE},
    {"referral_id":"REF_HSAC_DHSUD","agency":"Human Settlements Adjudication Commission / DHSUD","service":"Housing and real-estate dispute referral","topic_ids":"consumer.real_estate","when_to_use":"Subdivision, condominium, developer, homeowner-association, and housing adjudication matters.","first_step":"Determine whether the concern is adjudicatory or administrative, then consult HSAC or the proper DHSUD regional office.","portal_url":"https://hsac.gov.ph/","information_url":"https://dhsud.gov.ph/","email":"complaint@hsac.gov.ph","phone":"","office_address":"","verification_source_url":"https://hsac.gov.ph/wp-content/uploads/Citizens-Charter-2021_ver5.3.pdf","verification_status":"verified_official_citizens_charter_contact_requires_recheck","last_verified":STATUS_DATE},
    {"referral_id":"REF_LTFRB","agency":"Land Transportation Franchising and Regulatory Board","service":"Public-transport regulatory referral","topic_ids":"consumer.transportation","when_to_use":"Public-transport fares, franchises, and operator-service concerns.","first_step":"Use the current contact or complaint channel shown on the LTFRB official website.","portal_url":"https://ltfrb.gov.ph/","information_url":"https://ltfrb.gov.ph/","email":"","phone":"","office_address":"","verification_source_url":"https://ltfrb.gov.ph/","verification_status":"official_domain_only_contact_not_verified","last_verified":STATUS_DATE},
    {"referral_id":"REF_ERC","agency":"Energy Regulatory Commission","service":"Electric-utility regulatory referral","topic_ids":"consumer.utility_billing","when_to_use":"Electricity billing, distribution-utility, and regulated-rate concerns. Other utilities may require a different regulator.","first_step":"Identify the utility type and use the current complaint channel on the appropriate regulator's official website.","portal_url":"https://www.erc.gov.ph/","information_url":"https://www.erc.gov.ph/","email":"","phone":"","office_address":"","verification_source_url":"https://www.erc.gov.ph/","verification_status":"official_domain_only_contact_not_verified","last_verified":STATUS_DATE},
    {"referral_id":"REF_PNP_ACG","agency":"Philippine National Police Anti-Cybercrime Group","service":"Cybercrime reporting referral","topic_ids":"consumer.criminal_online_fraud","when_to_use":"Online fraud, phishing, account takeover, and conduct requiring criminal investigation.","first_step":"Preserve transaction records and use the current reporting channel on the PNP Anti-Cybercrime Group official website; urgent threats should go to local law enforcement.","portal_url":"https://acg.pnp.gov.ph/","information_url":"https://acg.pnp.gov.ph/","email":"","phone":"","office_address":"","verification_source_url":"https://acg.pnp.gov.ph/","verification_status":"official_domain_only_contact_page_blocked_during_check","last_verified":STATUS_DATE},
]


TOPIC_REFERRALS: dict[str, list[str]] = {}
for referral in REFERRALS:
    for topic_id in referral["topic_ids"].split("|"):
        TOPIC_REFERRALS.setdefault(topic_id, []).append(referral["referral_id"])


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            cooked = dict(row)
            for field, value in cooked.items():
                if isinstance(value, list):
                    cooked[field] = "|".join(value)
            writer.writerow(cooked)


EXISTING_QUESTION_IDS: dict[tuple[str, str], str] = {}


def load_existing_question_ids(path: Path) -> dict[tuple[str, str], str]:
    """Reuse issued IDs so the five distributed review workbooks stay valid."""
    if not path.exists():
        return {}
    result: dict[tuple[str, str], str] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for existing in csv.DictReader(handle):
            key = (existing["scenario_group_id"], existing["question_text"])
            result[key] = existing["question_id"]
    return result


def qid(group_id: str, variant: int, text: str) -> str:
    existing = EXISTING_QUESTION_IDS.get((group_id, text))
    if existing:
        return existing
    readable_group = group_id.upper().replace(":", "_").replace(".", "_")
    return f"Q9_{readable_group}_{variant + 1}"


def single_split(group_index: int) -> str:
    position = group_index % 8
    return "train" if position < 6 else ("validation" if position == 6 else "test")


def referrals_for_excluded(topic_id: str, scenario: str) -> list[str]:
    if topic_id == "consumer.banking_credit":
        return ["REF_SEC_IMESSAGE"] if "lending company" in scenario else ["REF_BSP_CAM"]
    return TOPIC_REFERRALS.get(topic_id, ["REF_PAO"])


def row(group_id: str, variant: int, text: str, language: str, split: str,
        primary_label: str, scope_label: str, routing_action: str,
        supported: list[str], excluded: list[str], referrals: list[str]) -> dict[str, Any]:
    return {
        "question_id": qid(group_id, variant, text),
        "scenario_group_id": group_id,
        "question_text": text,
        "language_style": language,
        "primary_label": primary_label,
        "scope_label": scope_label,
        "routing_action": routing_action,
        "supported_topic_ids": supported,
        "excluded_topic_ids": excluded,
        "referral_ids": sorted(set(referrals)),
        "split": split,
        "origin": "synthetic_seed",
        "annotation_status": "machine_generated_needs_human_review",
        "human_reviewer": "",
        "review_notes": "",
        "dataset_version": DATASET_VERSION,
        "status_as_of": STATUS_DATE,
    }


def build_questions(topic_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    supported = [r for r in topic_rows if r["scope_status"] == "supported"]
    excluded = [r for r in topic_rows if r["scope_status"] == "excluded"]
    by_domain = {
        domain: [r["topic_id"] for r in supported if r["domain"] == domain]
        for domain in ("labor", "consumer")
    }

    for topic in supported:
        topic_id = topic["topic_id"]
        primary = topic["domain"]
        for scenario_index, scenario in enumerate(SCENARIOS[topic_id]):
            groups = [
                ("rights", f"What are my rights if {scenario}?", f"Allowed po ba ito: {scenario}?"),
                ("steps", f"What should I do if {scenario}?", f"Saan po ako puwedeng lumapit if {scenario}?"),
            ]
            for intent_index, (intent, english, taglish) in enumerate(groups):
                group_index = scenario_index * 2 + intent_index
                group_id = f"single:{topic_id}:{intent}:{scenario_index}"
                split = single_split(group_index)
                refs = ["REF_DOLE_ARMS"] if primary == "labor" else ["REF_DTI_CARE"]
                questions.append(row(group_id, 0, english, "en", split, primary, "fully_supported", "answer", [topic_id], [], refs))
                questions.append(row(group_id, 1, taglish, "en_tl", split, primary, "fully_supported", "answer", [topic_id], [], refs))

    for topic in excluded:
        topic_id = topic["topic_id"]
        for scenario_index, scenario in enumerate(SCENARIOS[topic_id]):
            refs = referrals_for_excluded(topic_id, scenario)
            for intent_index, intent in enumerate(("rights", "steps")):
                group_index = scenario_index * 2 + intent_index
                group_id = f"outside:{topic_id}:{intent}:{scenario_index}"
                split = single_split(group_index)
                if intent == "rights":
                    text = f"Can this service advise me if {scenario}?"
                    language = "en"
                else:
                    text = f"Saan po ako dapat lumapit if {scenario}?"
                    language = "en_tl"
                questions.append(row(group_id, 0, text, language, split, "out_of_scope", "unsupported", "decline_and_refer", [], [topic_id], refs))

    mixed_groups: list[tuple[str, str, str, list[str], list[str], list[str], str]] = []
    labor_topics = by_domain["labor"]
    consumer_topics = by_domain["consumer"]
    for index in range(21):
        labor_topic = labor_topics[index % len(labor_topics)]
        consumer_topic = consumer_topics[(index * 3) % len(consumer_topics)]
        a = SCENARIOS[labor_topic][index % 4]
        b = SCENARIOS[consumer_topic][(index + 1) % 4]
        mixed_groups.append((f"mixed:supported:{index}", a, b, [labor_topic, consumer_topic], [], ["REF_DOLE_ARMS", "REF_DTI_CARE"], "fully_supported"))
    for index in range(21):
        supported_topic = supported[index % len(supported)]["topic_id"]
        excluded_topic = excluded[(index * 5) % len(excluded)]["topic_id"]
        a = SCENARIOS[supported_topic][index % 4]
        b = SCENARIOS[excluded_topic][(index + 2) % 4]
        refs = (["REF_DOLE_ARMS"] if supported_topic.startswith("labor.") else ["REF_DTI_CARE"]) + referrals_for_excluded(excluded_topic, b)
        mixed_groups.append((f"mixed:partial:{index}", a, b, [supported_topic], [excluded_topic], refs, "partially_supported"))

    for index, (group_id, first, second, supported_ids, excluded_ids, refs, scope) in enumerate(mixed_groups):
        split_position = index % 6
        split = "train" if split_position < 4 else ("validation" if split_position == 4 else "test")
        routing = "answer_multiple_supported_domains" if scope == "fully_supported" else "partial_answer_and_refer"
        texts = [
            (f"I have two concerns: {first}. Also, {second}. Can you help with both?", "en"),
            (f"My question involves both issues: {first}; and {second}. What rules apply?", "en"),
            (f"Dalawa po ang concern ko: {first}. Tapos, {second}. Alin dito ang masasagot ninyo?", "en_tl"),
            (f"Which parts of this can you answer: {first}; {second}?", "en"),
        ]
        for variant, (text, language) in enumerate(texts):
            questions.append(row(group_id, variant, text, language, split, "mixed", scope, routing, supported_ids, excluded_ids, refs))

    return questions


def main() -> int:
    global EXISTING_QUESTION_IDS
    dataset_root = Path(__file__).resolve().parents[2]
    output = dataset_root / "processed" / "item9"
    output.mkdir(parents=True, exist_ok=True)
    EXISTING_QUESTION_IDS = load_existing_question_ids(output / "classifier_questions.csv")
    taxonomy_path = dataset_root / "data_contract" / "topic_taxonomy.csv"
    with taxonomy_path.open(encoding="utf-8-sig", newline="") as handle:
        topics = list(csv.DictReader(handle))
    taxonomy_ids = {r["topic_id"] for r in topics}
    if set(SCENARIOS) != taxonomy_ids:
        missing = sorted(taxonomy_ids - set(SCENARIOS))
        extra = sorted(set(SCENARIOS) - taxonomy_ids)
        raise ValueError(f"Scenario taxonomy mismatch; missing={missing}, extra={extra}")

    questions = build_questions(topics)
    questions.sort(key=lambda r: (r["split"], r["primary_label"], r["scenario_group_id"], r["question_id"]))
    fields = [
        "question_id", "scenario_group_id", "question_text", "language_style", "primary_label",
        "scope_label", "routing_action", "supported_topic_ids", "excluded_topic_ids", "referral_ids",
        "split", "origin", "annotation_status", "human_reviewer", "review_notes", "dataset_version", "status_as_of"
    ]
    write_csv(output / "classifier_questions.csv", questions, fields)
    with (output / "classifier_questions.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for question in questions:
            handle.write(json.dumps(question, ensure_ascii=False, sort_keys=True) + "\n")
    pq.write_table(pa.Table.from_pylist(questions), output / "classifier_questions.parquet", compression="zstd")

    referral_fields = [
        "referral_id", "agency", "service", "topic_ids", "when_to_use", "first_step", "portal_url",
        "information_url", "email", "phone", "office_address", "verification_source_url",
        "verification_status", "last_verified"
    ]
    write_csv(output / "referral_directory.csv", REFERRALS, referral_fields)

    label_counts = Counter(q["primary_label"] for q in questions)
    split_counts = Counter(q["split"] for q in questions)
    split_label_counts = Counter((q["split"], q["primary_label"]) for q in questions)
    topic_counts = Counter(topic for q in questions for topic in q["supported_topic_ids"] + q["excluded_topic_ids"])
    summary = {
        "item": 9,
        "dataset_version": DATASET_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status_as_of": STATUS_DATE,
        "question_count": len(questions),
        "scenario_group_count": len({q["scenario_group_id"] for q in questions}),
        "label_counts": dict(sorted(label_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "split_label_counts": {
            f"{split}:{label}": count for (split, label), count in sorted(split_label_counts.items())
        },
        "topic_counts": dict(sorted(topic_counts.items())),
        "language_style_counts": dict(sorted(Counter(q["language_style"] for q in questions).items())),
        "scope_label_counts": dict(sorted(Counter(q["scope_label"] for q in questions).items())),
        "routing_action_counts": dict(sorted(Counter(q["routing_action"] for q in questions).items())),
        "referral_count": len(REFERRALS),
        "review_gate": "All synthetic questions require human annotation review before training or evaluation use."
    }
    (output / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
