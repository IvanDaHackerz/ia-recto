import { Link } from "react-router-dom";
import { ArrowRight, ChevronDown, ExternalLink } from "lucide-react";
import type { Citation } from "../data/answers";
import { documentUrl, libraryDocuments, locatorText, sourceLink } from "../data/library";
export function CitationCard({ citation, number, id, expanded, onToggle }: { citation: Citation; number: number; id: string; expanded: boolean; onToggle: () => void }) {
  const document = libraryDocuments.find(doc => doc.id === citation.sourceId);
  const provisions = document?.provisions.filter(p => citation.provisionIds.includes(p.id)) ?? [];
  const restricted = provisions.some(provision => !provision.answerEligible);
  return <section className="reference-block" id={id} tabIndex={-1} data-expanded={expanded} aria-label={`Reference ${number}: ${citation.citation}`}>
    <button className="reference-block-toggle" type="button" aria-expanded={expanded} aria-controls={`${id}-content`} onClick={onToggle}>
      <span className="reference-number">{number}</span><span><span className="reference-block-title">{citation.citation}</span><span className="metadata">{document?.title ?? citation.title}</span></span><ChevronDown size={18} aria-hidden="true" />
    </button>
    <p className={`reference-status metadata${restricted ? " is-restricted" : ""}`}>{!document ? "Source metadata unavailable" : restricted ? "Stored restriction: blocked from answer use" : "Recorded source · sample citation not validated"}</p>
    <div id={`${id}-content`} className="reference-content" hidden={!expanded}>
      {document ? <>
        <p className="metadata">Source status recorded {document.lastChecked}. This sample response has not been citation-validated.</p>
        {provisions.map(provision => <details className="reference-provision" key={provision.id}>
          <summary>{provision.label}{provision.heading ? `: ${provision.heading}` : ""}</summary>
          <p className="metadata">{locatorText(provision)}. {provision.answerEligible ? "Provision permitted by the stored data gates; freshness checks still apply." : "This provision is blocked from answer use in the stored data."}</p>
          {provision.qualityFlags.length > 0 && <p className="metadata">Recorded extraction notes: {provision.qualityFlags.join(", ").replaceAll("_", " ")}.</p>}
          <p className="source-text">{provision.text || "Stored provision text is unavailable."}</p>
          <Link to={sourceLink(document.id, provision.id)} className="text-link touch-link citation-jump">Open {provision.label} in Library <ArrowRight size={16} strokeWidth={1.6} aria-hidden="true" /></Link>
        </details>)}
        {provisions.length === 0 && <p className="metadata">No exact provision is mapped to this example yet.</p>}
        <a className="text-link touch-link citation-jump" href={documentUrl(document, provisions[0])} target="_blank" rel="noreferrer">Open source document <ExternalLink size={15} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span></a>
      </> : <p className="metadata">This reference cannot be presented as verified.</p>}
    </div>
  </section>;
}
