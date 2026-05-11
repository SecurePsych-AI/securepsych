import { Routes, Route } from "react-router-dom";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import ProjectOverviewPage from "@/pages/ProjectOverviewPage";
import ProjectChatPage from "@/pages/ProjectChatPage";
import ProjectSummarizerPage from "@/pages/ProjectSummarizerPage";
import ProjectJargonPage from "@/pages/ProjectJargonPage";
import ProjectHistoryPage from "@/pages/ProjectHistoryPage";
import NotFoundPage from "@/pages/NotFoundPage";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/p/:projectId" element={<ProjectOverviewPage />} />
        <Route path="/p/:projectId/qa" element={<ProjectChatPage />} />
        <Route path="/p/:projectId/qa/:threadId" element={<ProjectChatPage />} />
        <Route path="/p/:projectId/summarize" element={<ProjectSummarizerPage />} />
        <Route path="/p/:projectId/jargon" element={<ProjectJargonPage />} />
        <Route path="/p/:projectId/history" element={<ProjectHistoryPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
