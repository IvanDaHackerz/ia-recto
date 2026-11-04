import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen, Plus, Send } from "lucide-react";
import { answerScenarios, type AnswerScenario } from "../data/answers";
import { conversations, getConversationTurns } from "../data/conversations";
import { libraryDocuments } from "../data/library";
import { topics } from "../data/topics";
import { DomainTag } from "../components/DomainTag";
import { CitationCard } from "../components/CitationCard";
import { OutOfScopeNotice } from "../components/OutOfScopeNotice";
import { ExampleQuestion } from "../components/ExampleQuestion";
import { apiRequest, cancelQuery, fetchApi, initialReferenceIndex, isChatResult, referencesFor, type ChatResult, type LiveReference, type SavedConversation } from "../data/api";
import { useSettings } from "../context/settingsState";
import { PrivacyControls } from "../components/PrivacyControls";
import { LiveResult, LiveCitationCard } from "../components/LiveResult";

type ChatTurn = { query: string; scenario?: AnswerScenario; packet?: ChatResult; pending?: boolean; error?: string };
const EXAMPLES = answerScenarios.slice(0, 3);
const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const sourceQuotes = (packet: ChatResult | undefined, reference: LiveReference) => [
  ...packet?.explanation.claims.filter(c => !c.component_id || c.component_id === reference.concern.component_id).flatMap(c => c.citations.filter(q => q.chunk_id === reference.hit.chunk_id).map(q => q.quote)) ?? [],
  ...packet?.response?.quotes.filter(q => q.component_id === reference.concern.component_id && q.chunk_id === reference.hit.chunk_id).map(q => q.quote) ?? [],
];
export function ChatPage() {
  const { conversationId, savedId } = useParams();
  const { useAI, saveHistory } = useSettings();
  const navigate = useNavigate();
  const conversation = conversations.find(c => c.id === conversationId);
  const [turns, setTurns] = useState<ChatTurn[]>(() => conversation ? getConversationTurns(conversation).map(scenario => ({ query: scenario.query, scenario })) : []);
  const [value, setValue] = useState("");
  const [announcement, setAnnouncement] = useState("");
  const [savedLoading, setSavedLoading] = useState(Boolean(savedId));
  const [savedError, setSavedError] = useState("");
  const [activeTurn, setActiveTurn] = useState(0);
  const [activeCitation, setActiveCitation] = useState<number | null>(0);
  const [mobileView, setMobileView] = useState<"chat" | "sources">("chat");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const latestRef = useRef<HTMLElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sourceReturn = useRef<HTMLElement | null>(null);
  const submitted = useRef(false);
  const questionFeedback = useRef<Animation | null>(null);
  const request = useRef<AbortController | null>(null);
  const requestId = useRef<string | null>(null);
  const savedConversation = useRef<string | undefined>(savedId);
  const pending = turns.some(t => t.pending);
  const selected = turns[activeTurn];
  const liveReferences = referencesFor(selected?.packet);
  const citations = selected?.scenario?.citations ?? [];
  useEffect(() => {
    if (!submitted.current) return;
    latestRef.current?.focus({ preventScroll: true });
    latestRef.current?.scrollIntoView({ behavior: reducedMotion() ? "instant" : "smooth", block: "start" });
  }, [turns.length]);
  useEffect(() => () => { questionFeedback.current?.cancel(); if (requestId.current) void cancelQuery(requestId.current); request.current?.abort(); }, []);
  useEffect(() => {
    if (!savedId) return;
    const controller = new AbortController();
    apiRequest<SavedConversation>(`history/${savedId}`, { signal: controller.signal }).then(data => {
      if (controller.signal.aborted) return;
      if (!data.conversation.turns.every(turn => isChatResult(turn.packet))) throw new Error("This saved result is incompatible with the current viewer.");
      setTurns(data.conversation.turns.map(turn => ({ query: turn.packet.original_question_text, packet: turn.packet })));
      setActiveTurn(0); setActiveCitation(initialReferenceIndex(data.conversation.turns[0]?.packet)); savedConversation.current = savedId; setSavedLoading(false);
    }).catch(error => { if (!controller.signal.aborted) { setSavedError(error instanceof Error ? error.message : "Saved questions are unavailable."); setSavedLoading(false); } });
    return () => controller.abort();
  }, [savedId]);
  function pick(query: string) {
    setValue(query);
    setAnnouncement("Example added to your question field. You can edit it before asking.");
    const input = inputRef.current;
    input?.focus({ preventScroll: true });
    questionFeedback.current?.cancel();
    if (input && typeof input.animate === "function" && !reducedMotion()) {
      const colors = getComputedStyle(input);
      questionFeedback.current = input.animate([
        { backgroundColor: colors.getPropertyValue("--color-primary-wash"), borderColor: colors.getPropertyValue("--color-primary") },
        { backgroundColor: colors.getPropertyValue("--color-paper-raised"), borderColor: colors.getPropertyValue("--color-border-strong") },
      ], { duration: 520, easing: "cubic-bezier(0.16, 1, 0.3, 1)" });
    }
  }
  function questionKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey
      || event.nativeEvent.isComposing || event.nativeEvent.keyCode === 229) return;
    event.preventDefault();
    if (!event.repeat) event.currentTarget.form?.requestSubmit();
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const query = value.trim();
    if (!query || request.current || conversation) return;
    const controller = new AbortController(); request.current = controller;
    const id = crypto.randomUUID(); requestId.current = id;
    const index = turns.length;
    const timeout = window.setTimeout(() => { void cancelQuery(id); controller.abort(); }, 65000);
    submitted.current = true;
    setActiveTurn(index); setActiveCitation(0); setMobileView("chat");
    setTurns(previous => [...previous, { query, pending: true }]);
    setAnnouncement("Checking the question and searching recorded provisions."); setValue("");
    try {
      const packet = await fetchApi<ChatResult>("chat", controller.signal, query, { request_id: id, use_ai: useAI, save_history: saveHistory, ...(savedConversation.current ? { conversation_id: savedConversation.current } : {}) });
      if (request.current !== controller) return;
      if (packet.history?.saved) savedConversation.current = packet.history.conversation_id;
      setTurns(previous => previous.map((turn, i) => i === index ? { query, packet } : turn));
      setActiveCitation(initialReferenceIndex(packet));
      setAnnouncement("Analysis ready. Open references to inspect any retrieved provisions.");
    } catch (error) {
      if (request.current !== controller) return;
      const message = controller.signal.aborted ? "The request stopped. You can edit or retry the question." : error instanceof Error ? error.message : "Could not reach the local backend. Please retry.";
      setTurns(previous => previous.map((turn, i) => i === index ? { query, error: message } : turn)); setAnnouncement(message);
    } finally {
      window.clearTimeout(timeout); if (request.current === controller) { request.current = null; requestId.current = null; }
    }
  }
  function newChat() {
    if (requestId.current) void cancelQuery(requestId.current);
    request.current?.abort(); request.current = null; requestId.current = null; savedConversation.current = undefined;
    submitted.current = false;
    setTurns([]); setValue(""); setActiveTurn(0); setActiveCitation(0); setMobileView("chat");
    setAnnouncement("Current view cleared. Previously saved questions remain in History.");
    if (conversationId || savedId) navigate("/");
    else {
      inputRef.current?.focus({ preventScroll: true });
      scrollRef.current?.scrollTo({ top: 0, behavior: "instant" });
    }
  }
  function stopRequest() { if (requestId.current) void cancelQuery(requestId.current); request.current?.abort(); }
  function showSources(turnIndex: number, citationIndex: number, trigger: HTMLElement) {
    sourceReturn.current = trigger;
    setActiveTurn(turnIndex); setActiveCitation(citationIndex); setMobileView("sources");
    requestAnimationFrame(() => {
      const block = document.getElementById(`reference-${turnIndex}-${citationIndex}`);
      block?.focus({ preventScroll: true });
      block?.scrollIntoView({ behavior: reducedMotion() ? "instant" : "smooth", block: "start" });
    });
  }
  function returnToChat() {
    setMobileView("chat");
    requestAnimationFrame(() => (sourceReturn.current ?? inputRef.current)?.focus({ preventScroll: true }));
  }
  if (conversationId && !conversation) return <div className="reading-page workspace-not-found"><h1>Sample conversation not found</h1><p>This link does not match a sample conversation.</p><Link className="text-link touch-link" to="/history">Choose a sample conversation</Link></div>;
  if (savedLoading) return <div className="reading-page workspace-not-found" role="status"><h1>Loading saved questions…</h1></div>;
  if (savedError) return <div className="reading-page workspace-not-found"><h1>Saved questions unavailable</h1><p role="alert">{savedError}</p><Link className="text-link touch-link" to="/history">Return to History</Link></div>;
  return <div className="research-workspace" data-mobile-view={mobileView}>
    <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">{announcement}</div>
    <header className="workspace-toolbar">
      <h1>{conversation ? "Archived sample conversation" : "Ask about your rights"}</h1>
      <div className="workspace-tools">
        <button type="button" className="secondary-button sources-toggle" aria-pressed={mobileView === "sources"} onClick={event => {
          if (mobileView === "sources") returnToChat();
          else { sourceReturn.current = event.currentTarget; setMobileView("sources"); }
        }}><BookOpen size={17} aria-hidden="true" />Sources{(citations.length + liveReferences.length) ? ` (${citations.length + liveReferences.length})` : ""}</button>
        {turns.length > 0 && <button type="button" className="secondary-button new-question" aria-label="New question" onClick={newChat}><Plus size={17} aria-hidden="true" /><span>New question</span></button>}
      </div>
    </header>
    <div className="workspace-body">
      <div className="conversation-column">
        <div ref={scrollRef} className="conversation-scroll" role="region" aria-label="Conversation" tabIndex={0}>
          {turns.length > 0 ? <div className="conversation-turns">{turns.map((turn, index) => <article key={index} ref={index === turns.length - 1 ? latestRef : undefined} tabIndex={-1} className="conversation-turn" aria-label={`Response ${index + 1}`}>
            <div className="turn-heading"><span className="metadata">Question {index + 1}</span><h2 className="question-heading">{turn.query}</h2></div>
            {savedId && turn.packet && <p className="metadata">Saved analysis · recorded {turn.packet.result?.as_of ?? "date unavailable"}. Sources and explanations are not rechecked when opened.</p>}
            {turn.pending ? <section className="notice" role="status"><h3>Preparing your response…</h3><p>{useAI ? "Checking the concern, finding sources and checking an explanation when supported." : "Checking the concern and searching recorded sources locally."}</p><button type="button" className="text-link touch-link" onClick={stopRequest}>Stop request</button></section>
            : turn.error ? <section className="notice notice-caution" role="alert"><h3>Analysis unavailable</h3><p>{turn.error}</p><button type="button" className="text-link touch-link" onClick={() => pick(turn.query)}>Edit or retry this question</button></section>
            : turn.packet ? <><LiveResult packet={turn.packet} edit={() => pick(turn.query)} onFollowUp={pick} onReference={(chunk, trigger, component) => { const position = referencesFor(turn.packet).findIndex(r => r.hit.chunk_id === chunk && (!component || r.concern.component_id === component)); if (position >= 0) showSources(index, position, trigger); }} />
              {!!referencesFor(turn.packet).length && <div className="response-references"><p className="metadata">Retrieved candidates</p><div>{referencesFor(turn.packet).map(({ hit }, citationIndex) => <button key={`${citationIndex}-${hit.chunk_id}`} type="button" className="reference-chip" onClick={event => showSources(index, citationIndex, event.currentTarget)}><span className="reference-number">{citationIndex + 1}</span>{hit.citation_label ?? hit.citation_display}</button>)}</div></div>}
            </> : turn.scenario ? <>
              <ScenarioTurn scenario={turn.scenario} />
              {turn.scenario.citations.length > 0 && <div className="response-references" aria-label={`References for response ${index + 1}`}><p className="metadata">Source references</p><div>{turn.scenario.citations.map((citation, citationIndex) => <button key={citation.id} className="reference-chip" type="button" onClick={event => showSources(index, citationIndex, event.currentTarget)} aria-label={`Open reference ${citationIndex + 1}, ${citation.citation}, for response ${index + 1}`}><span className="reference-number">{citationIndex + 1}</span>{citation.citation}</button>)}</div></div>}
            </> : <section className="notice notice-caution">
              <h3>No analysis is available</h3><p>This question has not received a usable result. Edit it or try again.</p>
              <p>Edit your question or load a sample below.</p>
              <button type="button" className="text-link touch-link" onClick={() => pick(turn.query)}>Edit this question</button>
              <ul className="example-list question-rows">{EXAMPLES.map(example => <li key={example.id}><ExampleQuestion example={example} selected={value === example.query} onPick={pick} /></li>)}</ul>
            </section>}
          </article>)}</div> : <div className="workspace-welcome">
            <p className="welcome-copy">A place to understand your rights.<br /><span>Start with a Philippine labor or consumer concern.</span></p>
            <section className="examples"><h2>Try an example</h2><p className="metadata examples-help">Choose a question, edit it if needed, then ask the live classifier.</p><ul className="example-list question-rows">{EXAMPLES.map(example => <li key={example.id}><ExampleQuestion example={example} selected={value === example.query} onPick={pick} /></li>)}</ul>
              <details className="extra-examples"><summary>Explore scope and evidence limits</summary><ul className="example-list">{answerScenarios.slice(3).map(example => <li key={example.id}><button className="text-link touch-link" type="button" onClick={() => pick(example.query)}>{example.query}</button></li>)}</ul></details>
            </section>
          </div>}
        </div>
        {conversation ? <div className="workspace-composer"><p className="metadata">Archived design examples. These scripted answers were not generated or verified by the current backend.</p><button type="button" className="primary-button" onClick={newChat}>Start a live question</button></div> : <form onSubmit={submit} className="composer workspace-composer">
          <label htmlFor="query">{turns.length ? "Try another question" : "Your question"}</label>
          <div className="query-control"><textarea ref={inputRef} id="query" value={value} onChange={event => setValue(event.target.value)} onKeyDown={questionKeyDown} rows={2} maxLength={8000}
            placeholder="Ask about a labor or consumer concern…" aria-describedby="query-help" />
            <button className="primary-button" aria-label="Ask" disabled={!value.trim() || pending} type="submit"><Send size={17} aria-hidden="true" /><span>{pending ? "Checking…" : "Ask"}</span></button></div>
          <details className="composer-options"><summary>AI &amp; saving · {useAI ? "AI on" : "Local only"} · {saveHistory ? "Saving on" : "Saving off"}</summary><PrivacyControls /></details>
          <p id="query-help" className="metadata">Enter to send. Shift+Enter for a new line. Use fictional details. Each question is checked independently; include the complete concern and any requested facts. <Link to="/about">Scope &amp; privacy</Link></p>
        </form>}
      </div>
      <aside className="sources-panel" aria-label="Source references">
        <header className="sources-panel-heading"><div><h2>Source references</h2><p className="metadata">{selected?.pending ? "Preparing references…" : selected ? `For response ${activeTurn + 1} · ${citations.length + liveReferences.length} reference${citations.length + liveReferences.length === 1 ? "" : "s"}` : "The provisions retrieved for your question"}</p></div><button type="button" className="text-link touch-link sources-back" onClick={returnToChat}><ArrowLeft size={16} aria-hidden="true" />Back to chat</button></header>
        <div className="sources-scroll" role="region" aria-label="Reference blocks" tabIndex={0}>
          {selected?.pending ? <div className="source-panel-empty"><BookOpen size={28} strokeWidth={1.4} aria-hidden="true" /><h3>Preparing source references</h3><p>Your question is being checked. References will appear here when the analysis finishes.</p></div> : liveReferences.length > 0 ? <><p className="metadata reference-disclosure">Inspect the recorded source text here. Current legal applicability remains under review.</p><ol className="reference-blocks">{liveReferences.map((reference, index) => <li key={`${activeTurn}-${index}`}><LiveCitationCard reference={reference} number={index + 1} id={`reference-${activeTurn}-${index}`} expanded={activeCitation === index} onToggle={() => setActiveCitation(activeCitation === index ? null : index)} quotes={sourceQuotes(selected?.packet, reference)} /></li>)}</ol></> : citations.length > 0 ? <><p className="metadata reference-disclosure">References for a scripted example. Inspect source text and answer-use restrictions below.</p><ol className="reference-blocks">{citations.map((citation, index) => <li key={`${activeTurn}-${citation.id}`}><CitationCard citation={citation} number={index + 1} id={`reference-${activeTurn}-${index}`} expanded={activeCitation === index} onToggle={() => setActiveCitation(activeCitation === index ? null : index)} /></li>)}</ol></> : <>
            <div className="source-panel-empty"><BookOpen size={28} strokeWidth={1.4} aria-hidden="true" /><h3>{selected ? "No supporting citations" : "Follow the reference trail"}</h3><p>{!selected ? "Ask a question to see retrieved provisions here. Open a block to inspect the complete stored text." : !selected.scenario ? "No source references were returned for this response. Check the response for a clarification, scope boundary or source limitation." : selected.scenario.evidenceStatus === "insufficient" ? "No provision is mapped to this example. Topic coverage alone is not enough to answer." : "No legal answer or supporting citations are provided for this excluded topic."}</p><Link className="text-link touch-link citation-jump" to="/library">Browse the Library</Link></div>
            {!turns.length && <section className="workspace-topics"><h3>Explore by topic</h3><p className="metadata">{libraryDocuments.length} recorded documents. A local snapshot, not a live search index.</p><ul>{topics.map(topic => <li key={topic.id}><Link className="touch-link" to={`/library?domain=${topic.domain}&q=${encodeURIComponent(topic.searchTerm)}`}>{topic.label}</Link></li>)}</ul></section>}
          </>}
        </div>
      </aside>
    </div>
  </div>;
}
function ScenarioTurn({ scenario }: { scenario: AnswerScenario }) {
  const insufficient = scenario.evidenceStatus === "insufficient";
  return <>
    <DomainTag domain={scenario.domain} scope={scenario.scope} />
    <p className="metadata sample-caption">Illustrative response. Topic coverage is not a citation-verification result.</p>
    <div className="answer-copy">
      {scenario.scope === "unsupported" || insufficient ? <OutOfScopeNotice message={scenario.declineMessage ?? "No substantive answer is available."} evidenceMissing={insufficient} referralIds={scenario.referralIds} /> : <>
        {scenario.scope === "partially_supported" && <h3>Within scope: {scenario.supportedDomains.join(" and ")}</h3>}
        <p className="answer-text">{scenario.supportedAnswer}</p>
        {scenario.unsupportedTopic && <OutOfScopeNotice message={scenario.unsupportedTopic} referralIds={scenario.referralIds} />}
        {!scenario.unsupportedTopic && scenario.referralIds && <OutOfScopeNotice title="Need case-specific assistance?" message="Use the recorded agency links below." referralIds={scenario.referralIds} />}
      </>}
    </div>
  </>;
}
