import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { SettingsProvider } from "../context/SettingsContext";
import { ChatPage } from "../pages/ChatPage";
import { fetchApi } from "../data/api";
import { packet } from "./fixtures";

vi.mock("../data/api", async original => ({ ...await original<typeof import("../data/api")>(), fetchApi: vi.fn(), cancelQuery: vi.fn() }));

const openComposer = () => {
  render(<SettingsProvider><MemoryRouter><ChatPage /></MemoryRouter></SettingsProvider>);
  return screen.getByRole("textbox", { name: "Your question" });
};

describe("question composer keyboard", () => {
  beforeEach(() => {
    vi.mocked(fetchApi).mockReset().mockResolvedValue(packet);
    HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it("sends the question with Enter through the existing submission path", async () => {
    const user = userEvent.setup();
    const input = openComposer();
    await user.type(input, "A fictional wage question{Enter}");
    await waitFor(() => expect(fetchApi).toHaveBeenCalledOnce());
    expect(vi.mocked(fetchApi).mock.calls[0][2]).toBe("A fictional wage question");
    expect(input).toHaveValue("");
    expect(await screen.findByRole("heading", { name: "A fictional wage question" })).toBeInTheDocument();
  });

  it("keeps Shift+Enter as a line break without sending", async () => {
    const user = userEvent.setup();
    const input = openComposer();
    await user.type(input, "First line{Shift>}{Enter}{/Shift}Second line");
    expect(input).toHaveValue("First line\nSecond line");
    expect(fetchApi).not.toHaveBeenCalled();
  });

  it("does not send blank input, repeated keydown, or composition-confirming Enter", () => {
    const input = openComposer();
    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.change(input, { target: { value: "A fictional wage question" } });
    fireEvent.keyDown(input, { key: "Enter", repeat: true });
    fireEvent.keyDown(input, { key: "Enter", isComposing: true });
    fireEvent.keyDown(input, { key: "Enter", keyCode: 229 });
    expect(fetchApi).not.toHaveBeenCalled();
    expect(input).toHaveValue("A fictional wage question");
  });

  it("does not send a second question while a request is pending", async () => {
    vi.mocked(fetchApi).mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();
    const input = openComposer();
    await user.type(input, "First question{Enter}");
    await user.type(input, "Next draft{Enter}");
    expect(fetchApi).toHaveBeenCalledOnce();
    expect(input).toHaveValue("Next draft");
  });
});
