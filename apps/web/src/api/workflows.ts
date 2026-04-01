/**
 * Workflows API 客户端
 * P2阶段：工作流引擎管理
 */

import { apiClient } from './client';

// ==================== 类型定义 ====================

export type WorkflowTriggerType = 'manual' | 'api' | 'schedule' | 'webhook' | 'event';
export type WorkflowNodeType = 'start' | 'end' | 'agent' | 'team' | 'condition' | 'loop' | 'parallel' | 'human_input' | 'code' | 'api_call' | 'delay';
export type WorkflowStatus = 'draft' | 'active' | 'archived';
export type ExecutionStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'timeout';

export interface WorkflowVariable {
  name: string;
  type: string;
  default_value?: unknown;
  description?: string;
  required: boolean;
}

export interface WorkflowNodeConfig {
  // Agent 节点
  agent_id?: string;
  input_mapping?: Record<string, string>;
  output_mapping?: Record<string, string>;
  timeout_seconds?: number;
  
  // Team 节点
  team_id?: string;
  
  // Condition 节点
  branches?: Array<{
    label: string;
    expression: string;
    target_node_id?: string;
  }>;
  default_branch?: string;
  
  // Loop 节点
  loop_var?: string;
  iterable_expression?: string;
  max_iterations?: number;
  body_start_node_id?: string;
  
  // Parallel 节点
  parallel_branches?: string[];
  wait_all?: boolean;
  
  // Human Input 节点
  prompt?: string;
  input_type?: 'text' | 'select' | 'multiselect' | 'file';
  options?: string[];
  default_value?: string;
  timeout_action?: 'default' | 'fail' | 'skip';
  
  // Code 节点
  language?: 'python' | 'javascript';
  code?: string;
  
  // API Call 节点
  url?: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: Record<string, unknown>;
  
  // Delay 节点
  delay_seconds?: number;
  delay_until?: string;
}

export interface CanvasWorkflowNode {
  node_id?: string;
  node_type: WorkflowNodeType;
  label?: string;
  description?: string;
  position: { x: number; y: number };
  config: WorkflowNodeConfig;
}

export interface CanvasWorkflowEdge {
  edge_id?: string;
  source_node_id: string;
  target_node_id: string;
  label?: string;
  condition_type?: 'always' | 'expression' | 'output_match';
  condition_value?: string;
}

export interface Workflow {
  workflow_id: string;
  name: string;
  description?: string;
  trigger_type: WorkflowTriggerType;
  trigger_config: Record<string, unknown>;
  variables: WorkflowVariable[];
  status: WorkflowStatus;
  is_public: boolean;
  version: number;
  execution_count: number;
  last_execution_at?: string;
  creator?: {
    user_id: string;
    name: string;
    email: string;
  };
  created_at: string;
  updated_at: string;
}

export interface WorkflowDetail extends Workflow {
  nodes: CanvasWorkflowNode[];
  edges: CanvasWorkflowEdge[];
}

