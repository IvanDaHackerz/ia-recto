import { ChevronDown, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { labelName, routeName, type ChatResult, type LiveReference } from "../data/api";
import { GeneratedExplanation } from "./GeneratedExplanation";

export function LiveResult({ packet, edit, onReference, onFollowUp }: { packet: ChatResult; edit: () => void; onReference: (chunk: string, trigger: HTMLElement, component?: string) => void; onFollowUp?: (question: string) => void }) {
  const result = packet.result;
  const route = result?.routing;
  const wording = packet.normalization;
  const generated = ["generated", "partially_generated"].includes(packet.explanation.status) && packet.explanation.citations_checked && packet.explanation.automated_support_checked
    || packet.explanation.status === "verified" && packet.explanation.legal_support_verified === true;
  const clarification = packet.clarification_follow_up?.question ?? route?.clarification_question ?? wording?.clarification_question;
  const scopeLabel = (scope: string) => ({ fully_supported: "Within project topics", partially_supported: "Partly within project topics", unsupported: "Outside project topics" }[scope] ?? labelName(scope));
  return <div className="live-result">
    {packet.safety_notice && <section className="notice notice-caution safety-notice"><h3>{packet.safety_notice.heading}</h3><p>{packet.safety_notice.text}</p><a href="tel:911" className="text-link touch-link">Call 911</a><a href={packet.safety_notice.source_url} className="text-link touch-link" target="_blank" rel="noopener noreferrer">Official emergency directory</a></section>}
    {wording?.normalized_question_text && <div className="notice"><h3>Interpreted wording</h3><p>{wording.normalized_question_text}</p><p className="metadata">Check that this preserves your meaning. The labels below use this wording.</p></div>}
    {packet.guidance_context && <p className="scope-context"><strong>General information about private-sector employment.</strong> {packet.guidance_context.note}</p>}
    {!generated && packet.response && <section className="generated-explanation response-summary" aria-label="Response">
      <h3>{packet.response.heading}</h3>
      {packet.response.paragraphs.map((paragraph, i) => <p key={i}>{paragraph}</p>)}
      {!!packet.response.quotes.length && <details className="recorded-passages"><summary>Read the recorded source passages</summary>{packet.response.quotes.map(quote => <figure className="response-quote" key={quote.chunk_id}>
        <figcaption><button type="button" className="text-link touch-link" onClick={event => onReference(quote.chunk_id, event.currentTarget, quote.component_id)}>{quote.citation_display}</button></figcaption>
        <blockquote>{quote.quote}</blockquote><p className="metadata">{quote.complete_provision ? "Complete stored provision." : "Recorded excerpt. Open the reference for the complete provision and its exceptions."} Current applicability remains under review.</p>
      </figure>)}</details>}
      <p className="metadata">{packet.response.ai_generated ? "AI response about your situation and the available next step. Factual context checked; this does not establish a legal answer." : `Local response${packet.response.quotes.length ? " with recorded source text" : ""}. No live AI explanation was used.`}</p>
      {packet.explanation.reason === "provider_unavailable" && <button type="button" className="text-link touch-link" onClick={edit}>Use this question again</button>}
    </section>}
    {!generated && !packet.response && <h3 className="live-route">{routeName(route?.routing_action)}</h3>}
    {route && route.routing_action !== "clarify" && !generated && !packet.response && <dl className="live-labels">
      <div><dt>{route.routing_action === "clarify" ? "Tentative topic" : "Topic"}</dt><dd>{labelName(route.predicted_primary)} <span>{(route.primary_confidence * 100).toFixed(1)}% confidence</span></dd></div>
      <div><dt>Topic coverage</dt><dd>{scopeLabel(route.predicted_scope)} <span>{(route.scope_confidence * 100).toFixed(1)}% label confidence</span></dd></div>
    </dl>}
    {(!result || route?.routing_action === "clarify") && !packet.response && <section className="notice notice-caution"><h3>Help clarify the question</h3><p>{clarification || "Please retype the concern using fuller words and include the relevant details."}</p><p className="metadata">Edit the full question to include these details. Each submission is checked on its own.</p><button type="button" className="text-link touch-link" onClick={edit}>Edit this question</button></section>}
    {route?.routing_action === "refer_out_of_scope" && !packet.response && <p>This concern is outside the selected labor and consumer topics. See <Link to="/about">scope &amp; limitations</Link> for what is covered.</p>}
    {!!result?.excluded_components.length && <section className="notice notice-caution"><h3>Concerns outside coverage</h3><ul>{result.excluded_components.map((c, i) => <li key={i}>{c.text}</li>)}</ul><p>These parts were excluded from retrieval.</p></section>}
    {generated && <GeneratedExplanation explanation={packet.explanation} components={result?.components} onReference={onReference} />}
    {generated && !!packet.explanation.unanswered_components?.length && <section className="notice notice-caution" aria-label="Parts not explained">
      <h3>Parts I couldn’t explain</h3>
      <p>The explanation above covers only the supported parts. Here is what is still missing.</p>
      <ul>{packet.explanation.unanswered_components.map(concern => <li key={concern.component_id}><strong>{concern.query}</strong><p>{concern.reason === "related_authority_missing" ? "A required related source is unavailable or awaiting review." : concern.reason === "source_wording_requires_review" ? "The recorded wording needs review before it can support an explanation." : concern.reason === "claim_support_failed" ? "The draft for this concern did not pass the source-support check." : "The current records do not contain enough eligible evidence to explain this concern."}</p></li>)}</ul>
      {!!packet.response?.quotes.length && <details className="source-checks"><summary>Recorded passages for the remaining concerns</summary><p className="metadata">These are locally matched excerpts, without an AI interpretation. Open a reference to read its conditions and exceptions.</p>{packet.response.quotes.map(quote => <figure className="response-quote" key={`${quote.component_id}-${quote.chunk_id}`}><figcaption><button type="button" className="text-link touch-link" onClick={event => onReference(quote.chunk_id, event.currentTarget, quote.component_id)}>{quote.citation_display}</button></figcaption><blockquote>{quote.quote}</blockquote></figure>)}</details>}
      <p className="metadata">A missing explanation can reflect a source or checking limit. Rewording a clear question will not add a missing legal source.</p>
      <button type="button" className="text-link touch-link" onClick={edit}>Review the full question</button>
    </section>}
    {result?.components.some(c => c.candidates.some(h => h.explanation_restriction)) && <p className="metadata">A recorded passage has a wording discrepancy and was excluded from AI explanations. Open its reference for details.</p>}
    {!!result?.components.length && !generated && !packet.response && <section className="notice"><h3>{result.components.some(c => c.candidates.length) ? "Provisions found for inspection" : "No eligible provisions found"}</h3><p>Open a reference to inspect its complete stored text.</p><p><strong>{packet.explanation.reason === "local_only" ? "Local-only analysis." : "Explanation withheld."}</strong> {explanationMessage(packet.explanation.reason, packet.explanation.failure_code, packet.explanation.validation_failure)}</p>{packet.explanation.reason === "provider_unavailable" && !["daily_provider_limit", "provider_auth_failed", "model_pricing_not_configured"].includes(packet.explanation.failure_code ?? "") && <button type="button" className="text-link touch-link" onClick={edit}>Use this question again</button>}</section>}
    {packet.response?.follow_up && <section className="response-follow-up"><h3>A detail that would help</h3><p>{packet.response.follow_up}</p>
      {!!packet.response.follow_up_options.length && onFollowUp ? <><p className="metadata">Choose a type to add it to your question, then press Ask.</p><div className="follow-up-options">{packet.response.follow_up_options.map(option => <button type="button" className="secondary-button" key={option.label} onClick={() => onFollowUp(option.question_text)}>{option.label}</button>)}</div></> : <button type="button" className="text-link touch-link" onClick={edit}>Add this detail to my question</button>}
    </section>}
    {!!packet.source_review_notices?.length && <section className="notice notice-caution"><h3>A required source needs review</h3><ul>{packet.source_review_notices.map(source => <li key={source.document_id}>{source.title}. {safeUrl(source.official_url) && <a className="text-link touch-link" href={safeUrl(source.official_url)} target="_blank" rel="noopener noreferrer">Inspect the official record</a>}</li>)}</ul><p className="metadata">These records are not being used as approved answer evidence.</p></section>}
    {!!packet.referrals?.length && <details className="live-referrals"><summary>Where to ask for assistance</summary><p className="metadata">Recorded agency information. The agency determines jurisdiction and filing requirements.</p><ul>{packet.referrals.map(referral => <li key={referral.id}><h4>{referral.agency}</h4><p>{referral.service}</p><div className="referral-links">{safeUrl(referral.contact.portal_url) && <a className="text-link touch-link" href={safeUrl(referral.contact.portal_url)} target="_blank" rel="noopener noreferrer">Service portal</a>}{safeUrl(referral.information_url) && <a className="text-link touch-link" href={safeUrl(referral.information_url)} target="_blank" rel="noopener noreferrer">Official information</a>}{referral.contact.email && /^[\w.+-]+@[\w.-]+\.[A-Za-z]+$/.test(referral.contact.email) && <a className="text-link touch-link" href={`mailto:${referral.contact.email}`}>{referral.contact.email}</a>}{referral.contact.phone && /^[\d+() -]+$/.test(referral.contact.phone) && <a className="text-link touch-link" href={`tel:${referral.contact.phone.replace(/[^\d+]/g, "")}`}>{referral.contact.phone}</a>}</div><p className="metadata">Checked {referral.checked_on}. {referral.complete ? "See the official page for current service requirements." : "Unconfirmed contact details are withheld."}</p></li>)}</ul></details>}
    {packet.privacy?.redacted && <p className="metadata">Known personal identifiers were removed locally before analysis. Automated redaction can miss details; use fictional examples.</p>}
    {packet.history?.saved && <p className="metadata">Saved on this device. <Link to="/history">Open history</Link>.</p>}
    {packet.history?.error && <p className="metadata" role="status">{packet.history.error}</p>}
    <details className="live-diagnostics"><summary>How this question was checked</summary><dl className="live-labels">
      {route && <><div><dt>{route.routing_action === "clarify" ? "Tentative topic" : "Topic"}</dt><dd>{labelName(route.predicted_primary)} · {(route.primary_confidence * 100).toFixed(1)}% label confidence</dd></div><div><dt>Topic coverage</dt><dd>{scopeLabel(route.predicted_scope)} · {(route.scope_confidence * 100).toFixed(1)}% label confidence</dd></div></>}
      <div><dt>Wording check</dt><dd>{wording?.status ?? "Local only"} · {wording?.llm_calls ?? 0} LLM calls</dd></div>
      <div><dt>Explanation</dt><dd>{packet.explanation.reason.replaceAll("_", " ")} · {packet.explanation.llm_calls} LLM calls</dd></div>
      {packet.explanation.status === "partially_generated" && <div><dt>Explanation coverage</dt><dd>{packet.explanation.claims.length} of {result?.components.length ?? 0} concerns explained by AI</dd></div>}
      {packet.response && <div><dt>Response shown</dt><dd>{packet.response.kind === "ai_guidance" ? "AI situation response; no new legal rules" : packet.response.ai_generated ? packet.explanation.status === "partially_generated" ? "Partial AI explanation" : "Checked AI explanation" : packet.response.quotes.length ? "Local response with source excerpts" : "Local response"}</dd></div>}
      {packet.response?.generation && <div><dt>Situation response</dt><dd>{packet.response.generation.reason.replaceAll("_", " ")} · {packet.response.generation.llm_calls} LLM calls</dd></div>}
      {packet.situation_context && <div><dt>Question context</dt><dd>The scenario and its follow-up were searched together. Original classifier fragments: {packet.situation_context.original_components.map(c => c.query).join(" / ")}</dd></div>}
      {route?.reason === "explicit_component_scopes_require_evidence" && <div><dt>Why these parts were searched</dt><dd>Each separated concern matches a defined project category. The excluded concern was kept out of retrieval; the label confidence is unchanged.</dd></div>}
      {packet.guidance_context?.classification_is_conditional && <div><dt>Original classification</dt><dd>{labelName(packet.guidance_context.original_routing.predicted_primary)} · {packet.guidance_context.original_routing.reason.replaceAll("_", " ")}. Source search uses the stated private-sector assumption.</dd></div>}
      {packet.search_help && <div><dt>Additional search wording</dt><dd>{packet.search_help.query}</dd></div>}
      {packet.explanation.revision_attempted && <div><dt>Draft correction</dt><dd>One correction attempted</dd></div>}
      {packet.explanation.failure_code && <div><dt>AI service detail</dt><dd>{packet.explanation.failure_code.replaceAll("_", " ")}</dd></div>}
      {packet.explanation.validation_failure && <div><dt>Draft issue</dt><dd>{packet.explanation.validation_failure.replaceAll("_", " ")}</dd></div>}
      <div><dt>Support check</dt><dd>{packet.explanation.automated_support_checked ? "Automated check passed; independent legal review pending" : packet.explanation.status === "verified" ? "Recorded legal review passed" : packet.explanation.reason === "provider_unavailable" ? "Not completed — AI service unavailable" : packet.explanation.llm_calls < 2 ? "Not run — no validated draft was ready" : "Automated check did not approve an explanation"}</dd></div>
      <div><dt>Analysis time</dt><dd>{Math.round(packet.total_query_ms)} ms</dd></div>
    </dl><p className="metadata">Topic coverage describes the project's subject areas; it does not establish entitlement or source support. Confidence measures label certainty. A new question has no accuracy or F1 score without an expected label. <Link to="/performance">View recorded evaluation metrics</Link>.</p></details>
  </div>;
}

function explanationMessage(reason: string, failure?: string, validation?: string) {
  if (reason === "local_only") return "AI explanations are off. Classification and source retrieval ran locally.";
  if (failure === "daily_provider_limit") return "The daily AI-use limit has been reached. You can continue inspecting sources locally.";
  if (failure === "provider_circuit_open") return "The AI service has had repeated failures. Please wait a minute or inspect the sources.";
  if (failure === "provider_rate_limited") return "The AI service is busy. Please wait before trying again.";
  if (failure === "provider_auth_failed") return "The AI service rejected the server's credentials. The operator needs to check the API configuration.";
  if (failure && /^provider_http_5\d\d$/.test(failure)) return "The AI service returned a temporary server error. You can retry the same question; the sources remain available.";
  if (failure && /^provider_http_\d{3}$/.test(failure)) return "The AI service rejected the explanation request. The operator needs to inspect the service detail below.";
  if (failure === "provider_incomplete_output") return "The AI service stopped before finishing its draft. You can retry the same question; the sources remain available.";
  if (failure === "provider_invalid_response") return "The AI service returned a response the app could not validate. The sources remain available.";
  if (reason === "claim_support_failed" || reason === "support_check_unavailable") return "The proposed explanation did not clear the source-support check. Inspect the sources; an unsupported draft has not been shown.";
  if (reason === "provider_unavailable") return "The AI service could not complete the explanation. Your classification and sources are still available.";
  if (reason === "no_supported_explanation") return "The AI could not produce an explanation supported by the supplied sources. The references remain available for inspection.";
  if (reason === "citation_validation_failed" && validation === "incomplete_concerns") return "The draft did not cover every identified concern. It was withheld to avoid showing an incomplete answer.";
  if (reason === "citation_validation_failed" && validation === "numeric_detail_not_in_source") return "The draft included a number that could not be matched to its cited source. It was withheld.";
  if (reason === "citation_validation_failed") return "The proposed explanation did not pass citation or claim checks. It has been withheld.";
  if (reason === "related_authority_missing") return "A required related source is unavailable or awaiting review.";
  if (reason === "source_wording_requires_review") return "The available passage has conflicting wording and needs source review before it can support an explanation.";
  if (reason === "safety_assistance_first") return "Please attend to the immediate safety concern first.";
  return "The available source context has not cleared the current explanation checks. Inspect the records or add relevant facts to the question.";
}

const safeUrl = (value: string | null) => { try { const url = new URL(value ?? ""); return ["https:", "http:"].includes(url.protocol) ? url.href : undefined; } catch { return undefined; } };
export function LiveCitationCard({ reference, number, id, expanded, onToggle, quotes = [] }: {
  reference: LiveReference; number: number; id: string; expanded: boolean; onToggle: () => void; quotes?: string[];
}) {
  const { hit, concern } = reference;
  const gate = concern.evidence_gates.find(g => g.chunk_id === hit.chunk_id);
  const url = safeUrl(hit.official_source_url || hit.retrieval_url);
  return <section className="reference-block" id={id} tabIndex={-1} data-expanded={expanded}>
    <button type="button" className="reference-block-toggle" aria-expanded={expanded} aria-controls={`${id}-body`} onClick={onToggle}>
      <span className="reference-number">{number}</span><span><span className="reference-block-title">{hit.citation_label ?? hit.citation_display}</span><span className="metadata">{hit.document_title}</span></span><ChevronDown size={17} aria-hidden="true" />
    </button>
    <p className="reference-status is-restricted">Recorded source · current applicability unreviewed</p>
    {hit.explanation_restriction && <p className="metadata">{hit.explanation_restriction}</p>}
    <div id={`${id}-body`} className="reference-content" hidden={!expanded}>
      <p className="metadata">For: {concern.query}</p>
      <dl className="live-labels"><div><dt>Recorded status</dt><dd>{hit.legal_status}</dd></div><div><dt>Status checked</dt><dd>{hit.status_as_of}</dd></div><div><dt>Search ranking</dt><dd>{hit.score.toFixed(4)} · not confidence</dd></div></dl>
      <details className="source-checks"><summary>Use restrictions and source checks</summary><p className="metadata">Recorded dates do not prove current applicability.</p>
        <ul>{gate?.reasons.map(reason => <li key={reason}>{reason === "scoped_currentness_review_missing" ? "A current-source review for this concern is missing." : reason.replaceAll("_", " ")}</li>)}</ul>
        <pre className="source-metadata">{JSON.stringify({ conditions: hit.conditions, relationships: hit.legal_relationships, freshness: hit.freshness_rule }, null, 2)}</pre>
      </details>
      <h3>Complete stored provision</h3>{quotes.length > 0 && <p className="metadata">Highlighted passages were used in this response.</p>}<p className="source-text">{markedSource(hit.parent_text, quotes)}</p>
      <p className="metadata">{hit.provision_id}</p>
      {url && <a className="text-link touch-link" href={url} target="_blank" rel="noopener noreferrer">Open recorded source<ExternalLink size={14} aria-hidden="true" /></a>}
    </div>
  </section>;
}

function markedSource(text: string, quotes: string[]) {
  const spans = quotes.map(quote => ({ start: text.indexOf(quote), end: text.indexOf(quote) + quote.length })).filter(s => s.start >= 0 && s.end > s.start).sort((a, b) => a.start - b.start);
  const merged: { start: number; end: number }[] = [];
  for (const span of spans) { const last = merged[merged.length - 1]; if (last && span.start <= last.end) last.end = Math.max(last.end, span.end); else merged.push({ ...span }); }
  let cursor = 0;
  const parts = merged.flatMap(span => { const before = text.slice(cursor, span.start); cursor = span.end; return [before, <mark key={span.start}>{text.slice(span.start, span.end)}</mark>]; });
  return [...parts, text.slice(cursor)];
}
