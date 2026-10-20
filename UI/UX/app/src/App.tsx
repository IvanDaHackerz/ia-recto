import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SettingsProvider } from "./context/SettingsContext";
import { AppShell } from "./components/AppShell";
import { ChatPage } from "./pages/ChatPage";
import { HistoryPage } from "./pages/SavedHistoryPage";
import { LibraryPage } from "./pages/LibraryPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AboutPage } from "./pages/AboutPage";
import { PerformancePage } from "./pages/PerformancePage";

function App() {
  return (
    <SettingsProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<ChatPage />} />
            <Route path="chat/:conversationId" element={<ChatPage />} />
            <Route path="saved/:savedId" element={<ChatPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="library" element={<LibraryPage />} />
            <Route path="performance" element={<PerformancePage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="about" element={<AboutPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </SettingsProvider>
  );
}

export default App;

