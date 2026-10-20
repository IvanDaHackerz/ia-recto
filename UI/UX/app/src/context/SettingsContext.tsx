import { useEffect, useState, type ReactNode } from "react";
import { SettingsContext, type TextSize } from "./settingsState";
const TEXT_SIZE_KEY = "recto.textSize";
const CONTRAST_KEY = "recto.highContrast";
function readPreference(key: string) { try { return localStorage.getItem(key); } catch { return null; } }
export function SettingsProvider({ children }: { children: ReactNode }) {
  const [textSize, updateTextSize] = useState<TextSize>(() => { const value = readPreference(TEXT_SIZE_KEY); return value === "lg" || value === "xl" ? value : "md"; });
  const [highContrast, updateHighContrast] = useState(() => readPreference(CONTRAST_KEY) === "true");
  const [useAI, updateUseAI] = useState(() => readPreference("recto.useAI") !== "false");
  const [saveHistory, updateSaveHistory] = useState(() => readPreference("recto.saveHistory") === "true");
  const [storageAvailable, setStorageAvailable] = useState(() => { try { return typeof localStorage.length === "number"; } catch { return false; } });
  function persist(key: string, value: string) {
    try { localStorage.setItem(key,value); setStorageAvailable(true); }
    catch { setStorageAvailable(false); }
  }
  function setTextSize(size: TextSize) { updateTextSize(size); persist(TEXT_SIZE_KEY,size); }
  function setHighContrast(value: boolean) { updateHighContrast(value); persist(CONTRAST_KEY,String(value)); }
  function setUseAI(value: boolean) { updateUseAI(value); persist("recto.useAI",String(value)); }
  function setSaveHistory(value: boolean) { updateSaveHistory(value); persist("recto.saveHistory",String(value)); }
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("text-size-md", "text-size-lg", "text-size-xl");
    root.classList.add(`text-size-${textSize}`);
    root.classList.toggle("high-contrast",highContrast);
  }, [textSize,highContrast]);
  return <SettingsContext.Provider value={{textSize,setTextSize,highContrast,setHighContrast,storageAvailable,useAI,setUseAI,saveHistory,setSaveHistory}}>{children}</SettingsContext.Provider>;
}
