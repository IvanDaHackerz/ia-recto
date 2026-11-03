"""Reserved synthetic probe, frozen before repairs; still AI-authored, not independent gold."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
DATA='''
L|I am employed at a private dental clinic. Our salaries have been unpaid for two months.
L|Nagtatrabaho sa private bodega. Pinapa-duty kami kahit naka day off, walang dagdag bayad.
L|The private store makes us attend an unpaid half-hour meeting before every shift.
L|An employee at a private lending firm wants basic overtime-pay information about her job.
L|My private employer says cashiers must reimburse every customer shortage from their wages.
L|Our private employer calls every regular monthly payment an advance and keeps deducting it later.
L|The private restaurant owner fired me in a text message without explaining a cause.
L|Private shop staff kami, paano magtanong sa DOLE tungkol sa delayed salary?
L|My private employer says my six-month contract prevents me from ever becoming regular.
L|The employer withheld my earned salary after I resigned from my private job.
C|A retail store sold me a rechargeable light that won't hold a charge.
C|Bumili ako ng bagong plantsa sa appliance store, pero di umiinit. Anong consumer concern ito?
C|The laundry service mixed bleach into my colored clothes and ruined them.
C|The store manager says the printed warranty does not apply to discounted appliances.
C|An online retailer delivered a cheap substitute for the branded item on my receipt.
C|My supermarket receipt is higher than the price clearly printed on the shelf.
C|I paid a bicycle repair shop to fix a brake but it returned the bicycle without doing the repair.
C|A toy from a retailer overheats and the casing becomes dangerously hot.
C|The retailer advertised a new mattress but delivered a used one with stains.
C|A business seller on an online marketplace refuses to deliver my paid desk order.
B|Private employer owes salary. Also, the appliance retailer refuses my warranty repair.
B|My private office requires unpaid overtime, and a shop charged more than the price tag.
B|The private factory gave me no rest day; a laundry shop also lost my shirts.
B|The employer won't release my COE from my private job. The online retailer delivered a damaged chair.
P|Private employer has not paid my salary. I also need help disputing a credit-card fee with my bank.
P|The private store dismissed me without notice. What are my chances of winning the pending NLRC case?
Q|The retailer sold me a broken appliance. My broadband provider also refuses to cancel my internet plan.
Q|The shop will not honor my warranty. Separately, my insurer has rejected my policy claim.
Q|The repair shop ruined my chair, and my landlord will not return my rental deposit.
Q|The store charged more than the shelf price and the airline lost my checked bag.
X|Domestic helper ako sa bahay ng employer at hindi binabayaran nang tama.
X|Government nurse ako sa public hospital at may problema sa salary.
X|My overseas employer in Bahrain refuses to give me my final wages.
X|The union wants advice on challenging a collective bargaining representation election.
X|How much compensation does a seafarer get for permanent disability?
X|My investment broker will not transfer the proceeds of my securities sale.
X|The phone company renewed my mobile data plan without permission.
X|An online seller published my ID and address to shame me publicly.
X|Please calculate my GSIS retirement pension.
X|What is the exact minimum-wage rate in my city today?
X|My landlord added fees to the apartment rent. What can I do?
X|Someone stole my bag while I was heading to collect my salary.
A|Ayaw niya ako bayaran pero di ko alam anong details kailangan.
A|The contract is unfair. Help me understand it.
A|They refused my request again yesterday.
A|May tanong lang tungkol sa service, pwede ba?
'''
def main():
 cases=[]
 for i,line in enumerate(DATA.strip().splitlines(),1):
  k,q=line.split('|',1);c={'id':f'RES{i:03}','q':q,'flow':'clarify' if k=='A' else 'referral' if k=='X' else 'local_sources'}
  if k!='A':c.update(primary={'L':'labor','C':'consumer','B':'mixed','P':'mixed','Q':'mixed','X':'out_of_scope'}[k],scope='unsupported' if k=='X' else 'partially_supported' if k in 'PQ' else 'fully_supported')
  cases.append(c)
 f=H/'reserved_cases.json'
 if f.exists():raise RuntimeError('Do not overwrite frozen cases')
 f.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'count':len(cases),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
