export type Routing = {
  predicted_primary: string; predicted_scope: string; primary_confidence: number; scope_confidence: number;
  routing_action: string; reason: string; clarification_question: string | null;
};
export type Candidate = {
  chunk_id: string; provision_id: string; document_id: string; citation_display: string; citation_label?: string; document_title: string;
  parent_text: string; display_text: string; score: number; legal_status: string; status_as_of: string;
  official_source_url: string | null; retrieval_url: string | null;
  conditions: unknown; legal_relationships: unknown; freshness_rule: unknown; explanation_restriction?: string;
};
export type Concern = {
  component_id: string; query: string; allowed_domain: string; retrieval_status: string; retrieval_reason: string;
  candidates: Candidate[]; evidence_gates: { chunk_id: string; passed: boolean; reasons: string[] }[];
};
export type ChatResult = {
  schema_version: string; request_id: string; total_query_ms: number; original_question_text: string;
  clarification_follow_up: { question: string } | null;
  guidance_context?: { mode: string; note: string; follow_up: string; classification_is_conditional: boolean; original_routing: Routing };
  search_help?: { query: string; reason: string; changes_user_facts: false };
  situation_context?: { reason: string; original_components: { component_id: string; query: string }[] };
  response?: { version: string; kind: string; heading: string; paragraphs: string[]; ai_generated: boolean;
    context_checked?: boolean; generation?: { status: string; reason: string; llm_calls: number };
    follow_up: string | null; follow_up_options: { label: string; question_text: string }[];
    quotes: { component_id: string; chunk_id: string; citation_display: string; quote: string; complete_provision: boolean }[] };
  safety_notice?: { kind: string; heading: string; text: string; source_url: string; emergency_number: string } | null;
  privacy?: { redacted: boolean; categories: Record<string, number>; external_ai_enabled: boolean; guaranteed_complete: false; note: string };
  history?: { saved: boolean; conversation_id?: string; turn_id?: string; error?: string; retention_days?: number };
  referrals?: { id: string; agency: string; service: string; contact: Record<string, string>; checked_on: string; information_url: string; note: string; complete: boolean }[];
  source_review_notices?: { document_id: string; title: string; official_url: string; reason: string }[];
  normalization: { status: string; reason: string; normalized_question_text: string | null; effective_question_text: string | null;
    clarification_question: string | null; llm_calls: number; elapsed_ms: number; provider: string | null; model: string | null } | null;
  result: { question_text: string; routing: Routing; decision: string; as_of: string;
    excluded_components: { text: string }[]; referral_ids: string[]; components: Concern[] } | null;
  explanation: { status: string; reason: string; llm_calls: number; mode?: string; citations_checked?: boolean; automated_support_checked?: boolean; legal_support_verified?: boolean; failure_code?: string; validation_failure?: string; revision_attempted?: boolean;
    coverage_complete?: boolean; unanswered_components?: { component_id: string; query: string; reason: string }[];
    claims: { claim_id: string; component_id?: string; text: string; citations: { chunk_id: string; citation_display: string; citation_label?: string; quote: string; start?: number; end?: number }[] }[] };
};
export type ChatOptions = { request_id: string; use_ai: boolean; save_history: boolean; conversation_id?: string };
export type HistoryList = { schema_version: string; available: boolean; retention_days: number; conversations: { id: string; title: string; created_at: string; updated_at: string; turns: number }[] };
export type SavedConversation = { schema_version: string; conversation: { id: string; turns: { id: string; created_at: string; packet: ChatResult }[] } };
export type LiveReference = { hit: Candidate; concern: Concern };
export function referencesFor(packet?: ChatResult): LiveReference[] {
  return packet?.result?.components.flatMap(concern => concern.candidates.map(hit => ({ hit, concern }))) ?? [];
}

export function initialReferenceIndex(packet?: ChatResult): number | null {
  const references = referencesFor(packet);
  if (!references.length) return null;
  const explanation = packet?.explanation;
  const checked = explanation && (["generated", "partially_generated"].includes(explanation.status) && explanation.citations_checked && explanation.automated_support_checked
    || explanation.status === "verified" && explanation.legal_support_verified);
  if (!checked) return 0;
  const index = references.findIndex(reference => explanation.claims.some(claim => (!claim.component_id || claim.component_id === reference.concern.component_id)
    && claim.citations.some(citation => citation.chunk_id === reference.hit.chunk_id)));
  return index < 0 ? 0 : index;
}

