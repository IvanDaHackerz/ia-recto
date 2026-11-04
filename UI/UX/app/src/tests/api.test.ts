import { describe, expect, it, vi } from "vitest";
import { fetchApi, isChatResult } from "../data/api";
import { packet } from "./fixtures";
describe("chat contract", () => {
  it("rejects AI situation guidance without its completed context check", () => {
    const guidance = structuredClone(packet);
    guidance.response = { version: "test", kind: "ai_guidance", heading: "About your situation", paragraphs: ["A fictional situation response."], ai_generated: true,
      quotes: [], follow_up: null, follow_up_options: [] };
    expect(isChatResult(guidance)).toBe(false);
    guidance.response.context_checked = true;
    guidance.response.generation = { status: "generated", reason: "factual_context_checked", llm_calls: 2 };
    expect(isChatResult(guidance)).toBe(true);
  });
  it("rejects malformed local responses and quotations that are absent from the source", () => {
    const local = structuredClone(packet);
    local.response = { version: "test", kind: "recorded_sources", heading: "What I found", paragraphs: ["Recorded material."], ai_generated: false, follow_up: null, follow_up_options: [],
      quotes: [{ component_id: "c1", chunk_id: "h1", citation_display: "Fictional section", quote: "This quotation was never in the source.", complete_provision: false }] };
    expect(isChatResult(local)).toBe(false);
    local.response.quotes[0].quote = local.result!.components[0].candidates[0].parent_text;
    expect(isChatResult(local)).toBe(true);
    local.response.paragraphs = null as never;
    expect(isChatResult(local)).toBe(false);
  });
  it("rejects incomplete results instead of exposing an unchecked draft", () => {
    expect(isChatResult(packet)).toBe(true); expect(isChatResult({ schema_version: "1.0", explanation: { claims: [] } })).toBe(false);
    const bad = structuredClone(packet); bad.explanation.claims[0].citations = null as never; expect(isChatResult(bad)).toBe(false);
  });
  it("establishes the signed browser session before the chat and sends privacy choices", async () => {
    const fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ schema_version: "1.0", status: "ready" }) }).mockResolvedValueOnce({ ok: true, json: async () => packet });
    vi.stubGlobal("fetch", fetch);
    await fetchApi("chat", undefined, "fictional", { request_id: "test", use_ai: false, save_history: false });
    expect(fetch.mock.calls[0][0]).toBe("/api/health"); expect(fetch.mock.calls[1][0]).toBe("/api/chat");
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toMatchObject({ question_text: "fictional", use_ai: false, save_history: false, request_id: "test" });
  });
});
