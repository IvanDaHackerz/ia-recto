import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowDownToLine, ArrowRight, FlaskConical } from "lucide-react";
import { fetchApi, labelName, routeName } from "../data/api";
import { percent, ratio, reportFor, routingFor, type Head, type Language, type Path, type Variation, type PerformanceData, type EvaluationCase } from "../data/performance";
import "./performance.css";

function Segments<T extends string>({ label, value, choices, onChange }: {
  label: string; value: T; choices: { value: T; label: string }[]; onChange: (value: T) => void;
}) {
  return <div role="group" aria-label={label} className="perf-segments">{choices.map(c =>
    <button key={c.value} type="button" aria-pressed={c.value === value} onClick={() => onChange(c.value)}>{c.label}</button>)}</div>;
}
function CaseInspector({ rows, path }: { rows: EvaluationCase[]; path: Path }) {
  const [query, setQuery] = useState("");
  const [issuesOnly, setIssuesOnly] = useState(false);
  const [page, setPage] = useState(0);
  const matching = rows.filter(r => (!issuesOnly || r.paths[path]!.issues.length > 0) && (r.question + " " + r.id).toLowerCase().includes(query.toLowerCase()));
  const lastPage = Math.max(0, Math.ceil(matching.length / 8) - 1);
  const currentPage = Math.min(page, lastPage);
  const shown = matching.slice(currentPage * 8, currentPage * 8 + 8);
  return <section id="performance-questions" className="perf-prediction" aria-labelledby="questions-title">
    <div className="perf-section-title"><h2 id="questions-title">Check individual questions</h2><span className="perf-muted-tag">{matching.length} recorded forms</span></div>
    <p className="perf-description">See the expected labels, what the model predicted and its confidence. A question is correct or incorrect against its recorded label; F1 describes a set of questions.</p>
    <div className="perf-case-filters"><label>Find a question<input type="search" value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} placeholder="Search the wording or case ID" /></label>
      <label className="perf-checkbox"><input type="checkbox" checked={issuesOnly} onChange={e => { setIssuesOnly(e.target.checked); setPage(0); }} />Only cases with recorded issues</label></div>
    <div className="perf-records">{shown.length ? shown.map(row => {
      const prediction = row.paths[path]!;
      return <details key={row.id} className="perf-record"><summary><span className="perf-record-question">{row.question}<small>{row.id} · {row.variation} · {row.language === "en" ? "English" : "Taglish"}</small></span><span className="perf-record-status">{!row.labeled ? "Routing only" : prediction.domainCorrect && prediction.scopeCorrect ? prediction.routeCorrect ? "Labels correct" : "Labels match; route differs" : "Label withheld / incorrect"}</span></summary>
        <dl className="perf-case-scores"><div><dt>Topic</dt><dd>Expected: {row.labeled ? labelName(row.expectedDomain) : "Not labeled"}<br />Predicted: {labelName(prediction.domain)}<br />Confidence: {percent(prediction.domainConfidence)}</dd></div>
          <div><dt>Coverage</dt><dd>Expected: {row.labeled ? labelName(row.expectedScope) : "Not labeled"}<br />Predicted: {labelName(prediction.scope)}<br />Confidence: {percent(prediction.scopeConfidence)}</dd></div></dl>
        <p>Expected step: {routeName(row.expectedRoute)}<br />Actual step: {routeName(prediction.route)} · {prediction.routeCorrect ? "Matches" : "Does not match"}</p>
        <p className="metadata">{prediction.latencyMs.toFixed(0)} ms · {prediction.llmCalls} wording LLM calls · {prediction.wordingStatus}</p>
        {!!prediction.issues.length && <p className="perf-table-note">Recorded issues: {prediction.issues.map(x => x.replaceAll("_", " ")).join("; ")}.</p>}
      </details>;
    }) : <p className="notice">No questions match these filters. Clear the search or turn off the issue filter.</p>}</div>
    <div className="perf-pagination"><button type="button" className="secondary-button" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</button><span role="status">{matching.length ? "Page " + (currentPage + 1) + " of " + (lastPage + 1) : "0 results"}</span><button type="button" className="secondary-button" disabled={currentPage === lastPage} onClick={() => setPage(currentPage + 1)}>Next</button></div>
  </section>;
}

