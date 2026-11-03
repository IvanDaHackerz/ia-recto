"""AI-authored local development probes, never human gold or training data."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
# L/C/B = supported labor/consumer/both, P/Q = labor/consumer plus excluded,
# X = excluded only, A = genuinely under-specified. Each sentence is hand composed.
DATA='''
L|wages|Our bakery pays everyone ten days late every month. Where can workers ask about wage-payment rules?
L|wages|Boss keeps saying next week when I ask for the salary I already earned.
L|wages|Nagtatrabaho ako sa private warehouse, pero kulang yung sweldo ko nitong cutoff.
L|wages|My payslip lists a deduction for broken cups even though I never agreed to it.
L|wages|Cashier ako sa supermarket. May salary deduction kami pag kulang ang kaha.
L|wages|The employer pays us with store vouchers instead of money.
L|wages|The owner says tips from customers replace our basic wages at the restaurant.
L|wages|A private clinic employs me as a receptionist. They keep delaying my salary.
L|hours|Our private warehouse counts mandatory bag checks after the shift as unpaid time.
L|hours|I have to stay at my desk through lunch to answer customer calls. Is that working time?
L|hours|Eight hours ba kasama yung required opening meeting namin sa private store?
L|hours|Pinapastay kami sa factory kahit walang ginagawa habang naghihintay ng delivery.
L|rest|My employer schedules me for fourteen straight days without a day off.
L|rest|Rest day ko Sunday pero pinapapasok ako ng restaurant manager. Ano basic rules?
L|rest|Can a private employer move our weekly rest day every week?
L|overtime|My supervisor makes me clock out after eight hours then finish packing orders without extra pay.
L|overtime|Private company ako. Ten hours ang shift pero eight hours lang nasa payslip.
L|overtime|We are told overtime is included in our salary even when we work extra hours.
L|overtime|Nag OT ako sa shop ng dalawang oras pero regular rate lang binigay.
L|holiday|The private factory made us work on a regular holiday without additional pay.
L|holiday|Closed ang private office sa Christmas. May general holiday-pay rules ba kahit walang pasok?
L|holiday|How do regular holidays differ from special nonworking days for a private employee's pay?
L|thirteenth|My private employer calls the Christmas bonus our 13th-month pay. What distinction matters?
L|thirteenth|Three months lang ako nagwork sa private cafe this year, may prorated 13th month ba?
L|thirteenth|The employer says probationary staff don't get thirteenth-month pay.
L|contract|Every five months the private company renews my contract for exactly the same work.
L|contract|Project-based daw ako pero wala silang sinabing project sa contract ko.
L|contract|My private employer calls me a freelancer, but sets my daily hours and supervises everything.
L|contract|The company hired me on probation without explaining the standards for regular employment.
L|termination|Private employer removed my access card and said I am fired, with no letter or hearing.
L|termination|My manager says poor performance is enough to dismiss me immediately without notice.
L|termination|The private company is closing one department and says everyone is redundant.
L|termination|Pinapirma ako ng resignation letter pero hindi naman ako kusang nagresign sa private job ko.
L|final|I left a private company and HR will not release my certificate of employment.
L|final|Private employer ko ayaw ibigay final pay kahit tapos na clearance.
L|final|Does resigning from a private job mean I lose wages that I already earned?
L|referral|I need to know where a private-sector worker can raise an unpaid-salary complaint.
L|referral|Saan lalapit ang employee ng private shop kapag walang sweldo at walang payslip?
L|boundary|I work for a private telecom company. My question is about unpaid overtime, not my phone bill.
L|boundary|I am an employee at a private hospital and they deducted my salary for being late.
C|defect|Bought a desk lamp at a hardware store; it stopped switching on after one afternoon.
C|defect|Yung bagong electric fan galing sa appliance shop amoy sunog agad nung sinaksak.
C|defect|The shop sold me a supposedly new laptop with a cracked screen inside the sealed box.
C|defect|The shoes I bought from a retailer have soles that came off on the first day.
C|warranty|The appliance seller says my written one-year warranty ended after a month.
C|warranty|May warranty card yung blender pero ayaw tanggapin ng shop kasi sale item daw.
C|warranty|The seller requires the original box before accepting my faulty kettle under warranty.
C|warranty|A shop says a manufacturing defect is my responsibility even though the product has a warranty.
C|remedy|The seller has repaired my washing machine three times and it still leaks. What remedies can I read about?
C|remedy|No return no exchange daw kahit defective yung bagong binili kong toaster sa store.
C|remedy|The store delivered the wrong size table and refuses a replacement.
C|remedy|Nagbayad ako sa retailer para sa blue chair pero red ang pinadala at ayaw palitan.
C|sales|The store added an installation fee only after I had already paid for the appliance.
C|sales|A salesperson told me a secondhand phone was brand new and I bought it based on that claim.
C|sales|The shop hid a nonoptional service fee until checkout.
C|sales|Binenta nila yung display unit bilang bago, wala silang sinabi bago ako nagbayad.
C|advert|An advertisement promised a genuine leather bag but the retailer sent plastic.
C|advert|The electric fan advertised as silent makes a very loud grinding noise.
C|advert|The online shop advertises a free accessory but charges for it after payment.
C|price|The shelf says 199 but the cashier charges 249 for the same item.
C|price|Sukli ko sa grocery ginawa nilang candy kahit hindi ako pumayag.
C|price|A retail store displays no prices on any of its household goods.
C|price|The price sticker on my kettle is lower than the amount on my receipt.
C|safety|The plug on a brand-new lamp from a store sparks and melts during normal use.
C|safety|A toy sold by a retailer has loose sharp metal parts that fall out.
C|safety|May exposed wire yung bagong extension cord sa hardware. Unsafe consumer product ba ito?
C|service|I paid a furniture repair shop but they returned my chair with a broken leg.
C|service|Nagbayad sa laundry shop pero nawala nila yung damit ko at ayaw ayusin ang reklamo.
C|service|A paid shoe-cleaning service damaged my shoes instead of cleaning them.
C|online|An online retailer accepted my payment two weeks ago but has not shipped my order or answered a refund request.
C|online|Wrong item dumating galing sa registered online shop at ayaw nila ng replacement.
C|online|The business seller on a marketplace keeps cancelling delivery dates for my paid order.
C|referral|I have a receipt and photos of the damaged appliance. How do I raise a consumer complaint with DTI?
C|referral|Paano magreklamo tungkol sa repair shop na hindi tinapos yung binayaran kong trabaho?
C|framework|What is the Consumer Act of the Philippines generally intended to protect?
C|framework|Can you explain the scope of general consumer protection for household purchases?
C|boundary|My employer gave me a gift card. I used it at a store and the store sold me a broken fan.
C|boundary|I bought a phone from a retailer for work, and it arrived with a broken camera.
C|boundary|The shop manager refuses to honor the warranty on the appliance I purchased.
C|boundary|The private company that sold me a refrigerator refuses a refund for a defective unit.
B|both|Our private employer pays wages late. Separately, a retailer will not honor my laptop warranty.
B|both|Private employee ako, walang OT pay. Yung binili kong fan sa store sira din agad.
B|both|I was dismissed by my private employer without notice, and an online retailer delivered the wrong product.
B|both|My employer keeps withholding salary and the grocery cashier keeps charging more than the displayed price.
B|both|Two concerns: no weekly rest day at my private job; a paid repair shop damaged my bicycle.
B|both|My private employer refuses my COE. A store also refuses to replace a defective kettle.
B|both|Nagtrabaho sa regular holiday sa private shop pero walang premium. May misleading ad din yung retailer na pinagbilhan ko.
B|both|The private company deducts from my salary without explanation, while a store refuses my product warranty.
B|both|My private employer won't pay my 13th month. Also, the price at the grocery checkout is higher than the shelf tag.
B|both|Our company requires unpaid work after clock-out; the online business I bought from refuses to deliver my order.
P|partial|My private employer owes wages, and my bank charged an unexplained account fee.
P|partial|My private employer dismissed me without notice. Separately, can you predict whether I will win the case?
P|partial|Private company ako, hindi bayad OT ko. Gusto ko rin malaman exact minimum wage ngayon sa Cebu.
P|partial|I need general wage-payment rules for my private job and help with my pending NLRC case.
P|partial|I receive no rest day at my private job; my internet provider also billed me twice.
P|partial|The private shop owes my final pay. Separately, my landlord keeps my rental deposit.
Q|partial|A retailer sold me a faulty kettle, and my mobile provider charged the wrong subscription fee.
Q|partial|My online shop order arrived broken. The same seller also posted my home address publicly without permission.
Q|partial|The shop refuses my written product warranty, and my insurer refuses my policy claim.
Q|partial|The grocery charged more than the price tag. Also, I need help with an airline refund.
Q|partial|Nagbayad sa laundry shop pero sira damit ko. Yung electric utility bill ko sobra rin.
Q|partial|The appliance seller refuses a refund, and I want to know the legal rules for my divorce.
X|government|I am employed at city hall and the municipality has not paid my salary.
X|government|Public school teacher ako. May issue ako sa government salary deductions ko.
X|household|Yaya ako ng bata sa bahay ng isang pamilya, walang day off na binibigay.
X|household|I am a live-out domestic worker for a household and my employer withholds my pay.
X|overseas|I work in Qatar and my employer has withheld my passport and wages.
X|overseas|The overseas recruiter changed the contract for my job in Saudi Arabia.
X|sea|I work aboard an international cargo ship and need help with my seafarer employment contract.
X|union|How do we contest the result of our union representation election?
X|compensation|I need a computation of disability benefits after a workplace injury.
X|osh|Does the chemical ventilation in our factory comply with occupational safety standards?
X|pension|Please calculate how much SSS pension I will get next year.
X|pending|What evidence should I submit in my pending NLRC dismissal case?
X|prediction|Can you tell me whether I will win my illegal dismissal case?
X|minimum|Magkano eksaktong minimum wage ngayon sa NCR para sa retail employee?
X|bank|My bank deducted an unauthorized fee from my savings account.
X|insurance|My insurer denied the claim on my car insurance policy.
X|investment|I invested in a securities fund but the platform will not let me withdraw.
X|telecom|My broadband provider bills me for an internet plan I already cancelled.
X|privacy|A seller published my ID photo online without my consent.
X|medical|The surgeon operated on the wrong part of my body. Can I bring a malpractice complaint?
X|housing|The condominium developer keeps delaying turnover of the unit I bought.
X|transport|The airline cancelled my flight and refuses a refund.
X|utility|My water provider charged three times the usual amount on the bill.
X|crime|The fake online seller disappeared after receiving my payment. How do I ask police to investigate?
X|family|My sibling and I disagree over inheritance of our parents' land.
X|general|Can you help me solve this algebra homework problem?
X|general|How do I cook chicken adobo for four people?
X|code|Write a Python script to calculate the average of a list.
A|vague|They won't give it back. What can I do?
A|vague|May problema ako sa bayad.
A|vague|I signed something and now I regret it.
A|vague|The manager said no. Is that allowed?
A|vague|Hindi ko alam paano ito ayusin.
A|vague|Can you help me please?
A|vague|I paid but nothing happened.
A|vague|Ayaw nila ibigay yung kailangan ko.
'''
def main():
 cases=[]
 for i,line in enumerate(DATA.strip().splitlines(),1):
  kind,field,q=line.split('|',2)
  c={'id':f'DEV{i:03}','field':field,'q':q,'flow':'clarify' if kind=='A' else 'referral' if kind=='X' else 'local_sources'}
  if kind!='A':c.update(primary={'L':'labor','C':'consumer','B':'mixed','P':'mixed','Q':'mixed','X':'out_of_scope'}[kind],scope='unsupported' if kind=='X' else 'partially_supported' if kind in 'PQ' else 'fully_supported')
  cases.append(c)
 target=HERE/'development_cases.json'
 if target.exists():raise RuntimeError('Frozen cases already exist')
 target.write_text(json.dumps(cases,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'count':len(cases),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'provenance':'AI-authored synthetic development probes; no human or independent accuracy claim'}))
if __name__=='__main__':main()
