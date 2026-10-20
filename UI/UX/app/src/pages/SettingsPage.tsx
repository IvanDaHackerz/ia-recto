import { ReadingControls } from "../components/ReadingControls";
import { useSettings } from "../context/settingsState";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PrivacyControls } from "../components/PrivacyControls";
import { apiRequest } from "../data/api";
export function SettingsPage() {
  const { storageAvailable } = useSettings();
  const [usage, setUsage] = useState<{ provider_requests: number; estimated_usd: number; maximum_calls: number; maximum_estimated_usd: number } | null>(null);
  useEffect(() => { const controller = new AbortController(); apiRequest<{ usage: typeof usage }>("status", { signal: controller.signal }).then(data => setUsage(data.usage)).catch(() => {}); return () => controller.abort(); }, []);
  return <div className="reading-page">
    <header className="page-heading"><div><h1>Settings</h1><p>Choose how you read, use AI and save questions.</p></div></header>
    <p className="metadata" role="status">{storageAvailable ? "Preferences are saved in this browser. Saving a question is a separate opt-in choice." : "Browser preference storage is unavailable. These choices apply while the page remains open."}</p>
    <ReadingControls />
    <section className="settings-section"><h2>AI and privacy</h2><PrivacyControls /><p className="metadata">Known personal identifiers are removed locally before provider export. Automated redaction can miss details; omit real names and sensitive information. <Link to="/about">Read the scope and privacy information</Link>.</p></section>
    <section className="settings-section"><h2>Saved questions</h2><p>Saved responses are encrypted on this device and expire after 30 days. You can open, export or delete them in History. Exports contain readable question and response data.</p><Link className="text-link touch-link" to="/history">Manage saved questions</Link></section>
    <section className="settings-section"><h2>AI use today</h2>{usage ? <><p>{usage.provider_requests} of {usage.maximum_calls} request attempts · ${usage.estimated_usd.toFixed(4)} estimated of ${usage.maximum_estimated_usd.toFixed(2)} daily limit.</p><p className="metadata">The day resets at 00:00 UTC. Failed attempts count toward the limit. Estimates use configured model rates; provider billing can differ. Limits apply to all browsers using this local service.</p></> : <p className="metadata">Usage is available when the local API is running.</p>}</section>
  </div>;
}
