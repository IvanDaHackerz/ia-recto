"""AI-authored source-grounded development queries; no independent human-gold claim."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from common import readrows,save,jsonl,sha

# Expected provisions were chosen by inspecting the preserved source text,
# before scoring search methods. No topic-oracle filter is supplied for positives.
FAMILIES=[
 ('labor',['LAB_CODE_2022__art_83'],'General ordinary-hours provision',
  'At my private job, what is the normal daily limit on working hours?',
  'Private employee ako. Ilang oras ang normal na workday bago maging excess hours?'),
 ('labor',['LAB_CODE_2022__art_87','LAB_IRR_1989__rule_i_hours_of_work__section_8'],'Overtime pay for work beyond ordinary hours',
  'My private employer keeps me working after eight hours. Which provision covers the additional overtime payment?',
  'Sa private company, lampas eight hours ang trabaho ko. Saan nakasaad yung dagdag na overtime pay?'),
 ('labor',['LAB_CODE_2022__art_88'],'Undertime cannot offset overtime under this provision',
  'My private employer says yesterday\'s short hours cancel today\'s overtime. What text addresses that?',
  'Private worker ako. Pwede bang ibawas ang undertime kahapon sa overtime ko today?'),
 ('labor',['LAB_CODE_2022__art_89','LAB_IRR_1989__rule_i_hours_of_work__section_10'],'Situations listed for compulsory/emergency overtime',
  'When can my private employer require emergency overtime to prevent damage to equipment or perishable goods?',
  'Private job ito. Kailan pwedeng compulsory overtime dahil may emergency o masisirang products?'),
 ('labor',['LAB_IRR_1989__rule_iii_weekly_rest_periods__section_3'],'Weekly consecutive rest period',
  'What weekly rest period does the rule provide after six consecutive days at a private job?',
  'Anim na sunod na araw sa private work. Gaano kahaba ang weekly rest na nasa rules?'),
 ('labor',['LAB_IRR_1989__rule_iii_weekly_rest_periods__section_5'],'Written notice of rest-day schedules',
  'Does my private employer have to post written notice of the weekly rest-day schedule in advance?',
  'Private employee ako. Kailangan bang may advance written notice ng rest-day schedule?'),
 ('labor',['LAB_CODE_2022__art_94','LAB_IRR_1989__rule_iv_holidays_with_pay__section_3'],'General holiday-pay text, not a current-year holiday list',
  'Which basic provision discusses pay for a regular holiday at a private workplace?',
  'Sa private employer, saan ang general rule tungkol sa regular-holiday pay?'),
 ('labor',['LAB_CODE_2022__art_296'],'Probationary period and standards made known at engagement',
  'I am on probation at a private company. Where are the period limit and qualification standards discussed?',
  'Probationary ako sa private company. Anong provision sa haba ng probation at standards na dapat sinabi sa umpisa?'),
 ('labor',['LAB_CODE_2022__art_294'],'Security of tenure and just/authorized causes',
  'Which provision describes security of tenure and the grounds for ending regular private employment?',
  'Regular employee sa private firm. Saan nakalagay ang security of tenure at causes ng termination?'),
 ('labor',['LAB_IRR_1989__rule_viii_payment_of_wages__section_3'],'Frequency and timing of wage payments',
  'How frequently should a private employer pay wages under the payment-of-wages rules?',
  'Private employee ako. Gaano kadalas dapat ibigay ang sahod ayon sa wage-payment rules?'),
 ('labor',['LAB_IRR_1989__rule_viii_payment_of_wages__section_1'],'Legal tender rather than vouchers/tokens for wages',
  'Can my private employer pay my wages with shopping vouchers instead of legal tender?',
  'Sa private job, vouchers ang ibinibigay imbes na pera bilang sahod. Anong rule ang applicable?'),
 ('labor',['LAB_IRR_1989__rule_x_administration_and_enforcement__section_6'],'Information required in a payroll',
  'What payroll information should my private employer record about hours, overtime and deductions?',
  'Private employee ako. Anong details ang dapat nasa payroll tungkol sa oras, overtime, at deductions?'),
 ('labor',['DOLE_DO_249_25__rule_v_conciliat_on_mediation_proceedings__section_4'],'Confidentiality and recording during conciliation',
  'Are statements during SEnA conciliation confidential, and can a participant record the conference?',
  'Sa SEnA conference, confidential ba ang usapan at pwede bang mag-video record ang participant?'),
 ('labor',['DOLE_DO_249_25__rule_v_conciliat_on_mediation_proceedings__section_2'],'Appearance of lawyers/agents at conciliation',
  'What does the SEnA rule say about lawyers, agents or representatives appearing at a conference?',
  'Sa SEnA meeting, ano ang rule sa pagharap ng lawyer, agent, o representative?'),
 ('consumer',['RA_7394_1992__art_68'],'Written warranty terms and warrantor obligations',
  'What details must the written warranty for a retail appliance state about coverage and repairs?',
  'Bumili ako ng appliance sa store. Anong details ang dapat nasa written warranty tungkol sa coverage at repair?'),
 ('consumer',['RA_7394_1992__art_103'],'Replacement parts in product repair',
  'A repair shop fitted a replacement part that does not meet the appliance manufacturer\'s specification. What provision discusses parts?',
  'Repair shop gumamit ng piyesang hindi pasok sa manufacturer specs ng appliance. Saan ang rule tungkol sa replacement parts?'),
 ('consumer',['RA_7394_1992__art_102'],'Remedies for service quality imperfection',
  'A paid household repair service was improperly done. Which text covers redoing the service, refund or price reduction?',
  'Palpak ang paid repair service sa bahay. Saan ang provision tungkol sa redo, refund, o bawas presyo?'),
 ('consumer',['RA_7394_1992__art_100'],'Remedies when product quality imperfection is not corrected',
  'A retail product is unfit for use and repair has not corrected its quality problem. What text discusses replacement or reimbursement?',
  'Sira pa rin ang biniling item kahit inayos na. Anong provision sa replacement o refund para sa product quality problem?'),
 ('consumer',['RA_7394_1992__art_101'],'Net quantity below indicated amount',
  'The net quantity of a household product is less than the amount on its package. Where are the remedies stated?',
  'Kulang ang actual laman ng household product kumpara sa net quantity sa label. Saan ang remedies?'),
 ('consumer',['RA_7394_1992__art_97'],'Liability for defects and inadequate hazard information',
  'An appliance defect caused damage. Which provision discusses manufacturer liability and inadequate hazard information?',
  'May damage dahil defective ang appliance. Saan ang manufacturer liability at kulang na hazard information?'),
 ('consumer',['RA_7394_1992__art_10'],'Recall, prohibition and seizure of unsafe products',
  'What provision allows authorities to recall or prohibit an unsafe household consumer product?',
  'Unsafe ang household item. Anong provision sa recall o pag-ban ng consumer product?'),
 ('consumer',['RA_7394_1992__art_110'],'False or materially misleading advertisement',
  'A store advertisement hides material information about an ordinary product. Where is misleading advertising discussed?',
  'May mahalagang info na tinago sa advertisement ng store. Saan ang rule sa misleading advertising?'),
 ('consumer',['RA_7394_1992__art_50'],'Deceptive sales through concealment or false representation',
  'A retail seller described a refurbished appliance as brand new. What text addresses deceptive sales practices?',
  'Refurbished pala ang appliance pero sinabi ng seller brand new. Anong provision sa deceptive sales?'),
 ('consumer',['RA_7394_1992__art_81'],'Displayed retail price and prohibition on higher sale price',
  'The retail cashier charged more than the price displayed on the shelf. Which provision addresses price tags?',
  'Mas mahal ang singil ng cashier kaysa sa price tag sa shelf. Saan ang rule dito?'),
 ('consumer',['RA_10909_2016__sec_4'],'Exact change, coins and non-currency substitutes',
  'The grocery says it has no coins and wants to give candy instead of my change. What provision covers this?',
  'Walang barya daw ang grocery kaya candy na lang ang sukli. Saan ang exact-change rule?'),
 ('consumer',['RA_7394_1992__art_159'],'Consumer letter complaints and investigation',
  'Can a consumer submit a letter-complaint to trigger an investigation of a retail transaction?',
  'Pwede bang mag-submit ng letter-complaint ang consumer para ma-investigate ang store transaction?'),
 ('consumer',['RA_11967_2023__sec_20'],'Online consumer remedies and return without cost',
  'An online merchant delivered defective goods. Which provision discusses remedies and returning the original goods without cost?',
  'Defective ang delivery ng online merchant. Saan ang remedies at pagbabalik ng original goods nang walang gastos?'),
 ('consumer',['RA_11967_2023__sec_24'],'Internal redress before outside complaint and seven-day rule',
  'Must I use an online platform\'s internal complaint process before taking the complaint to an agency?',
  'Kailangan bang dumaan muna sa internal complaint process ng online platform bago sa government agency?'),
]

NEGATIVES=[
 ('labor','My government employer withheld my salary.','blocked_scope',None),
 ('labor','What is the exact minimum wage in my city today?','blocked_scope',None),
 ('labor','My overseas employer changed my OFW contract.','blocked_scope',None),
 ('labor','I have a complaint about my seafarer deployment.','blocked_scope',None),
 ('consumer','My bank charged an unauthorized credit card fee.','blocked_scope',None),
 ('consumer','My insurance claim was denied.','blocked_scope',None),
 ('consumer','My mobile phone plan has an extra telecom service charge.','blocked_scope',None),
 ('consumer','The seller posted my ID publicly without permission.','blocked_scope',None),
 ('consumer','The developer delayed turnover of my condominium.','blocked_scope',None),
 ('consumer','I want a criminal cyberfraud investigation of a fake store.','blocked_scope',None),
 ('labor','When should my private employer issue my COE and final pay?','no_eligible_evidence',['labor.final_pay_coe']),
]

def main():
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True);p.add_argument('--reuse-queries-from',type=Path);a=p.parse_args();out=a.index.resolve()
    if (out/'benchmark_queries.jsonl').exists():raise ValueError('Benchmark already created; do not overwrite')
    records=readrows(out/'records.jsonl');ids={r['provision_id'] for r in records};rows=[]
    for i,(domain,relevant,rationale,en,tl) in enumerate(FAMILIES,1):
        if set(relevant)-ids:raise ValueError('Expected relevance target is not indexed: '+str(set(relevant)-ids))
        for language,text in [('en',en),('en_tl',tl)]:rows.append({'query_id':f'IR_{i:02d}_{language}','scenario_family_id':f'IR_{i:02d}','question_text':text,'domain':domain,'language_style':language,
            'relevant_provision_ids':relevant,'relevance_rationale':rationale,'expected_status':'candidates_found','topic_ids':None,'origin':'ai_authored','relevance_judge':'Codex, source-text inspection','human_validated':False})
    for i,(domain,text,status,topics) in enumerate(NEGATIVES,1):rows.append({'query_id':f'IR_NEG_{i:02d}','scenario_family_id':f'IR_NEG_{i:02d}','question_text':text,'domain':domain,'language_style':'en','relevant_provision_ids':[],
        'expected_status':status,'topic_ids':topics,'origin':'ai_authored','relevance_judge':'Codex, recorded project scope/data availability','human_validated':False})
    if a.reuse_queries_from:
        old=a.reuse_queries_from;old_manifest=json.loads((old/'benchmark_manifest.json').read_text())
        if sha(old/'benchmark_queries.jsonl')!=old_manifest['queries_sha256']:raise ValueError('Reused query checksum mismatch')
        rows=readrows(old/'benchmark_queries.jsonl')
        if any(set(r['relevant_provision_ids'])-ids for r in rows):raise ValueError('Reused relevance target is no longer indexed')
    jsonl(out/'benchmark_queries.jsonl',rows)
    save(out/'benchmark_manifest.json',{'role':'source-grounded AI-authored development benchmark, not independent human gold','positive_queries':56,'positive_scenario_families':28,'negative_queries':len(NEGATIVES),
        'domain_is_given':'Oracle-domain retrieval evaluation; separate classifier integration checks are reported','positive_topic_filters_used':False,'relevance_labels_exhaustive':False,'relevance_limit':'Known source passages chosen by AI; other relevant results may be unjudged. This evaluates retrieval, not current law or answer correctness.',
        'queries_sha256':sha(out/'benchmark_queries.jsonl'),'index_manifest_sha256':sha(out/'index_manifest.json'),'retrieval_config_fixed_before_queries':not bool(a.reuse_queries_from),
        'reused_queries_from':str(a.reuse_queries_from) if a.reuse_queries_from else None,'previous_development_scores_inspected':bool(a.reuse_queries_from),'model_weights_or_idf_fitted_on_queries':False})
    print('Created '+str(len(rows))+' AI development retrieval queries',flush=True)
if __name__=='__main__':main()
