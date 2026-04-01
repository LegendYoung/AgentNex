/**
 * Agent Teams API 客户端
 * P1阶段：多智能体团队管理
 */

import { apiClient } from './client';

// ==================== 类型定义 ====================

export interface TeamConfig {
  max_rounds: number;
  timeout_minutes: number;
  entry_agent_id?: string;
  global_prompt?: string;
}

export interface AgentTeamNodeConfig {
  role_in_team?: string;
  responsibilities?: string;
  allowed_tools: string[];
  can_call_agents: string[];
}

export interface CanvasNode {
  node_id?: string;
  agent_id: string;
  agent_name?: string;
  position: { x: number; y: number };
  config: AgentTeamNodeConfig;
}

export interface CanvasEdgeCondition {
  type: string;
  value?: string;
}

export interface CanvasEdge {
  edge_id?: string;
  source_node_id: string;
  target_node_id: string;
  condition?: CanvasEdgeCondition;
}

export interface AgentTeam {
  team_id: string;
  name: string;
  description?: string;
  goal: string;
  team_config: TeamConfig;
  communication_mode: 'broadcast' | 'point_to_point' | 'topic_based';
  decision_mode: 'voting' | 'leader' | 'unanimous';
  is_public: boolean;
  is_active: boolean;
  creator?: {
    user_id: string;
    name: string;
    email: string;
  };
  node_count?: number;
  nodes?: CanvasNode[];
  edges?: CanvasEdge[];
  created_at: string;
  updated_at: string;
}

export interface CreateAgentTeamRequest {
  name: string;
  description?: string;
  goal: string;
  team_config?: TeamConfig;
  communication_mode?: 'broadcast' | 'point_to_point' | 'topic_based';
  decision_mode?: 'voting' | 'leader' | 'unanimous';
}

export interface UpdateAgentTeamRequest {
  name?: string;
  description?: string;
  goal?: string;
  team_config?: TeamConfig;
  communication_mode?: 'broadcast' | 'point_to_point' | 'topic_based';
  decision_mode?: 'unanimous' | 'leader' | 'voting';
  is_public?: boolean;
  is_active?: boolean;
}

export interface SaveCanvasRequest {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
}

export interface TeamSession {
  session_id: string;
  team_id: string;
  status: string;
  messages: TeamMessage[];
  task_status: Record<string, any>;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface TeamMessage {
  role: 'user' | 'assistant' | 'system';
  agent_id?: string;
  agent_name?: string;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

// ==================== API 函数 ====================

/**
 * 创建Agent团队
 */
export async function createAgentTeam(data: CreateAgentTeamRequest): Promise<AgentTeam> {
  const response = await apiClient.post<AgentTeam>('/api/v1/agent-teams', data);
  return response.data.data;
}

/**
 * 获取Agent团队列表
 */
export async function listAgentTeams(params?: {
  page?: number;
  page_size?: number;
  visibility?: 'all' | 'my' | 'shared';
  search?: string;
}): Promise<{ items: AgentTeam[]; total: number; page: number; page_size: number }> {
  const response = await apiClient.get<{ items: AgentTeam[]; total: number; page: number; page_size: number }>('/api/v1/agent-teams', { params });
  return response.data.data;
}

/**
 * 获取Agent团队详情
 */
export async function getAgentTeam(teamId: string): Promise<AgentTeam> {
  const response = await apiClient.get<AgentTeam>(`/api/v1/agent-teams/${teamId}`);
  return response.data.data;
}

/**
 * 更新Agent团队
 */
export async function updateAgentTeam(teamId: string, data: UpdateAgentTeamRequest): Promise<AgentTeam> {
  const response = await apiClient.put<AgentTeam>(`/api/v1/agent-teams/${teamId}`, data);
  return response.data.data;
}

/**
 * 删除Agent团队
 */
export async function deleteAgentTeam(teamId: string): Promise<void> {
  await apiClient.delete<void>(`/api/v1/agent-teams/${teamId}`);
}

/**
 * 保存画布配置
 */
export async function saveCanvas(teamId: string, data: SaveCanvasRequest): Promise<void> {
  await apiClient.post<void>(`/api/v1/agent-teams/${teamId}/canvas`, data);
}

/**
 * 获取画布配置
 */
export async function getCanvas(teamId: string): Promise<{ nodes: CanvasNode[]; edges: CanvasEdge[] }> {
  const response = await apiClient.get<{ nodes: CanvasNode[]; edges: CanvasEdge[] }>(`/api/v1/agent-teams/${teamId}/canvas`);
  return response.data.data;
}

/**
 * 运行团队任务（返回SSE URL）
 */
export function getTeamRunUrl(teamId: string): string {
  const baseUrl = apiClient.defaults.baseURL || '';
  return `${baseUrl}/api/v1/agent-teams/${teamId}/run`;
}

/**
 * 获取团队对话历史
 */
export async function listTeamSessions(
  teamId: string,
  params?: { page?: number; page_size?: number }
): Promise<{ items: TeamSession[]; total: number; page: number; page_size: number }> {
  const response = await apiClient.get<{ items: TeamSession[]; total: number; page: number; page_size: number }>(`/api/v1/agent-teams/${teamId}/sessions`, { params });
  return response.data.data;
}

/**
 * 导出团队配置
 */
export async function exportTeam(teamId: string, format: 'json' | 'python' = 'json'): Promise<Blob> {
  const token = localStorage.getItem('agentnex_access_token');
  const response = await fetch(`${apiClient.defaults.baseURL}/api/v1/agent-teams/${teamId}/export?format=${format}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.blob();
}

/**
 * 导入团队配置
 */
export async function importTeam(file: File): Promise<AgentTeam> {
  const formData = new FormData();
  formData.append('file', file);
  const token = localStorage.getItem('agentnex_access_token');
  const response = await fetch(`${apiClient.defaults.baseURL}/api/v1/agent-teams/import`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });
  const data = await response.json();
  return data.data;
}
