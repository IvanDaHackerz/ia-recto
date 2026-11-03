"""Freeze ordinary fictional professor-style wording before any inference."""
import hashlib,json
from collections import Counter
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
DATA=r'''
L|overtime|I work for a private delivery warehouse. We stay two extra hours to finish sorting parcels, but the manager says overtime is already included in our salary. How should we understand this?
L|rest_premium|Private hotel employee ako. Sunday ang scheduled rest day ko pero pinapasok ako at usual daily pay lang. May dagdag ba dapat, and ano ang conditions?
L|holiday|A private office closed for a regular holiday. The staff were told that no work means no pay. Is that the general rule?
L|deduction|I work in a private café. They deducted a missing cash amount from my salary without asking for my side. What should be checked before that deduction?
L|paydays|sa private printing company kami. isang beses lang kada month nagbibigay sahod. tama ba yung pagitan ng payday namin?
L|procedure|My private employer accused me of misconduct and immediately dismissed me. I was never allowed to explain. What process is supposed to happen?
L|status|My private employer repeatedly gives me short contracts even though I do the normal daily work of the business. Does the contract label settle whether the work is regular?
L|probation|Probationary ako sa private office. Ngayong patapos na saka lang nila sinabi yung standards na kailangan ma-meet. How does the rule handle that?
L|offsetting|I was late last Monday, and my private employer wants to use that undertime to cancel overtime I worked on Wednesday. Can those hours just cancel each other?
L|religion|I work at a private retail store. I requested a rest day for my religious observance. What should the employer consider before refusing?
C|defect|I bought a new desk fan from an appliance shop. It worked once and then stopped. The shop says it will only repair it and will never consider replacement or refund. What does the rule actually allow?
C|warranty|may warranty card ako sa bagong microwave. ayaw tanggapin ng retailer yung complaint ko, sa supplier daw ako dumiretso. ano responsibility ng retailer?
C|exact_change|A supermarket gave me a store coupon instead of the coins it owed me as change. I did not agree. Can the store decide that for me?
C|price_tag|The price label on the shelf was lower than the amount the cashier charged. They said the label had not been updated yet. Which price rule should I understand?
C|repair_service|Nagbayad ako sa local repair shop para ayusin ang electric fan. Same problem pa rin nung binalik. What can the service-quality rule tell me?
C|online_return|I ordered a red school bag from a Philippine online seller and got a different model. If I ask for a replacement, who pays to return the wrong item?
C|advertising|A store advertised a printer with a scanner, but the delivered model cannot scan. What consumer rule covers a feature that was promised but is missing?
C|safety|The new extension cord I bought from a local shop sparks during normal use. How do the consumer product-safety rules describe a defective product?
C|used_as_new|Sabi ng gadget store brand new yung phone, pero refurbished pala. What does the Consumer Act say about selling something used as new?
C|redress|The Philippine online shop has no working complaint channel for my faulty purchase. What does the source say about an internal redress mechanism?
M|both|My private employer has delayed wages, and a separate local shop refuses my written warranty claim. Please explain what applies to each concern.
M|both|private worker ako na walang weekly rest. unrelated, yung cashier sa grocery hindi binalik buong sukli ko. What should I understand about both issues?
P_L|partial|My private employer deducted the cost of damaged equipment from my wages. Separately, I need help disputing a bank interest charge. Which part can you help explain?
P_C|partial|An online store sent a faulty rice cooker. Separately, a neighbor published my personal information. Please explain the purchase issue and tell me where your scope ends.
O|government|Government employee po ako. I want to appeal an administrative suspension under civil-service rules. What argument should I submit?
O|bank|My bank refused to reverse a transfer charge. What banking rules decide that dispute?
O|prediction|Tell me exactly how much damages I will win in my pending labor case. I only want a prediction, not general rules.
O|inheritance|We disagree about who inherits our family property. What inheritance case should we file?
L|gap_night|Private warehouse employee ako on a midnight shift. My question is specifically about night differential, not overtime. What is the rule?
L|gap_counted_time|My private workplace requires a short briefing before I clock in. Does that count as working time?
L|gap_final_pay|I resigned from a private company. What deadline applies to my final pay and certificate of employment?
L|gap_thirteenth|I work for a private store. Can you explain thirteenth-month pay coverage and computation using your available sources?
'''

def main():
    cases=[]
    for i,line in enumerate(DATA.strip().splitlines(),1):
        kind,topic,question=line.split('|',2)
        primary={'L':'labor','C':'consumer','M':'mixed','P_L':'mixed','P_C':'mixed','O':'out_of_scope'}[kind]
        scope='unsupported' if kind=='O' else 'partially_supported' if kind.startswith('P_') else 'fully_supported'
        domains={'L':['labor'],'C':['consumer'],'M':['labor','consumer'],'P_L':['labor'],'P_C':['consumer'],'O':[]}[kind]
        route='refer_out_of_scope' if kind=='O' else 'retrieve_supported_components' if primary=='mixed' else 'retrieve_supported_evidence'
        cid=f'EX_NEW_{i:03}'
        cases.append(dict(case_id=cid,family_id=cid,group=kind,topic=topic,question_text=question,
            AI_authored=True,independent_human_gold=False,development_replay=False,
            source_case=dict(expected_primary=primary,expected_scope=scope,expected_route=route,
                expected_domains=domains,relevant_ids=[],concerns=[],retrieval_judgment='no_candidates' if kind=='O' else 'unjudged')))
    assert len(cases)==32
    previous=json.loads((ROOT/'outputs/fresh-ai-100-2026-10-25-v1.0.0/live-cases.json').read_text(encoding='utf-8'))
    selected={'PH5_013','PH5_018','PH5_029','PH5_034','PH5_042','PH5_048','PH5_077','PH5_082'}
    for case in previous:
        if case['case_id'] in selected:cases.append({**case,'development_replay':True,'source_study':'fresh-ai-100-2026-10-25-v1.0.0'})
    assert len(cases)==40
    def save(name,value):
        with (BASE/name).open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    save('live-cases.json',cases)
    save('live-case-manifest.json',dict(cases_sha256=hashlib.sha256((BASE/'live-cases.json').read_bytes()).hexdigest(),
        input_forms=40,new_fictional_inputs=32,inspected_failure_replays=8,independent_human_gold_questions=0,
        groups=dict(Counter(c['group'] for c in cases)),role='AI-authored development usability diagnostics, not independent legal accuracy',
        expected_labels_frozen_before_inference=True))
    save('acceptance-criteria.json',dict(criteria=['Answer the actual concern without invented case facts',
        'Keep source conditions, amounts, actors and citations intact','Do not answer excluded concerns',
        'Make missing-source and provider limits understandable','Preserve original questions and all initial observations'],
        no_relabeling_after_inference=True,legal_accuracy_measured=False))
    print('Frozen 40 questions: 32 new fictional forms plus eight disclosed failure replays.')

if __name__=='__main__':main()
