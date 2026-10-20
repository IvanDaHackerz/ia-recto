import { useEffect, useMemo, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { documentUrl, libraryDocuments, locatorText } from "../data/library";
export function LibraryPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const domainParam = params.get("domain") ?? "all";
  const domain = ["labor", "consumer"].includes(domainParam) ? domainParam : "all";
  const candidatesOnly = params.get("candidates") === "yes";
  const selectedId = params.get("doc");
  const provisionId = params.get("provision");
  const selected = libraryDocuments.find(doc => doc.id === selectedId);
  const readerRef = useRef<HTMLElement>(null);
  const listHeadingRef = useRef<HTMLHeadingElement>(null);
  const previousSelection = useRef<string | null>(null);
  const results = useMemo(() => libraryDocuments.filter(doc => {
    if (domain !== "all" && doc.domain !== domain) return false;
    if (candidatesOnly && !doc.answerCandidate) return false;
    return [doc.title, doc.citation, doc.notes, ...doc.provisions.map(p => p.heading)].join(" ").toLocaleLowerCase().includes(query.trim().toLocaleLowerCase());
  }), [query, domain, candidatesOnly]);
  useEffect(() => {
    let focusFrame = 0;
    if (selectedId) {
      // Run after route-level focus/scroll restoration. Deep links land on the actual provision.
      focusFrame = requestAnimationFrame(() => {
        const linkedProvision = provisionId ? document.getElementById(`provision-${provisionId}`) : null;
        const target = linkedProvision?.querySelector<HTMLElement>("summary") ?? readerRef.current;
        target?.focus({ preventScroll: true });
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (linkedProvision || window.matchMedia("(max-width: 899px)").matches) {
          target?.scrollIntoView({ block: "start", behavior: reduced ? "instant" : "smooth" });
        }
      });
    } else if (previousSelection.current) {
      listHeadingRef.current?.focus({ preventScroll: true });
      listHeadingRef.current?.scrollIntoView({block:"start", behavior:"instant"});
    }
    previousSelection.current = selectedId;
    return () => cancelAnimationFrame(focusFrame);
  }, [selectedId, provisionId]);
  function filter(name: string, value: string) {
    const next = new URLSearchParams(params);
    if (value && value !== "all") next.set(name, value); else next.delete(name);
    next.delete("doc"); next.delete("provision");
    setParams(next, {replace:true});
  }
  function choose(id: string) { const next = new URLSearchParams(params); next.set("doc", id); next.delete("provision"); setParams(next); }
  function backToList() {
    const next = new URLSearchParams(params); next.delete("doc"); next.delete("provision"); setParams(next);
  }
  return <div className="library-page">
    <header className="page-heading"><div><h1>Source library</h1><p>Recorded metadata and selected complete provisions from the project's canonical collection. Verification, answer eligibility, and currentness are separate checks.</p></div></header>
    <div className={`library-filters${selectedId ? " has-reader" : ""}`}>
      <div className="search-field"><label htmlFor="lib-search">Search source records</label><input id="lib-search" type="search" value={query} onChange={e => filter("q",e.target.value)} placeholder="Title, citation, or topic" /></div>
      <div><label htmlFor="lib-domain">Topic</label><select id="lib-domain" value={["labor","consumer"].includes(domain) ? domain : "all"} onChange={e => filter("domain",e.target.value)}><option value="all">All topics</option><option value="labor">Labor</option><option value="consumer">Consumer</option></select></div>
      <label className="checkbox-label"><input type="checkbox" checked={candidatesOnly} onChange={e => filter("candidates",e.target.checked ? "yes" : "")} />Document candidates only</label>
      {(query || domain !== "all" || candidatesOnly) && <button className="text-link touch-link" type="button" onClick={() => setParams({})}>Clear filters</button>}
    </div>
    <div className={`library-layout${selectedId ? " has-reader" : ""}`}>
      <section className="library-list-pane" aria-labelledby="results-heading">
        <h2 ref={listHeadingRef} tabIndex={-1} id="results-heading" className="results-heading">Source records</h2>
        <p role="status" aria-live="polite" className="metadata">{results.length} {results.length === 1 ? "document" : "documents"} found</p>
        {results.length ? <ul className="source-list">{results.map(doc => <li key={doc.id}><button type="button" aria-pressed={doc.id === selectedId} onClick={() => choose(doc.id)}>
          <span className="source-title">{doc.title}</span><span className="metadata">{doc.citation}</span><span className="source-status">{doc.answerCandidate ? "Document candidate" : "Restricted to reference"}</span>
        </button></li>)}</ul> : <div className="empty-state"><h3>No matching source records</h3><p>Try a shorter title or citation, choose another topic, or clear the filters.</p><button type="button" className="secondary-button" onClick={() => setParams({})}>Clear filters</button></div>}
      </section>
      {(selectedId || results.length > 0) && <article ref={readerRef} tabIndex={-1} aria-label="Document reader" className="library-reader">
        {selectedId && <button type="button" className="text-link touch-link reader-back" onClick={backToList}>Back to source records</button>}
        {selected ? <div key={selected.id}>
          <h2>{selected.title}</h2>
          <dl className="document-meta"><div><dt>Citation</dt><dd>{selected.citation}</dd></div><div><dt>Issuer</dt><dd>{selected.issuer}</dd></div><div><dt>Edition / approval</dt><dd>{selected.date}</dd></div><div><dt>Recorded status date</dt><dd>{selected.lastChecked}</dd></div></dl>
          <p className="source-status">{selected.answerCandidate ? "Document candidate; provision-level checks still apply" : "Restricted to reference; not a current answer authority"}</p>
          <div className="source-actions"><a className="text-link touch-link" href={selected.officialUrl} target="_blank" rel="noreferrer">Official publication page <span className="sr-only">(opens in a new tab)</span></a>
            {selected.retrievalUrl !== selected.officialUrl && <a className="text-link touch-link" href={selected.retrievalUrl} target="_blank" rel="noreferrer">Recorded retrieval copy <span className="sr-only">(opens in a new tab)</span></a>}</div>
          <details className="source-checks"><summary>Recorded checks and restrictions</summary><dl className="document-meta">
            <div><dt>Source verification</dt><dd>{selected.verificationStatus.replaceAll("_"," ").replaceAll(";","; ")}</dd></div>
            <div><dt>Legal status</dt><dd>{selected.legalStatus.replaceAll("_"," ")}</dd></div>
          </dl>{selected.freshness && <p>{selected.freshness}</p>}{selected.notes && <p>{selected.notes}</p>}</details>
          <section className="provisions"><h3>Selected stored provisions</h3><p className="metadata">These are complete selected provisions, not the entire document. Text is preserved from the local extraction; recorded review restrictions remain in force. Follow the publication link to inspect the complete source.</p>
            {provisionId && !selected.provisions.some(p => p.id === provisionId) && <p className="notice notice-caution">The requested provision is not included in this snapshot. Use the publication link above.</p>}
            {selected.provisions.length ? selected.provisions.map((provision,index) => <details className="provision" id={`provision-${provision.id}`} data-cited={provisionId === provision.id} key={`${provision.id}-${provisionId === provision.id}`} open={provisionId ? provision.id === provisionId : index === 0}>
              <summary><span>{provision.label}{provision.heading ? `: ${provision.heading}` : ""}</span>{provisionId === provision.id && <span className="citation-target-label">Linked provision</span>}</summary>
              <p className="metadata">{locatorText(provision)}</p>
              <p className={`provision-gate${provision.answerEligible ? "" : " is-restricted"}`}>{provision.answerEligible ? "Permitted by stored provision gates. Currentness and evidence checks are still required." : `Blocked from answer use: ${provision.useMode.replaceAll("_"," ")}.`}</p>
              {provision.qualityFlags.length > 0 && <p className="metadata">Recorded extraction notes: {provision.qualityFlags.map(flag => flag.replaceAll("_"," ")).join("; ")}.</p>}
              <blockquote className="source-text">{provision.text}</blockquote>
              <a className="text-link touch-link" href={documentUrl(selected,provision)} target="_blank" rel="noreferrer">Inspect this location in the source <span className="sr-only">(opens in a new tab)</span></a>
            </details>) : <p>No extracted provision is available in this snapshot. Use the publication link.</p>}
          </section>
        </div> : <div className="empty-state"><h2>{selectedId ? "Source record unavailable" : "Choose a source to read"}</h2><p>{selectedId ? "This link does not match a record in the local snapshot. Return to the list to choose an available source." : "Select a document to inspect its recorded checks, selected provisions, and publication link."}</p></div>}
      </article>}
    </div>
  </div>;
}
