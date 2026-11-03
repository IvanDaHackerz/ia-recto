"""Unused synthetic scenario probe. Expected labels are authored before inference."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
DATA='''
L|Our private restaurant employer holds the first month's salary as a security deposit.
L|A private office employee is told to answer work calls during an unpaid lunch break.
L|My private employer says newly hired probationary workers cannot receive holiday pay.
L|Kulang ang 13th month na binigay ng private employer ko kahit buong taon ako nagwork.
L|My private employer keeps renewing a project-based contract without identifying any project.
L|Private company dismissed my sister without any notice or explanation. What basic process can she read about?
L|Can a private employer refuse a certificate of employment because an employee resigned?
L|I'm a private supermarket employee. Where can I ask about deductions from my wages?
C|The appliance shop says the blender's motor is not covered by its written warranty.
C|A retailer delivered a cupboard with a broken door and refuses to replace it.
C|The grocery cashier says I must accept sweets instead of my exact change.
C|Bumili sa online business ng bagong bag pero mali ang product na dumating at ayaw ng refund.
C|A shop advertised a stainless-steel pot but delivered one made of a different material.
C|The paid repair service left my washing machine in worse condition and won't address my complaint.
C|The hardware store sold an electric kettle with a loose exposed wire near the handle.
C|My employer recommended a store, and that retailer sold me a defective laptop. This is about the purchase.
B|A private employer has delayed my salary, and a paid laundry shop ruined my jacket.
B|The private company refuses my COE and the store refuses to honor my refrigerator warranty.
B|Unpaid overtime at my private job and a misleading product ad from the retailer are my two concerns.
B|Our private shop gives no weekly rest day. Separately, the online business seller delivered a broken table.
P|I want general dismissal notice rules for private employees, and a prediction of my chances of winning a pending case.
P|My private employer owes my wages, while my insurance company is delaying my claim.
Q|The store sold me a defective phone; the mobile network also charged an unauthorized data-plan fee.
Q|The laundry shop damaged my shirts, and the water utility billed me for an unexplained meter charge.
X|The employer in Singapore has not released my salary for my overseas job.
X|Kasambahay ako at hindi tama ang sweldo ko sa household employer.
X|A government employee needs help disputing an administrative charge.
X|What legal arguments should I make at the hearing of my pending NLRC case?
X|Can you calculate my retirement benefits and SSS pension?
X|The bank refuses to reverse an unauthorized debit from my account.
X|A seller leaked my identity documents online without my consent.
X|The apartment landlord is keeping my rent deposit after I moved out.
X|The airline cancelled our booking and refuses to return the fare.
X|The fake online store took the money and disappeared. I want a police investigation.
X|Please explain how to debug a JavaScript program.
X|My cousin needs advice about a divorce and child custody.
A|They kept some money and won't explain why.
A|Someone changed the agreement. What are my rights?
A|May problema po. Ano gagawin ko?
A|Can I ask about something that happened yesterday?
'''
cases=[]
for i,line in enumerate(DATA.strip().splitlines(),1):
 k,q=line.split('|',1);c={'id':f'FINAL{i:03}','q':q,'flow':'clarify' if k=='A' else 'referral' if k=='X' else 'local_sources'}
 if k!='A':c.update(primary={'L':'labor','C':'consumer','B':'mixed','P':'mixed','Q':'mixed','X':'out_of_scope'}[k],scope='unsupported' if k=='X' else 'partially_supported' if k in 'PQ' else 'fully_supported')
 cases.append(c)
f=H/'final_probe_cases.json'
if f.exists():raise RuntimeError('Frozen file exists')
f.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'count':len(cases),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'use':'post-repair synthetic probe; not used for fitting or repair before first result'}))
