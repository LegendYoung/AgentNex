// Agent 相关类型定义

export interface ToolConfig {
  web_search: boolean;
  file_read: boolean;
  python_exec: boolean;
  permission: 'all' | 'allow_only' | 'deny_only';
}

export interface TeamPermissionConfig {
  team_id: string;
  permission: 'view' | 'edit' | 'manage';
}

export interface AgentConfig {
  name: string;
  description?: string;
  avatar_url?: string;
  system_prompt: string;
  model_id: string;
  temperature: number; // 0-200, 存储时乘100
  top_p: number; // 0-100
  enable_memory: boolean;
  memory_type: 'short_term' | 'long_term';
  memory_window: number;
  enable_knowledge: boolean;
  knowledge_base_ids: string[];
  enable_tools: boolean;
  tool_config?: ToolConfig;
  is_public: boolean;
  team_permissions?: TeamPermissionConfig[];
}

export interface Agent extends AgentConfig {
  agent_id: string;
  is_active: boolean;
  creator: {
    user_id: string;
    name: string;
    email: string;
  };
  created_at: string;
  updated_at: string;
}

export interface AgentListItem {
  agent_id: string;
  name: string;
  description?: string;
  model_id: string;
  is_public: boolean;
  is_active: boolean;
  creator: {
    user_id: string;
    name: string;
    email: string;
  };
  created_at: string;
  updated_at: string;
}

export interface Draft {
  draft_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  expires_at: string;
}

export interface AgentTestRequest {
  agent_config: AgentConfig;
  message: string;
  session_id?: string;
}

export interface AgentTestResult {
  response: string;
  tool_calls: Array<{
    tool: string;
    input: string;
    output: string;
    timestamp: string;
  }>;
  knowledge_retrieved: Array<{
    content: string;
    similarity: number;
    document: string;
  }>;
  memory_used: Array<{
    memory_id: string;
    content: string;
  }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
