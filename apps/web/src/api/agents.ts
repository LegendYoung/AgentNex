/**
 * Agent 管理 API
 */

import { api } from './client';
import type {
  Agent,
  AgentConfig,
  AgentListItem,
  AgentTestRequest,
  AgentTestResult,
  Draft,
  PaginatedResponse,
} from '@/types';

interface CreateAgentResponse {
  success: boolean;
  data: {
    agent_id: string;
    name: string;
    created_at: string;
  };
}

interface DraftResponse {
  success: boolean;
  data: {
    draft_id: string;
    expires_at: string;
    created_at?: string;
  };
}

interface DraftListResponse {
  success: boolean;
  data: {
    drafts: Draft[];
    total: number;
  };
}

interface DraftDetailResponse {
  success: boolean;
  data: Draft & AgentConfig;
}

interface AgentListResponse {
  success: boolean;
  data: PaginatedResponse<AgentListItem>;
}

interface AgentResponse {
  success: boolean;
  data: Agent;
}

interface TestResponse {
  success: boolean;
  data: AgentTestResult;
}

interface MessageResponse {
  success: boolean;
  message: string;
}

interface CopyResponse {
  success: boolean;
  data: {
    agent_id: string;
    name: string;
  };
}

/**
 * 创建 Agent
 */
export async function createAgent(config: AgentConfig): Promise<CreateAgentResponse['data']> {
  const response = await api.post<CreateAgentResponse>('/api/v1/agents', config);
  return response.data;
}

/**
 * 保存草稿
 */
export async function saveDraft(config: AgentConfig): Promise<DraftResponse['data']> {
  const response = await api.post<DraftResponse>('/api/v1/agents/draft', config);
  return response.data;
}

/**
 * 获取草稿列表
 */
export async function listDrafts(): Promise<Draft[]> {
  const response = await api.get<DraftListResponse>('/api/v1/agents/draft');
  return response.data.drafts;
}

/**
 * 获取草稿详情
 */
export async function getDraft(draftId: string): Promise<Draft & AgentConfig> {
  const response = await api.get<DraftDetailResponse>(`/api/v1/agents/draft/${draftId}`);
  return response.data;
}

/**
 * 删除草稿
 */
export async function deleteDraft(draftId: string): Promise<void> {
  await api.delete<MessageResponse>(`/api/v1/agents/draft/${draftId}`);
}

/**
 * 测试 Agent
 */
export async function testAgent(request: AgentTestRequest): Promise<AgentTestResult> {
  const response = await api.post<TestResponse>('/api/v1/agents/test', request);
  return response.data;
}

/**
 * 获取 Agent 列表
 */
export async function listAgents(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  visibility?: 'all' | 'my' | 'shared';
}): Promise<PaginatedResponse<AgentListItem>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.search) searchParams.set('search', params.search);
  if (params?.visibility) searchParams.set('visibility', params.visibility);

  const query = searchParams.toString();
  const endpoint = query ? `/api/v1/agents?${query}` : '/api/v1/agents';

  const response = await api.get<AgentListResponse>(endpoint);
  return response.data;
}

/**
 * 获取 Agent 详情
 */
export async function getAgent(agentId: string): Promise<Agent> {
  const response = await api.get<AgentResponse>(`/api/v1/agents/${agentId}`);
  return response.data;
}

/**
 * 更新 Agent
 */
export async function updateAgent(agentId: string, config: AgentConfig): Promise<void> {
  await api.put<MessageResponse>(`/api/v1/agents/${agentId}`, config);
}

/**
 * 删除 Agent
 */
export async function deleteAgent(agentId: string): Promise<void> {
  await api.delete<MessageResponse>(`/api/v1/agents/${agentId}`);
}

/**
 * 复制 Agent
 */
export async function copyAgent(agentId: string): Promise<CopyResponse['data']> {
  const response = await api.post<CopyResponse>(`/api/v1/agents/${agentId}/copy`);
  return response.data;
}

/**
 * 启停 Agent
 */
export async function toggleAgent(agentId: string, isActive: boolean): Promise<void> {
  await api.post<MessageResponse>(`/api/v1/agents/${agentId}/toggle`, { is_active: isActive });
}
