import { useSettings } from "../context/settingsState";

export function PrivacyControls() {
  const { useAI, setUseAI, saveHistory, setSaveHistory } = useSettings();
  return <div className="privacy-controls">
    <label><input type="checkbox" checked={useAI} onChange={event => setUseAI(event.target.checked)} /><span>Use AI explanations<span className="metadata">The question and selected sources may be sent to Together.ai. Turn off for local classification and retrieval only.</span></span></label>
    <label><input type="checkbox" checked={saveHistory} onChange={event => setSaveHistory(event.target.checked)} /><span>Save questions on this device<span className="metadata">Opt in to encrypted local history for 30 days. Use the same browser profile to return. You can export or delete saved questions.</span></span></label>
  </div>;
}
