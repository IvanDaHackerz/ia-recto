export type Head = "domain" | "scope";
export type Language = "all" | "en" | "en_tl";
export type Path = "baseline" | "normalized";
export type Variation = "all" | "clear" | "noisy";
export type Prediction = {
  domain: string | null; scope: string | null; domainConfidence: number | null; scopeConfidence: number | null;
  route: string | null; routeCorrect: boolean; domainCorrect: boolean | null; scopeCorrect: boolean | null;
  latencyMs: number; retrieval: { hit_at_1: boolean; hit_at_5: boolean }[]; issues: string[]; llmCalls: number; wordingStatus: string;
};
export type EvaluationCase = {
  id: string; family: string; language: string; variation: string; question: string; labeled: boolean;
  expectedDomain: string | null; expectedScope: string | null; expectedRoute: string; paths: Partial<Record<Path, Prediction>>;
};
export type PerformanceData = {
  schema_version: string; sample_data: false; development_only: true; independent_human_questions: number;
  run_id: string; recorded_at: string; stack: Record<string, string>; stack_matches_current: boolean; provenance: string;
  metrics: unknown; cases: EvaluationCase[]; available_paths: Path[]; evaluation_mode: string;
  historical_report?: PerformanceData;
  application_replay?: { run_id: string; input_forms: number; successful_packets: number;
    explanation_status: Record<string, number>; withholding_reasons: Record<string, number>;
    generated_without_automated_support: number; normalizer_calls: number;
    latency_ms: { p50: number; p95: number; maximum: number };
    usage: { provider_requests: number; estimated_usd: number }; independent_legal_accuracy: null;
    inference_files_match: boolean };
  evidence_checks?: { inputs: number; live_permissions_closed: number; unreviewed_explanation_withheld: number;
    cross_domain_candidate_leaks: number; candidate_integrity_checks: number; candidate_integrity_failures: number;
    recorded_excerpt_claims: number; recorded_excerpt_claims_passed: number; recorded_excerpt_legal_support_claimed: number };
  development_intervals?: Record<string, { low: number; high: number; families: number; meaning: string }>;
};
export const DOMAIN_LABELS = ["labor", "consumer", "mixed", "out_of_scope"];
export const SCOPE_LABELS = ["fully_supported", "partially_supported", "unsupported"];
export const percent = (n: number | null | undefined, places = 1) => n == null || !Number.isFinite(n) ? "—" : (n * 100).toFixed(places) + "%";
export const ratio = (n: number, d: number) => d ? n / d : null;

export function reportFor(rows: EvaluationCase[], path: Path, head: Head) {
  const labels = head === "domain" ? DOMAIN_LABELS : SCOPE_LABELS;
  const records = rows.filter(r => r.labeled);
  const columns = [...labels, "__abstain__"];
  const matrix = labels.map(actual => columns.map(predicted => records.filter(r =>
    (head === "domain" ? r.expectedDomain : r.expectedScope) === actual && (r.paths[path]![head] ?? "__abstain__") === predicted).length));
  const classes = labels.map((label, index) => {
    const support = matrix[index].reduce((a, b) => a + b, 0);
    const predicted = matrix.reduce((n, row) => n + row[index], 0);
    const correct = matrix[index][index];
    const precision = predicted ? correct / predicted : 0, recall = support ? correct / support : 0;
    return { label, support, predicted, correct, precision, recall, f1: precision + recall ? 2 * precision * recall / (precision + recall) : 0 };
  });
  const active = classes.filter(c => c.support || c.predicted);
  const mean = (key: "precision" | "recall" | "f1") => active.length ? active.reduce((n, c) => n + c[key], 0) / active.length : null;
  const correct = classes.reduce((n, c) => n + c.correct, 0);
  const confidenceKey = head === "domain" ? "domainConfidence" : "scopeConfidence";
  const available = records.filter(r => r.paths[path]![confidenceKey] != null);
  const bins = Array.from({ length: 10 }, (_, i) => {
    const cases = available.filter(r => Math.min(9, Math.floor(r.paths[path]![confidenceKey]! * 10)) === i);
    return { low: i / 10, high: (i + 1) / 10, count: cases.length,
      confidence: cases.length ? cases.reduce((n, r) => n + r.paths[path]![confidenceKey]!, 0) / cases.length : null,
      accuracy: cases.length ? cases.filter(r => r.paths[path]![head] === (head === "domain" ? r.expectedDomain : r.expectedScope)).length / cases.length : null };
  });
  const ece = available.length ? bins.reduce((n, b) => n + b.count / available.length * Math.abs((b.confidence ?? 0) - (b.accuracy ?? 0)), 0) : null;
  return { labels, columns, matrix, classes, total: records.length, correct, accuracy: ratio(correct, records.length),
    macroPrecision: mean("precision"), macroRecall: mean("recall"), macroF1: mean("f1"), bins, ece, available: available.length };
}
export function routingFor(rows: EvaluationCase[], path: Path) {
  const timings = rows.map(r => r.paths[path]!.latencyMs).sort((a, b) => a - b);
  const quantile = (p: number) => {
    if (!timings.length) return null;
    const x = (timings.length - 1) * p, a = Math.floor(x), b = Math.ceil(x);
    return timings[a] + (timings[b] - timings[a]) * (x - a);
  };
  const judged = rows.flatMap(r => r.paths[path]!.retrieval);
  const clarifications = rows.filter(r => !r.labeled);
  const unsupported = rows.filter(r => r.labeled && r.expectedScope === "unsupported");
  return { correct: rows.filter(r => r.paths[path]!.routeCorrect).length, total: rows.length,
    hit: judged.filter(r => r.hit_at_5).length, judged: judged.length,
    clarificationCorrect: clarifications.filter(r => r.paths[path]!.routeCorrect).length, clarifications: clarifications.length,
    admissions: unsupported.filter(r => ["retrieve_supported_evidence", "retrieve_supported_components"].includes(r.paths[path]!.route ?? "")).length,
    unsupported: unsupported.length, llmCalls: rows.reduce((n, r) => n + r.paths[path]!.llmCalls, 0),
    median: quantile(.5), p95: quantile(.95) };
}

