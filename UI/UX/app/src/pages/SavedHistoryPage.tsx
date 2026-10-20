import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest, type HistoryList, type SavedConversation } from "../data/api";
import { conversations, getConversationTurns } from "../data/conversations";
import { DomainTag } from "../components/DomainTag";

function checkedList(value: HistoryList): HistoryList {
  if (!value || typeof value.available !== "boolean" || !Array.isArray(value.conversations)
    || !value.conversations.every(row => row && /^[a-f0-9]{32}$/.test(row.id) && typeof row.title === "string" && Number.isInteger(row.turns) && typeof row.updated_at === "string"))
    throw new Error("Saved questions could not be read. Restart the local API and try again.");
  return value;
}

export function HistoryPage() {
  const [data, setData] = useState<HistoryList | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    apiRequest<HistoryList>("history", { signal: controller.signal }).then(checkedList).then(value => { if (!controller.signal.aborted) setData(value); }).catch(err => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "History could not be loaded."); });
    return () => controller.abort();
  }, []);
  async function remove(id: string) {
    setBusy(true); setError("");
    try {
      await apiRequest(id === "all" ? "history" : `history/${id}`, { method: "DELETE" });
      setData(checkedList(await apiRequest<HistoryList>("history"))); setConfirmation(null);
      setMessage(id === "all" ? "All saved questions for this browser were deleted." : "Saved questions deleted.");
      requestAnimationFrame(() => heading.current?.focus());
    } catch (err) { setError(err instanceof Error ? err.message : "Could not delete the saved questions."); }
    finally { setBusy(false); }
  }
  async function download(id: string) {
    setError("");
    try {
      const result = await apiRequest<SavedConversation>(`history/${id}/export`);
      const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = `recto-questions-${id}.json`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000); setMessage("Export prepared. The download contains your saved questions and responses.");
    } catch (err) { setError(err instanceof Error ? err.message : "The export could not be prepared."); }
  }
  return <div className="reading-page">
    <header className="page-heading"><div><h1 ref={heading} tabIndex={-1}>Saved questions</h1><p>Return to questions you chose to save. New questions stay temporary unless saving is switched on.</p></div></header>
    <p className="metadata">Encrypted on this device for {data?.retention_days ?? 30} days. Use the same browser profile to return. Opening an old response does not recheck its legal sources.</p>
    <p role="status" className="metadata">{message || (!data && !error ? "Loading saved questions…" : "")}</p>
    {error && <section className="notice notice-caution" role="alert"><h2>History unavailable</h2><p>{error}</p></section>}
    {data && !data.available && <p className="notice">Encrypted saving is unavailable. You can still ask temporary questions.</p>}
    {data?.conversations.length === 0 && <section className="history-empty"><h2>No saved questions yet</h2><p>Turn on <strong>Save questions on this device</strong> in the question options or Settings before asking.</p><Link to="/" className="text-link touch-link">Ask a question</Link></section>}
    {!!data?.conversations.length && <>
      <ul className="saved-list">{data.conversations.map(row => <li key={row.id}>
        <div><Link to={`/saved/${row.id}`} className="saved-title">{row.title}</Link><p className="metadata">{row.turns} saved {row.turns === 1 ? "response" : "responses"} · {new Date(row.updated_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}</p></div>
        <div className="history-actions"><button type="button" className="text-link touch-link" onClick={() => void download(row.id)}>Export JSON</button><button type="button" className="text-link touch-link" aria-label={`Delete ${row.title}`} onClick={() => setConfirmation(row.id)}>Delete</button></div>
        {confirmation === row.id && <div className="delete-confirmation"><p>Delete this set of saved questions from this device?</p><button type="button" className="secondary-button" disabled={busy} onClick={() => void remove(row.id)}>Delete saved questions</button><button type="button" className="text-link touch-link" disabled={busy} onClick={() => setConfirmation(null)}>Keep questions</button></div>}
      </li>)}</ul>
      {confirmation === "all" ? <div className="delete-confirmation"><p>Delete all saved questions for this browser? Export anything you need first.</p><button type="button" className="secondary-button" disabled={busy} onClick={() => void remove("all")}>Delete all saved questions</button><button type="button" className="text-link touch-link" disabled={busy} onClick={() => setConfirmation(null)}>Keep questions</button></div> : <button type="button" className="text-link touch-link" onClick={() => setConfirmation("all")}>Delete all saved questions</button>}
    </>}
    <details className="archived-examples"><summary>Archived design examples</summary><p className="metadata">Scripted examples, separate from your saved questions. They were not generated or verified by the live system.</p>
      <ul className="history-list">{conversations.map(conversation => {
        const turns = getConversationTurns(conversation);
        return turns.length ? <li key={conversation.id}><Link to={`/chat/${conversation.id}`}><h2>{conversation.title}</h2><DomainTag domain={turns[0].domain} scope={turns[0].scope} /><p className="metadata">{turns.length} scripted responses</p></Link></li> : null;
      })}</ul>
    </details>
  </div>;
}
