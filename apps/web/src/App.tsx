/**
 * 应用入口
 * 路由配置
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/hooks/useAuth';
import { AuthGuard } from '@/components/auth';
import { ConsoleLayout } from '@/components/console';
import {
  LoginPage,
  RegisterPage,
  ChatPage,
  AgentsPage,
  KnowledgePage,
  TeamsPage,
  SettingsPage,
  AgentCreatePage,
  AgentDetailPage,
  AgentTeamsPage,
  AgentTeamCreatePage,
  WorkflowsPage,
  WorkflowCreatePage,
} from '@/pages';
import { ThemeProvider } from '@/components/theme-provider';

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* 公开路由 */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* 受保护路由 - 控制台 */}
            <Route
              path="/console"
              element={
                <AuthGuard>
                  <ConsoleLayout />
                </AuthGuard>
              }
            >
              <Route index element={<Navigate to="chat" replace />} />
              <Route path="chat" element={<ChatPage />} />
              <Route path="agents" element={<AgentsPage />} />
              <Route path="agents/create" element={<AgentCreatePage />} />
              <Route path="agents/:agentId" element={<AgentDetailPage />} />
              <Route path="agent-teams" element={<AgentTeamsPage />} />
              <Route path="agent-teams/create" element={<AgentTeamCreatePage />} />
              <Route path="agent-teams/:teamId" element={<AgentTeamCreatePage />} />
              <Route path="workflows" element={<WorkflowsPage />} />
              <Route path="workflows/create" element={<WorkflowCreatePage />} />
              <Route path="workflows/:workflowId" element={<WorkflowCreatePage />} />
              <Route path="knowledge" element={<KnowledgePage />} />
              <Route path="teams" element={<TeamsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* 默认重定向 */}
            <Route path="/" element={<Navigate to="/console" replace />} />
            <Route path="*" element={<Navigate to="/console" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
