import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

export function mediaPreference(initial = false) {
  const listeners = new Set<() => void>();
  const media = { matches: initial, media: "(prefers-reduced-motion: reduce)", onchange: null,
    addEventListener: (_: string, fn: () => void) => listeners.add(fn), removeEventListener: (_: string, fn: () => void) => listeners.delete(fn),
    addListener: (fn: () => void) => listeners.add(fn), removeListener: (fn: () => void) => listeners.delete(fn), dispatchEvent: () => true };
  Object.defineProperty(window, "matchMedia", { configurable: true, writable: true, value: vi.fn(() => media) });
  return (value: boolean) => { media.matches = value; listeners.forEach(fn => fn()); };
}
beforeEach(() => { localStorage.clear(); mediaPreference(); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
