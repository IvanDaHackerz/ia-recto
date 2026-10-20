import { createContext, useContext } from "react";
export type TextSize = "md" | "lg" | "xl";
export interface SettingsState {
  textSize: TextSize; setTextSize: (size: TextSize) => void;
  highContrast: boolean; setHighContrast: (value: boolean) => void;
  storageAvailable: boolean;
  useAI: boolean; setUseAI: (value: boolean) => void;
  saveHistory: boolean; setSaveHistory: (value: boolean) => void;
}
export const SettingsContext = createContext<SettingsState | null>(null);
export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) throw new Error("useSettings must be used within SettingsProvider");
  return context;
}