export interface WorkflowExecution {
  execution_id: string;
  workflow_id: string;
  status: ExecutionStatus;
  current_node_id?: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  variables: Record<string, unknown>;
  error_message?: string;
  error_node_id?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface ExecutionLog {
  log_id: string;
  node_id?: string;
  node_type?: string;
  node_label?: string;
  event_type: string;
  message?: string;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error_message?: string;
  duration_ms?: number;
  timestamp: string;
}

export interface WorkflowExecutionDetail extends WorkflowExecution {
  logs: ExecutionLog[];
}

export interface CreateWorkflowRequest {
  name: string;
  description?: string;
  trigger_type?: WorkflowTriggerType;
  trigger_config?: Record<string, unknown>;
  variables?: WorkflowVariable[];
  is_public?: boolean;
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  trigger_type?: WorkflowTriggerType;
  trigger_config?: Record<string, unknown>;
  variables?: WorkflowVariable[];
  status?: WorkflowStatus;
  is_public?: boolean;
}

export interface SaveWorkflowCanvasRequest {
  nodes: CanvasWorkflowNode[];
  edges: CanvasWorkflowEdge[];
}

export interface RunWorkflowRequest {
  input_data?: Record<string, unknown>;
  variables?: Record<string, unknown>;
}

// ==================== API 函数 ====================

/**
 * 创建工作流
 */
export async function createWorkflow(data: CreateWorkflowRequest): Promise<Workflow> {
  const response = await apiClient.post<Workflow>('/api/v1/workflows', data);
  return response.data.data;
}

/**
 * 获取工作流列表
 */
export async function listWorkflows(params?: {
  page?: number;
  page_size?: number;
  status?: WorkflowStatus;
  search?: string;
}): Promise<{ items: Workflow[]; total: number; page: number; page_size: number }> {
  const response = await apiClient.get<{ items: Workflow[]; total: number; page: number; page_size: number }>('/api/v1/workflows', { params });
  return response.data.data;
}

/**
 * 获取工作流详情
 */
export async function getWorkflow(workflowId: string): Promise<WorkflowDetail> {
  const response = await apiClient.get<WorkflowDetail>(`/api/v1/workflows/${workflowId}`);
  return response.data.data;
}

/**
 * 更新工作流
 */
export async function updateWorkflow(workflowId: string, data: UpdateWorkflowRequest): Promise<Workflow> {
  const response = await apiClient.put<Workflow>(`/api/v1/workflows/${workflowId}`, data);
  return response.data.data;
}

/**
 * 删除工作流
 */
export async function deleteWorkflow(workflowId: string): Promise<void> {
  await apiClient.delete<void>(`/api/v1/workflows/${workflowId}`);
}

/**
 * 保存工作流画布
 */
export async function saveWorkflowCanvas(workflowId: string, data: SaveWorkflowCanvasRequest): Promise<void> {
  await apiClient.post<void>(`/api/v1/workflows/${workflowId}/canvas`, data);
}

/**
 * 获取工作流画布
 */
export async function getWorkflowCanvas(workflowId: string): Promise<{ nodes: CanvasWorkflowNode[]; edges: CanvasWorkflowEdge[] }> {
  const response = await apiClient.get<{ nodes: CanvasWorkflowNode[]; edges: CanvasWorkflowEdge[] }>(`/api/v1/workflows/${workflowId}/canvas`);
  return response.data.data;
}

/**
 * 激活工作流
 */
export async function activateWorkflow(workflowId: string): Promise<void> {
  await apiClient.post<void>(`/api/v1/workflows/${workflowId}/activate`);
}

/**
 * 停用工作流
 */
export async function deactivateWorkflow(workflowId: string): Promise<void> {
  await apiClient.post<void>(`/api/v1/workflows/${workflowId}/deactivate`);
}

/**
 * 获取工作流运行 URL（SSE）
 */
export function getWorkflowRunUrl(workflowId: string): string {
  const baseUrl = apiClient.defaults.baseURL || '';
  return `${baseUrl}/api/v1/workflows/${workflowId}/run`;
}

/**
 * 获取执行历史
 */
export async function listWorkflowExecutions(
  workflowId: string,
  params?: { page?: number; page_size?: number; status?: ExecutionStatus }
): Promise<{ items: WorkflowExecution[]; total: number; page: number; page_size: number }> {
  const response = await apiClient.get<{ items: WorkflowExecution[]; total: number; page: number; page_size: number }>(`/api/v1/workflows/${workflowId}/executions`, { params });
  return response.data.data;
}

/**
 * 获取执行详情
 */
export async function getExecutionDetail(executionId: string): Promise<WorkflowExecutionDetail> {
  const response = await apiClient.get<WorkflowExecutionDetail>(`/api/v1/workflows/executions/${executionId}`);
  return response.data.data;
}

/**
 * 继续执行工作流（提供人工输入）
 */
export async function continueWorkflow(data: { execution_id: string; node_id: string; input_value: unknown }): Promise<void> {
  await apiClient.post<void>('/api/v1/workflows/continue', data);
}

/**
 * 导出工作流
 */
export async function exportWorkflow(workflowId: string, format: 'json' | 'python' = 'json'): Promise<Blob> {
  const token = localStorage.getItem('agentnex_access_token');
  const response = await fetch(`${apiClient.defaults.baseURL}/api/v1/workflows/${workflowId}/export?format=${format}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.blob();
}

/**
 * 导入工作流
 */
export async function importWorkflow(file: File): Promise<Workflow> {
  const formData = new FormData();
  formData.append('file', file);
  const token = localStorage.getItem('agentnex_access_token');
  const response = await fetch(`${apiClient.defaults.baseURL}/api/v1/workflows/import`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });
  const data = await response.json();
  return data.data;
}
