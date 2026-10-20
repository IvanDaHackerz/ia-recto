import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { HistoryPage } from "../pages/SavedHistoryPage";
import { PrivacyControls } from "../components/PrivacyControls";
import { SettingsProvider } from "../context/SettingsContext";
import { apiRequest } from "../data/api";
import { ChatPage } from "../pages/ChatPage";
import { packet } from "./fixtures";
vi.mock("../data/api", async original => ({ ...await original<typeof import("../data/api")>(), apiRequest: vi.fn() }));

describe("history and privacy choices", () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset());
  it("keeps saving off by default and lets keyboard users opt in", async () => {
    const user = userEvent.setup(); render(<SettingsProvider><PrivacyControls /></SettingsProvider>);
    const save = screen.getByRole("checkbox", { name: /Save questions on this device/ });
    expect(save).not.toBeChecked(); await user.tab(); await user.tab(); expect(save).toHaveFocus(); await user.keyboard(" ");
    expect(save).toBeChecked(); expect(localStorage.getItem("recto.saveHistory")).toBe("true");
  });
  it("can disable external AI without enabling saving", async () => {
    const user = userEvent.setup(); render(<SettingsProvider><PrivacyControls /></SettingsProvider>);
    await user.click(screen.getByRole("checkbox", { name: /Use AI explanations/ }));
    expect(localStorage.getItem("recto.useAI")).toBe("false"); expect(screen.getByRole("checkbox", { name: /Save questions on this device/ })).not.toBeChecked();
  });
  it("distinguishes empty saved history from archived design examples", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ schema_version: "1.0", available: true, retention_days: 30, conversations: [] });
    render(<MemoryRouter><HistoryPage /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "No saved questions yet" })).toBeInTheDocument();
    expect(screen.getByText("Archived design examples")).toBeInTheDocument();
  });
  it("requires confirmation before deletion and refetches the scoped list", async () => {
    const user = userEvent.setup(); const row = { id: "a".repeat(32), title: "Fictional salary question", turns: 1, updated_at: "2026-10-19T00:00:00Z" };
    vi.mocked(apiRequest).mockResolvedValueOnce({ schema_version: "1.0", available: true, retention_days: 30, conversations: [row] }).mockResolvedValueOnce({ schema_version: "1.0", deleted_turns: 1 }).mockResolvedValueOnce({ schema_version: "1.0", available: true, retention_days: 30, conversations: [] });
    render(<MemoryRouter><HistoryPage /></MemoryRouter>); await screen.findByRole("link", { name: row.title });
    await user.click(screen.getByRole("button", { name: `Delete ${row.title}` }));
    expect(vi.mocked(apiRequest).mock.calls.filter(c => c[1]?.method === "DELETE")).toHaveLength(0);
    await user.click(screen.getByRole("button", { name: "Delete saved questions" }));
    await waitFor(() => expect(apiRequest).toHaveBeenCalledWith(`history/${row.id}`, { method: "DELETE" }));
    expect(await screen.findByRole("heading", { name: "No saved questions yet" })).toBeInTheDocument();
  });
  it("renders a stored title as text and provides an honest offline error", async () => {
    vi.mocked(apiRequest).mockRejectedValueOnce(new Error("The local API is unavailable."));
    render(<MemoryRouter><HistoryPage /></MemoryRouter>); expect(await screen.findByRole("alert")).toHaveTextContent("The local API is unavailable.");
  });
  it("contains a malformed history response as a recoverable error", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ schema_version: "1.0", available: true });
    render(<MemoryRouter><HistoryPage /></MemoryRouter>);
    expect(await screen.findByRole("alert")).toHaveTextContent("Saved questions could not be read");
  });
  it("opens a saved packet from the history link and discloses that it is not rechecked", async () => {
    const user = userEvent.setup(); const id = "b".repeat(32);
    vi.mocked(apiRequest).mockResolvedValueOnce({ schema_version: "1.0", available: true, retention_days: 30,
      conversations: [{ id, title: "Fictional stored question", turns: 1, updated_at: "2026-10-19" }] })
      .mockResolvedValueOnce({ schema_version: "1.0", conversation: { id, turns: [{ id: "turn", created_at: "2026-10-19", packet }] } });
    render(<SettingsProvider><MemoryRouter initialEntries={["/history"]}><Routes><Route path="/history" element={<HistoryPage />} /><Route path="/saved/:savedId" element={<ChatPage />} /></Routes></MemoryRouter></SettingsProvider>);
    await user.click(await screen.findByRole("link", { name: "Fictional stored question" }));
    expect(await screen.findByText(/Sources and explanations are not rechecked when opened/)).toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledWith(`history/${id}`, expect.any(Object));
  });
});