export async function apiRequest<T>(path: string, options: { method?: string; signal?: AbortSignal; body?: unknown; keepalive?: boolean } = {}): Promise<T> {
  const response = await fetch(`/api/${path}`, { method: options.method ?? "GET", signal: options.signal,
    headers: options.body === undefined ? undefined : { "Content-Type": "application/json" }, credentials: "same-origin",
    body: options.body === undefined ? undefined : JSON.stringify(options.body), cache: "no-store", keepalive: options.keepalive });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.error?.message || "The local backend is unavailable. Start the API and try again.");
  }
  const payload = await response.json();
  if (payload.schema_version !== "1.0") throw new Error("The backend returned an unsupported response. Restart the local services.");
  return payload as T;
}

let session: Promise<unknown> | undefined;
const ensureSession = () => session ??= apiRequest("health").finally(() => { session = undefined; });
export async function cancelQuery(requestId: string) {
  try { await ensureSession(); await apiRequest("cancel", { method: "POST", body: { request_id: requestId }, keepalive: true }); } catch { /* The local service may already be offline. */ }
}
export function isChatResult(value: unknown): value is ChatResult {
  if (!value || typeof value !== "object") return false;
  const p = value as ChatResult;
  const responseValid = p.response === undefined || !!p.response && typeof p.response.heading === "string"
    && typeof p.response.ai_generated === "boolean" && Array.isArray(p.response.paragraphs) && p.response.paragraphs.every(text => typeof text === "string")
    && (p.response.generation === undefined || !!p.response.generation && typeof p.response.generation.status === "string" && typeof p.response.generation.reason === "string" && Number.isInteger(p.response.generation.llm_calls) && p.response.generation.llm_calls >= 0)
    && (p.response.kind !== "ai_guidance" || p.response.ai_generated && p.response.context_checked === true && p.response.generation?.status === "generated" && p.response.generation.llm_calls >= 2)
    && (p.response.follow_up === null || typeof p.response.follow_up === "string")
    && Array.isArray(p.response.follow_up_options) && p.response.follow_up_options.every(option => typeof option.label === "string" && typeof option.question_text === "string")
    && Array.isArray(p.response.quotes) && p.response.quotes.every(quote => typeof quote.quote === "string" && typeof quote.citation_display === "string"
      && p.result?.components?.some(component => component.component_id === quote.component_id && component.candidates.some(hit => hit.chunk_id === quote.chunk_id && hit.parent_text.includes(quote.quote))));
  const contextValid = p.guidance_context === undefined || !!p.guidance_context && typeof p.guidance_context.note === "string"
    && typeof p.guidance_context.classification_is_conditional === "boolean" && !!p.guidance_context.original_routing
    && typeof p.guidance_context.original_routing.predicted_primary === "string" && typeof p.guidance_context.original_routing.reason === "string";
  const situationValid = p.situation_context === undefined || !!p.situation_context && typeof p.situation_context.reason === "string"
    && Array.isArray(p.situation_context.original_components) && p.situation_context.original_components.every(c => typeof c.component_id === "string" && typeof c.query === "string");
  return p.schema_version === "1.0" && typeof p.original_question_text === "string" && typeof p.request_id === "string"
    && responseValid && contextValid && situationValid
    && !!p.explanation && Array.isArray(p.explanation.claims) && typeof p.explanation.reason === "string"
    && p.explanation.claims.every(c => typeof c.text === "string" && Array.isArray(c.citations) && c.citations.every(q => typeof q.quote === "string" && typeof q.chunk_id === "string"))
    && (p.result === null || !!p.result?.routing && Array.isArray(p.result.components) && Array.isArray(p.result.excluded_components)
      && p.result.components.every(c => Array.isArray(c.candidates) && Array.isArray(c.evidence_gates) && c.candidates.every(h => typeof h.parent_text === "string" && typeof h.citation_display === "string")));
}
export async function fetchApi<T>(path: string, signal?: AbortSignal, question?: string, options?: ChatOptions): Promise<T> {
  if (question !== undefined) await ensureSession();
  const packet = await apiRequest<T>(path, { signal, method: question === undefined ? "GET" : "POST", body: question === undefined ? undefined : { question_text: question, ...options } });
  if (path === "chat" && !isChatResult(packet)) throw new Error("The response was incomplete. Please retry; an unchecked draft has not been displayed.");
  return packet;
}

export const labelName = (label: string | null | undefined) => ({ labor: "Labor", consumer: "Consumer", mixed: "Mixed", out_of_scope: "Out of scope",
  fully_supported: "Fully supported", partially_supported: "Partially supported", unsupported: "Unsupported", __abstain__: "Withheld" }[label ?? ""] ?? label ?? "Withheld");
export const routeName = (route?: string | null) => ({ retrieve_supported_evidence: "Inspect supporting provisions", retrieve_supported_components: "Inspect the supported concerns",
  clarify: "More detail needed", refer_out_of_scope: "Outside this project’s scope" }[route ?? ""] ?? "Please reword your question");
