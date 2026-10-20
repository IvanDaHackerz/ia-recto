import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import axe from "axe-core";
import { GeneratedExplanation } from "../components/GeneratedExplanation";
import { LiveCitationCard, LiveResult } from "../components/LiveResult";
import { packet, reference } from "./fixtures";
import { mediaPreference } from "./setup";

describe("validated explanation presentation", () => {
  it("reveals words, exposes complete accessible text, and never rewinds after skip", () => {
    let next = 0; const frames = new Map<number, FrameRequestCallback>();
    vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => { frames.set(++next, cb); return next; });
    vi.stubGlobal("cancelAnimationFrame", (id: number) => frames.delete(id));
    const tick = (time: number) => act(() => { const current = [...frames.values()]; frames.clear(); current.forEach(cb => cb(time)); });
    const { container } = render(<GeneratedExplanation explanation={packet.explanation} onReference={() => {}} />);
    expect(container.querySelector(".sr-only")).toHaveTextContent(packet.explanation.claims[0].text);
    tick(0); tick(200);
    expect(container.querySelector("p [aria-hidden=true]")?.textContent?.length).toBeLessThan(packet.explanation.claims[0].text.length);
    fireEvent.click(screen.getByRole("button", { name: "Show full answer" })); tick(300); tick(1000);
    expect(container.querySelector("p [aria-hidden=true]")?.textContent).toBe(packet.explanation.claims[0].text);
    expect(screen.queryByRole("button", { name: "Show full answer" })).not.toBeInTheDocument();
  });
  it("starts complete with reduced motion and completes when that preference changes", () => {
    mediaPreference(true);
    const view = render(<GeneratedExplanation explanation={packet.explanation} onReference={() => {}} />);
    expect(screen.queryByRole("button", { name: "Show full answer" })).not.toBeInTheDocument();
    view.unmount(); const change = mediaPreference(false);
    render(<GeneratedExplanation explanation={packet.explanation} onReference={() => {}} />);
    act(() => change(true)); expect(screen.queryByRole("button", { name: "Show full answer" })).not.toBeInTheDocument();
  });
  it("keeps citation navigation associated with the correct concern", () => {
    mediaPreference(true); const open = vi.fn();
    render(<GeneratedExplanation explanation={packet.explanation} onReference={open} />);
    const button = screen.getByRole("button", { name: "Fictional section — Rule I" }); fireEvent.click(button);
    expect(open).toHaveBeenCalledWith("h1", button, "c1");
  });
  it("withholds an old or unchecked generated draft", () => {
    const old = structuredClone(packet); old.explanation.automated_support_checked = false;
    render(<MemoryRouter><LiveResult packet={old} edit={() => {}} onReference={() => {}} /></MemoryRouter>);
    expect(screen.queryByRole("region", { name: "AI explanation" })).not.toBeInTheDocument();
    expect(screen.getByText("Explanation withheld.")).toBeInTheDocument();
  });
  it("explains topic coverage and a skipped support check without implying approval", () => {
    const waiting = structuredClone(packet);
    waiting.result!.routing.routing_action = "clarify";
    waiting.result!.routing.clarification_question = "Which employment category applies?";
    waiting.result!.components = [];
    waiting.explanation = { status: "withheld", reason: "supported_concern_required", llm_calls: 0, claims: [] };
    render(<MemoryRouter><LiveResult packet={waiting} edit={() => {}} onReference={() => {}} /></MemoryRouter>);
    expect(screen.getByText(/Within project topics/)).toBeInTheDocument();
    expect(screen.getByText("Not run — no validated draft was ready")).toBeInTheDocument();
    expect(screen.queryByText(/No explanation approved/)).not.toBeInTheDocument();
  });
  it("shows the actual draft problem while keeping failed content hidden", () => {
    const failed = structuredClone(packet);
    failed.explanation = { status: "withheld", reason: "citation_validation_failed", validation_failure: "incomplete_concerns", revision_attempted: true, llm_calls: 3, claims: [] };
    render(<MemoryRouter><LiveResult packet={failed} edit={() => {}} onReference={() => {}} /></MemoryRouter>);
    expect(screen.getByText(/did not cover every identified concern/)).toBeInTheDocument();
    expect(screen.getByText("incomplete concerns")).toBeInTheDocument();
    expect(screen.getByText("One correction attempted")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "AI explanation" })).not.toBeInTheDocument();
  });
  it("distinguishes a provider server error from a rejected explanation", () => {
    const failed = structuredClone(packet);
    failed.explanation = { status: "withheld", reason: "provider_unavailable", failure_code: "provider_http_503", llm_calls: 1, claims: [] };
    const reuse = vi.fn();
    render(<MemoryRouter><LiveResult packet={failed} edit={reuse} onReference={() => {}} /></MemoryRouter>);
    expect(screen.getByText(/temporary server error/)).toBeInTheDocument();
    expect(screen.getByText("provider http 503")).toBeInTheDocument();
    expect(screen.getByText("Not completed — AI service unavailable")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Use this question again" }));
    expect(reuse).toHaveBeenCalledOnce();
    expect(screen.queryByText(/did not pass citation/)).not.toBeInTheDocument();
  });
  it("highlights exact quoted text while retaining the complete stored provision", () => {
    const { container } = render(<LiveCitationCard reference={reference} id="source1" number={1} expanded onToggle={() => {}} quotes={[packet.explanation.claims[0].citations[0].quote]} />);
    expect(container.querySelector("mark")).toHaveTextContent("A recorded fictional rule with its condition.");
    expect(container.querySelector(".source-text")).toHaveTextContent(reference.hit.parent_text);
  });
  it("marks a disputed source without hiding its recorded text", () => {
    const held = structuredClone(reference);
    held.hit.explanation_restriction = "Recorded wording differs; excluded from AI explanations pending source review.";
    render(<LiveCitationCard reference={held} id="held-source" number={1} expanded onToggle={() => {}} />);
    expect(screen.getByText(held.hit.explanation_restriction)).toBeInTheDocument();
    expect(screen.getByText(held.hit.parent_text)).toBeInTheDocument();
  });
  it("has no detected structural accessibility violations in the response", async () => {
    mediaPreference(true);
    const { container } = render(<MemoryRouter><main><h1>Fictional question</h1><h2>Response</h2><LiveResult packet={packet} edit={() => {}} onReference={() => {}} /></main></MemoryRouter>);
    const result = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(result.violations).toEqual([]);
  });
});
