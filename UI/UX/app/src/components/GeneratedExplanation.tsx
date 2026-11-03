import { useEffect, useMemo, useRef, useState } from "react";
import type { ChatResult } from "../data/api";

export function GeneratedExplanation({ explanation, components = [], onReference }: {
  explanation: ChatResult["explanation"]; onReference: (chunk: string, trigger: HTMLElement, component?: string) => void;
  components?: NonNullable<ChatResult["result"]>["components"];
}) {
  const words = useMemo(() => explanation.claims.map(c => c.text.match(/\S+\s*/g) ?? []), [explanation.claims]);
  const total = words.reduce((n, row) => n + row.length, 0);
  const skipped = useRef(false);
  const [visible, setVisible] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches ? total : 0);
  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0; let started: number | undefined;
    const finish = () => { cancelAnimationFrame(frame); setVisible(total); };
    const advance = (now: number) => {
      if (skipped.current) return;
      started ??= now;
      const count = Math.min(total, Math.ceil((now - started) / Math.min(5000, Math.max(1, total * 30)) * total));
      setVisible(count);
      if (count < total) frame = requestAnimationFrame(advance);
    };
    if (!preference.matches) frame = requestAnimationFrame(advance);
    const changed = () => { if (preference.matches) finish(); };
    const hidden = () => { if (document.hidden) finish(); };
    preference.addEventListener("change", changed); document.addEventListener("visibilitychange", hidden);
    return () => { cancelAnimationFrame(frame); preference.removeEventListener("change", changed); document.removeEventListener("visibilitychange", hidden); };
  }, [total]);
  return <section className="generated-explanation" aria-label="AI explanation">
    <div className="explanation-heading"><h3>{explanation.status === "partially_generated" ? "AI explanation for supported parts" : "AI explanation"}</h3>{visible < total && <button type="button" className="text-link touch-link" onClick={() => { skipped.current = true; setVisible(total); }}>Show full answer</button>}</div>
    <p className="metadata explanation-disclosure">{explanation.status === "verified" ? "Reviewed against the recorded evidence. Inspect the source-check dates and limitations." : "Citations and automated source support checked. Legal interpretation and current applicability have not been independently reviewed."}</p>
    {explanation.claims.map((claim, index) => {
      const before = words.slice(0, index).reduce((sum, row) => sum + row.length, 0);
      const count = Math.max(0, visible - before);
      const component = components.find(c => c.component_id === claim.component_id);
      return <div className="explanation-paragraph" key={claim.claim_id}>
        {components.length > 1 && component && <h4>{component.allowed_domain === "labor" ? "Labor concern" : "Consumer concern"}</h4>}
        <p><span className="sr-only">{claim.text}</span><span aria-hidden="true">{words[index].slice(0, count).join("")}{count > 0 && count < words[index].length && <span className="reveal-caret" />}</span></p>
        <div className="explanation-citations" aria-label={`Sources for paragraph ${index + 1}`}>
          {claim.citations.filter((citation, i, all) => all.findIndex(c => c.chunk_id === citation.chunk_id) === i).map(citation => <button type="button" className="text-link touch-link" key={citation.chunk_id} onClick={event => onReference(citation.chunk_id, event.currentTarget, claim.component_id)}>{citation.citation_label ?? citation.citation_display}</button>)}
        </div>
      </div>;
    })}
  </section>;
}
