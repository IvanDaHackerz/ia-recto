import { StrictMode } from "react";
import { act, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import { PerformancePage } from "../pages/PerformancePage";
import { fetchApi } from "../data/api";
vi.mock("../data/api", async original => ({ ...await original<typeof import("../data/api")>(), fetchApi: vi.fn() }));

it("does not let an old canceled load overwrite a valid newer report", async () => {
  let rejectOld!: (reason: Error) => void;
  vi.mocked(fetchApi).mockImplementationOnce(() => new Promise((_, reject) => { rejectOld = reject; }))
    .mockResolvedValueOnce({ schema_version: "1.0", sample_data: false, development_only: true, independent_human_questions: 0,
      run_id: "synthetic-empty-test", recorded_at: "2026-10-19", stack: {}, stack_matches_current: true,
      provenance: "Fictional empty test fixture", metrics: {}, cases: [], available_paths: ["baseline"], evaluation_mode: "local_classifier_retrieval_verifier" });
  render(<StrictMode><MemoryRouter><PerformancePage /></MemoryRouter></StrictMode>);
  expect(await screen.findByText("Fictional empty test fixture")).toBeInTheDocument();
  await act(async () => rejectOld(new DOMException("Canceled earlier load", "AbortError")));
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.getByText("Fictional empty test fixture")).toBeInTheDocument();
});
