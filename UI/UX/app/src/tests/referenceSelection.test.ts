import { describe, expect, it } from "vitest";
import { initialReferenceIndex } from "../data/api";
import { packet } from "./fixtures";

describe("initial source selection", () => {
  it("opens a cited supported component instead of an earlier unanswered component", () => {
    const partial = structuredClone(packet);
    partial.explanation.status = "partially_generated";
    partial.result!.components.push({ ...partial.result!.components[0], component_id: "c2", candidates: [{ ...partial.result!.components[0].candidates[0], chunk_id: "h2" }] });
    partial.explanation.claims[0].component_id = "c2";
    partial.explanation.claims[0].citations[0].chunk_id = "h2";
    expect(initialReferenceIndex(partial)).toBe(1);
  });
  it("keeps component identity when two concerns retrieve the same chunk", () => {
    const partial = structuredClone(packet);
    partial.result!.components.push({ ...partial.result!.components[0], component_id: "c2" });
    partial.explanation.claims[0].component_id = "c2";
    expect(initialReferenceIndex(partial)).toBe(1);
  });
  it("does not select citations from an unchecked draft", () => {
    const unchecked = structuredClone(packet);
    unchecked.result!.components.push({ ...unchecked.result!.components[0], component_id: "c2", candidates: [{ ...unchecked.result!.components[0].candidates[0], chunk_id: "h2" }] });
    unchecked.explanation.status = "withheld";
    unchecked.explanation.claims[0].component_id = "c2";
    unchecked.explanation.claims[0].citations[0].chunk_id = "h2";
    expect(initialReferenceIndex(unchecked)).toBe(0);
  });
  it("has no selected reference before any references exist", () => {
    expect(initialReferenceIndex()).toBeNull();
  });
});