export function PerformancePage() {
  const [params] = useSearchParams();
  const detailed = params.get("view") === "details";
  const heading = useRef<HTMLHeadingElement>(null);
  const previousView = useRef(detailed);
  const [collection, setCollection] = useState<PerformanceData | null>(null);
  const [runChoice, setRunChoice] = useState<"current" | "historical">("current");
  const data = runChoice === "historical" ? collection?.historical_report ?? collection : collection;
  const local = data?.evaluation_mode === "local_classifier_retrieval_verifier";
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [language, setLanguage] = useState<Language>("all");
  const [variation, setVariation] = useState<Variation>("all");
  const [path, setPath] = useState<Path>("baseline");
  const [head, setHead] = useState<Head>("domain");
  const [matrixMode, setMatrixMode] = useState<"count" | "percent">("count");
  const [cell, setCell] = useState<{ actual: string; predicted: string } | null>(null);
  const [announcement, setAnnouncement] = useState("");
  useEffect(() => {
    if (previousView.current !== detailed) { previousView.current = detailed; heading.current?.focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: "instant" }); }
  }, [detailed]);
  useEffect(() => {
    const controller = new AbortController();
    let disposed = false; let timedOut = false;
    const timeout = window.setTimeout(() => { timedOut = true; controller.abort(); }, 15000);
    fetchApi<PerformanceData>("performance", controller.signal).then(value => {
      if (value.sample_data !== false || !Array.isArray(value.cases)) throw new Error("The saved evaluation report is invalid.");
      if (!disposed && !controller.signal.aborted) { setCollection(value); setError(""); }
    }).catch(reason => { if (!disposed) setError(timedOut ? "Loading the report timed out. Check the local API and retry." : reason instanceof Error ? reason.message : "The report could not be loaded. Please retry."); }).finally(() => window.clearTimeout(timeout));
    return () => { disposed = true; window.clearTimeout(timeout); controller.abort(); };
  }, [retry]);
  const rows = data?.cases.filter(r => (language === "all" || r.language === language) && (variation === "all" || r.variation === variation)) ?? [];
  const domain = reportFor(rows, path, "domain"), scope = reportFor(rows, path, "scope");
  const report = head === "domain" ? domain : scope;
  const routing = routingFor(rows, path);
  const withheldLabels = rows.filter(r => r.labeled && r.paths[path]!.domain === "__abstain__").length;
  const selectedRows = cell ? rows.filter(r => r.labeled && (head === "domain" ? r.expectedDomain : r.expectedScope) === cell.actual && (r.paths[path]![head] ?? "__abstain__") === cell.predicted) : [];
  function download() {
    if (!data) return;
    const payload = { ...data, cases: rows, selected_filters: { language, variation, path }, selected_results: { domain, scope, routing } };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = data.run_id + "-" + path + "-" + variation + "-" + language + ".json"; anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000); setAnnouncement("Recorded development report downloaded.");
  }
  return <div className="performance-page" id="performance-top">
    <header className="perf-page-heading"><div><h1 ref={heading} tabIndex={-1}>Classifier performance</h1><p>{detailed ? "The scores, mistakes and checks behind the overview." : "How well does it recognize a question? Start with the essentials."}</p></div></header>
    <div className="perf-sample-notice"><FlaskConical size={19} aria-hidden="true" /><p><strong>Measured development results.</strong> AI-authored cases used while improving the system. These are not independent human tests or legal-answer accuracy scores.</p></div>
    <div className="perf-view-bar"><nav className="perf-view-nav" aria-label="Performance views"><Link to="/performance" aria-current={!detailed ? "page" : undefined}>Overview</Link><Link to="/performance?view=details" aria-current={detailed ? "page" : undefined}>Detailed results</Link></nav></div>
    {!data ? <section className="notice" role={error ? "alert" : "status"}><h2>{error ? "Report unavailable" : "Loading recorded results…"}</h2>{error && <><p>{error}</p><button type="button" className="secondary-button" onClick={() => { setError(""); setRetry(n => n + 1); }}>Retry</button></>}</section> : <>
    {!data.stack_matches_current && <p className="notice notice-caution">The saved evaluation measures a different stack. These figures describe that recorded run, not the current model.</p>}
    <div className="perf-live-filters">{collection?.historical_report && <label>Evaluation<select value={runChoice} onChange={e => { const choice = e.target.value as "current" | "historical"; setRunChoice(choice); setPath(choice === "historical" ? "normalized" : "baseline"); setCell(null); }}><option value="current">Current local evaluation</option><option value="historical">Previous LLM comparison</option></select></label>}<label>Inputs<select value={variation} onChange={e => { setVariation(e.target.value as Variation); setCell(null); }}><option value="all">Clear + noisy wording</option><option value="clear">Clear wording</option><option value="noisy">Noisy wording</option></select></label>
      <label>Language<select value={language} onChange={e => { setLanguage(e.target.value as Language); setCell(null); }}><option value="all">English + Taglish</option><option value="en">English</option><option value="en_tl">Taglish</option></select></label>
      {data.available_paths.length > 1 && <label>Pipeline<select value={path} onChange={e => { setPath(e.target.value as Path); setCell(null); }}><option value="normalized">Classifier + conditional wording LLM</option><option value="baseline">Classifier alone</option></select></label>}</div>
    <p className="perf-table-note">{rows.length} input forms · {new Set(rows.map(r => r.family)).size} wording families · {domain.total} labeled · {rows.length - domain.total} routing-only. No fresh model calls are made by this page. {local ? "Tested path: classifier + retrieval + verifier, with both LLM layers disabled." : "Historical conditional-wording comparison; this measures its recorded stack."}</p>
    {!detailed ? <>
      <section className="perf-simple-summary" aria-labelledby="summary-title"><h2 id="summary-title">How often it gets the labels right</h2><p className="perf-description">Measured against recorded expectations, including withheld labels in the denominator.</p>
        <dl className="perf-simple-scores">{[{ name: "Recognizing the topic", sub: "Domain accuracy", result: domain }, { name: "Checking what we cover", sub: "Scope accuracy", result: scope }].map(x => <div key={x.name}><dt>{x.name}<span>{x.sub}</span></dt><dd><strong>{percent(x.result.accuracy)}</strong><span>{x.result.correct} of {x.result.total} labels correct</span><small>Development results on these selected forms.</small></dd></div>)}</dl>
        <p className="perf-table-note">Correct routing: {routing.correct}/{routing.total} ({percent(ratio(routing.correct, routing.total))}). {withheldLabels} labeled inputs withheld in this selection; they count as misses.</p>
      </section>
      <CaseInspector key={data.run_id} rows={rows} path={path} />
      <aside className="perf-detail-invite"><div><h2>Want to look closer?</h2><p>Inspect F1, class-by-class mistakes, routing and confidence calibration.</p></div><Link className="secondary-button" to="/performance?view=details">View detailed results<ArrowRight size={16} aria-hidden="true" /></Link></aside>
    </> : <>
      <div className="perf-details-heading"><div><h2>Detailed results</h2><p className="perf-description">The same saved predictions power every score and case below.</p></div><button type="button" className="secondary-button perf-download" onClick={download}><ArrowDownToLine size={17} aria-hidden="true" />Download report</button></div>
      <nav className="perf-section-nav" aria-label="Detailed report sections"><span>Jump to</span><a href="#performance-scores">Scores</a><a href="#performance-classes">Classes</a><a href="#performance-routing">Routing</a><a href="#performance-confidence">Confidence</a>{data.evidence_checks && <a href="#performance-evidence">Evidence</a>}<a href="#performance-questions">Questions</a><a href="#performance-data">About the data</a></nav>
      <section id="performance-scores" className="perf-overview"><h2>Two decisions, measured separately</h2><div className="perf-table-scroll" tabIndex={0} role="region" aria-label="Overall classifier scores"><table className="perf-table"><caption className="perf-sr-only">Selected development results</caption><thead><tr><th scope="col">Decision</th><th scope="col">Accuracy</th><th scope="col">Macro precision</th><th scope="col">Macro recall</th><th scope="col">Macro F1</th><th scope="col">Correct / total</th></tr></thead><tbody>{[{ name: "Topic", r: domain }, { name: "Coverage", r: scope }].map(({ name, r }) => <tr key={name}><th scope="row">{name}</th><td>{percent(r.accuracy)}</td><td>{r.macroPrecision?.toFixed(3) ?? "—"}</td><td>{r.macroRecall?.toFixed(3) ?? "—"}</td><td className="perf-f1">{r.macroF1?.toFixed(3) ?? "—"}</td><td>{r.correct}/{r.total}</td></tr>)}</tbody></table></div><p className="perf-table-note">Macro scores weight each represented class equally. Clarification-only forms have no invented topic or coverage labels.</p></section>
      <section className="perf-evidence" id="performance-classes"><div className="perf-filter-bar"><Segments label="Classification output" value={head} onChange={x => { setHead(x); setCell(null); }} choices={[{ value: "domain", label: "Topic" }, { value: "scope", label: "Coverage" }]} /><Segments label="Matrix values" value={matrixMode} onChange={setMatrixMode} choices={[{ value: "count", label: "Counts" }, { value: "percent", label: "Row %" }]} /></div>
        <h2>Where predictions land</h2><p className="perf-description">Rows are expected labels; columns are predictions. “Withheld” includes failed wording validation. Select a cell to inspect its questions.</p>
        <div className="perf-table-scroll" tabIndex={0} role="region" aria-label="Confusion matrix"><table className="perf-matrix"><caption className="perf-sr-only">Expected versus predicted {head} labels</caption><thead><tr><td aria-hidden="true" />{report.columns.map(c => <th scope="col" key={c}>{labelName(c)}</th>)}</tr></thead><tbody>{report.labels.map((label, i) => <tr key={label}><th scope="row">{labelName(label)}</th>{report.columns.map((column, j) => <td key={column}><button type="button" className="perf-matrix-cell" data-tone={report.matrix[i][j] === 0 ? "zero" : label === column ? "correct" : "confused"} aria-pressed={cell?.actual === label && cell.predicted === column} aria-label={"Expected " + labelName(label) + ", predicted " + labelName(column) + ": " + report.matrix[i][j] + " cases"} onClick={() => setCell({ actual: label, predicted: column })}><strong>{matrixMode === "count" ? report.matrix[i][j] : percent(ratio(report.matrix[i][j], report.classes[i].support), 0)}</strong></button></td>)}</tr>)}</tbody></table></div>
        {cell && <div className="perf-case-inspector" aria-live="polite"><h3>{selectedRows.length} cases: {labelName(cell.actual)} → {labelName(cell.predicted)}</h3>{selectedRows.length ? selectedRows.slice(0, 3).map(r => <p key={r.id}>{r.question}<small className="metadata"> · {r.id}</small></p>) : <p>No cases fall in this cell.</p>}{selectedRows.length > 3 && <p className="metadata">Showing 3 of {selectedRows.length}. Search by ID below or download all selected cases.</p>}</div>}
        <h3 className="perf-breakdown-heading">Performance by class</h3><div className="perf-table-scroll" tabIndex={0} role="region" aria-label="Per class metrics"><table className="perf-table"><caption className="perf-sr-only">Per-class precision recall and F1</caption><thead><tr><th scope="col">Class</th><th scope="col">Precision</th><th scope="col">Recall</th><th scope="col">F1</th><th scope="col">Cases</th></tr></thead><tbody>{report.classes.map(c => <tr key={c.label}><th scope="row">{labelName(c.label)}</th><td>{c.precision.toFixed(3)}</td><td>{c.recall.toFixed(3)}</td><td className="perf-f1">{c.f1.toFixed(3)}</td><td>{c.support}</td></tr>)}</tbody></table></div>
      </section>
      <div className="perf-quality-grid"><section id="performance-routing" className="perf-routing"><h2>Routing and retrieval</h2><dl className="perf-routing-list">{[
        { label: "Correct next step", n: routing.correct, d: routing.total, note: "Exact route matches across all selected forms." },
        { label: "Known-relevant Hit@5", n: routing.hit, d: routing.judged, note: "Judged concern groups with a known relevant provision among the first five." },
        { label: "Clarification success", n: routing.clarificationCorrect, d: routing.clarifications, note: "Routing-only forms that ask for clarification." },
        { label: "Unsupported admission", n: routing.admissions, d: routing.unsupported, note: "Unsupported forms sent to retrieval. Lower is better." }
      ].map(x => <div key={x.label}><dt>{x.label}<small>{x.note}</small></dt><dd>{percent(ratio(x.n, x.d))}<span>{x.n}/{x.d}</span></dd></div>)}</dl><div className="perf-timing"><span>Recorded pipeline time</span><span>Median <strong>{routing.median?.toFixed(0) ?? "—"} ms</strong></span><span>P95 <strong>{routing.p95?.toFixed(0) ?? "—"} ms</strong></span></div><p className="perf-table-note">{routing.llmCalls} wording LLM calls. {local ? "Both LLM stages were disabled. Timing excludes the separate diagnostic excerpt postflight." : "Most inputs stayed local; overall latency is not LLM request latency."}</p></section>
      <section id="performance-confidence" className="perf-calibration"><h2>Does confidence match accuracy?</h2><p className="perf-description">{head === "domain" ? "Topic" : "Coverage"} ECE: <strong>{report.ece?.toFixed(3) ?? "—"}</strong>. Lower is better. Calculated on {report.available} available predictions; withheld labels have no fabricated confidence.</p><div className="perf-table-scroll" tabIndex={0} role="region" aria-label="Calibration bins"><table className="perf-table"><caption className="perf-sr-only">Observed confidence calibration</caption><thead><tr><th scope="col">Bin</th><th scope="col">Cases</th><th scope="col">Confidence</th><th scope="col">Accuracy</th></tr></thead><tbody>{report.bins.filter(b => b.count).map(b => <tr key={b.low}><th scope="row">{percent(b.low, 0)}–{percent(b.high, 0)}</th><td>{b.count}</td><td>{percent(b.confidence)}</td><td>{percent(b.accuracy)}</td></tr>)}</tbody></table></div><p className="perf-table-note">Confidence is label certainty, not a probability that a legal answer is correct. Reused development cases do not establish calibration on future users.</p></section></div>
      <CaseInspector key={data.run_id} rows={rows} path={path} />
    </>}
    {detailed && data.evidence_checks && <section className="perf-prediction" id="performance-evidence"><h2>Evidence checks for the complete local run</h2><p className="perf-description">These checks cover the full run, independent of the question filters. Exact source quotations establish provenance, not legal relevance or current applicability.</p>
      <dl className="perf-routing-list"><div><dt>Candidate integrity<small>Stored metadata, source text and domain checks.</small></dt><dd>{data.evidence_checks.candidate_integrity_checks - data.evidence_checks.candidate_integrity_failures}/{data.evidence_checks.candidate_integrity_checks}<span>checks passed</span></dd></div>
      <div><dt>Exact recorded excerpts<small>Diagnostic quotations passed the citation postflight.</small></dt><dd>{data.evidence_checks.recorded_excerpt_claims_passed}/{data.evidence_checks.recorded_excerpt_claims}<span>claims checked</span></dd></div>
      <div><dt>Unapproved explanations withheld<small>No legal explanation was generated or approved.</small></dt><dd>{data.evidence_checks.unreviewed_explanation_withheld}/{data.evidence_checks.inputs}<span>inputs</span></dd></div>
      <div><dt>Wrong-domain candidate leaks<small>Lower is better. Relevance is measured separately through Hit@5.</small></dt><dd>{data.evidence_checks.cross_domain_candidate_leaks}<span>candidate leaks</span></dd></div></dl>
      {detailed && language === "all" && variation === "all" && data.development_intervals && <p className="perf-table-note">Descriptive 95% family-resampling range for topic accuracy: {percent(data.development_intervals.primary_correct.low)}–{percent(data.development_intervals.primary_correct.high)}. This reflects variation within the inspected development families, not independent population accuracy.</p>}
    </section>}
    {detailed && data.application_replay && <section className="perf-prediction"><h2>Live AI pipeline check</h2><p>A separate replay used the same {data.application_replay.input_forms} synthetic inputs with conditional wording and explanation checks enabled. These figures cover the full replay and do not follow the filters above.</p><dl className="perf-routing-list"><div><dt>Responses returned</dt><dd>{data.application_replay.successful_packets}/{data.application_replay.input_forms}</dd></div><div><dt>Explanations shown<small>Passed exact citations and same-model automated support. This is not an answer-accuracy score.</small></dt><dd>{data.application_replay.explanation_status.generated ?? 0}<span>{data.application_replay.explanation_status.withheld ?? 0} withheld</span></dd></div><div><dt>Provider use<small>Includes failures. Cost is an estimate, not confirmed billing.</small></dt><dd>{data.application_replay.usage.provider_requests}<span>${data.application_replay.usage.estimated_usd.toFixed(4)} estimated</span></dd></div><div><dt>Whole-request latency</dt><dd>{Math.round(data.application_replay.latency_ms.p50)} ms<span>P95 {Math.round(data.application_replay.latency_ms.p95)} ms</span></dd></div></dl><details><summary>Why explanations were withheld</summary><ul>{Object.entries(data.application_replay.withholding_reasons).map(([reason, count]) => <li key={reason}>{reason.replaceAll("_", " ")}: {count}</li>)}</ul></details><p className="perf-table-note">Run: {data.application_replay.run_id}. Inference code {data.application_replay.inference_files_match ? "matches" : "differs from"} the evaluated files. Independent legal-answer accuracy is unmeasured. Provider failures and conservative withholding limit availability; a passed automated check does not establish current legal correctness.</p></section>}
    <section className="perf-method" id="performance-data"><div><h2>What these results represent</h2><p>{data.provenance}</p><p>The full selected run contains {data.cases.length} forms from {new Set(data.cases.map(r => r.family)).size} families: {data.cases.filter(r => r.labeled).length} labeled forms and {data.cases.filter(r => !r.labeled).length} routing-only forms. Repeated variants are not independent people. Independent human questions: {data.independent_human_questions}.</p><p>Measured on {data.recorded_at.slice(0, 10)}. {local ? "The 424 reused inputs and 12 joined-concern regressions were evaluated locally. Expected labels are scored even when routing conservatively asks for clarification. No conditional-wording or explanation LLM was tested in this local run." : "The noisy conditional pipeline scored 250/252 topic labels; the classifier alone scored 251/252. The wording LLM did not improve topic accuracy in that historical run."} Independent generated-answer quality and current legal applicability were not evaluated.</p></div><div><h2>Recorded stack</h2><dl className="perf-stack">{Object.entries(data.stack).map(([name, value]) => <div key={name}><dt>{name.replaceAll("_", " ")}</dt><dd>{value.split("/").at(-1)}</dd></div>)}</dl><p>Run: {data.run_id}. Current classifier, retrieval and verifier bindings {data.stack_matches_current ? "match" : "differ from"} this record. New questions are not added to the report or used for training.</p></div></section>
    </>}
    <span role="status" className="perf-sr-only">{announcement}</span>
  </div>;
}

