import { referralSnapshot } from "../data/source-snapshot";
export function OutOfScopeNotice({ message, referralIds = [], evidenceMissing = false, title }: { message: string; referralIds?: string[]; evidenceMissing?: boolean; title?: string }) {
  return <section className={`notice${evidenceMissing ? " notice-caution" : " notice-redirect"}`}>
    <h3>{title ?? (evidenceMissing ? "Not enough supporting evidence" : "Outside the supported scope")}</h3>
    <p>{message}</p>
    {referralIds.length > 0 && <div className="referrals"><h4>Where to find assistance</h4><ul>{referralIds.map(id => {
      const referral = referralSnapshot.find(r => r.id === id);
      return referral ? <li key={id}><a href={referral.url} target="_blank" rel="noreferrer">{referral.agency} <span className="sr-only">(opens in a new tab)</span></a><span className="metadata">Directory link last checked {referral.lastChecked}</span></li> : null;
    })}</ul></div>}
  </section>;
}
