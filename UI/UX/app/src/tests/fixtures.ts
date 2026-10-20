import type { ChatResult, LiveReference } from "../data/api";
export const packet: ChatResult = {
  schema_version: "1.0", request_id: "synthetic-ui-test", total_query_ms: 10, original_question_text: "A fictional wage question",
  clarification_follow_up: null, normalization: null,
  result: { question_text: "A fictional wage question", as_of: "2026-10-19", decision: "insufficient_evidence", excluded_components: [], referral_ids: [],
    routing: { predicted_primary: "labor", predicted_scope: "fully_supported", primary_confidence: .9, scope_confidence: .8, routing_action: "retrieve_supported_evidence", reason: "test", clarification_question: null },
    components: [{ component_id: "c1", query: "A fictional wage question", allowed_domain: "labor", retrieval_status: "candidates_found", retrieval_reason: "test", evidence_gates: [], candidates: [{
      chunk_id: "h1", provision_id: "p1", document_id: "d1", citation_display: "Fictional section", citation_label: "Fictional section — Rule I", document_title: "Synthetic source fixture",
      parent_text: "Before. A recorded fictional rule with its condition. After.", display_text: "A recorded fictional rule with its condition.", score: 1, legal_status: "recorded_test", status_as_of: "2026-10-19", official_source_url: "https://example.com/source", retrieval_url: null, conditions: [], legal_relationships: [], freshness_rule: "test" }] }] },
  explanation: { status: "generated", reason: "citations_and_automated_support_checked", llm_calls: 2, citations_checked: true, automated_support_checked: true, legal_support_verified: false,
    claims: [{ claim_id: "claim1", component_id: "c1", text: "This fictional explanation describes the recorded rule and keeps its condition. It does not decide the facts of an individual case.", citations: [{ chunk_id: "h1", citation_display: "Fictional section", citation_label: "Fictional section — Rule I", quote: "A recorded fictional rule with its condition." }] }] },
};
export const reference: LiveReference = { hit: packet.result!.components[0].candidates[0], concern: packet.result!.components[0] };
