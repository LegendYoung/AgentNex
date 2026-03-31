/**
 * Agent 详情页面
 * 查看、编辑、测试 Agent
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAgent, updateAgent, deleteAgent, copyAgent, toggleAgent } from '@/api/agents';
import type { Agent, AgentConfig } from '@/types';
import { cn } from '@workspace/ui/lib/utils';
import {
  ArrowLeft,
  Pencil,
  Trash2,
  Copy,
  Power,
  Download,
  Settings,
  MessageSquare,
  Loader2,
} from 'lucide-react';

type TabType = 'overview' | 'config' | 'test';

export function AgentDetailPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState<AgentConfig | null>(null);

  // 加载 Agent 详情
  useEffect(() => {
    loadAgent();
  }, [agentId]);

  const loadAgent = async () => {
    if (!agentId) return;
    setIsLoading(true);
    try {
      const data = await getAgent(agentId);
      setAgent(data);
      setEditedConfig(data);
    } catch (error) {
      console.error('Failed to load agent:', error);
      alert('加载 Agent 失败');
      navigate('/console/agents');
    } finally {
      setIsLoading(false);
    }
  };

  // 复制 Agent
  const handleCopy = async () => {
    if (!agentId) return;
    if (!confirm('确定要复制此 Agent 吗？')) return;
    try {
      const result = await copyAgent(agentId);
      alert(`Agent "${result.name}" 已复制`);
      navigate(`/console/agents/${result.agent_id}`);
    } catch (error) {
      console.error('Failed to copy agent:', error);
      alert('复制失败');
    }
  };

  // 启停 Agent
  const handleToggle = async () => {
    if (!agent) return;
    try {
      await toggleAgent(agentId!, !agent.is_active);
      setAgent({ ...agent, is_active: !agent.is_active });
    } catch (error) {
      console.error('Failed to toggle agent:', error);
      alert('操作失败');
    }
  };

  // 删除 Agent
  const handleDelete = async () => {
    if (!agentId) return;
    if (!confirm('确定要删除此 Agent 吗？此操作不可恢复。')) return;
    try {
      await deleteAgent(agentId);
      alert('Agent 已删除');
      navigate('/console/agents');
    } catch (error) {
      console.error('Failed to delete agent:', error);
      alert('删除失败');
    }
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    if (!agentId || !editedConfig) return;
    try {
      await updateAgent(agentId, editedConfig);
      setAgent({ ...agent!, ...editedConfig });
      setIsEditing(false);
      alert('保存成功');
    } catch (error) {
      console.error('Failed to update agent:', error);
      alert('保存失败');
    }
  };

  // 导出代码
  const handleExport = () => {
    navigate(`/console/agents/${agentId}/export`);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Agent 不存在
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/console/agents')}
            className="rounded-md p-2 hover:bg-accent"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">{agent.name}</h1>
              <div
                className={cn(
                  'rounded px-2 py-0.5 text-xs font-medium',
                  agent.is_active
                    ? 'bg-green-500/10 text-green-600'
                    : 'bg-gray-500/10 text-gray-600'
                )}
              >
                {agent.is_active ? '运行中' : '已停用'}
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              {agent.description || '暂无描述'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleToggle}
            className={cn(
              'flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium',
              agent.is_active ? 'hover:bg-accent' : 'bg-primary text-primary-foreground hover:bg-primary/90'
            )}
          >
            <Power className="h-4 w-4" />
            {agent.is_active ? '停用' : '启用'}
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            <Copy className="h-4 w-4" />
            复制
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            <Download className="h-4 w-4" />
            导出
          </button>
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 rounded-md border border-destructive px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive hover:text-destructive-foreground"
          >
            <Trash2 className="h-4 w-4" />
            删除
          </button>
        </div>
      </header>

      {/* 标签页 */}
      <div className="border-b">
        <div className="flex gap-4 px-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={cn(
              'border-b-2 py-3 text-sm font-medium',
              activeTab === 'overview'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            概览
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={cn(
              'border-b-2 py-3 text-sm font-medium',
              activeTab === 'config'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            配置
          </button>
          <button
            onClick={() => setActiveTab('test')}
            className={cn(
              'border-b-2 py-3 text-sm font-medium',
              activeTab === 'test'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            测试
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === 'overview' && (
          <OverviewTab agent={agent} onEdit={() => setActiveTab('config')} />
        )}
        {activeTab === 'config' && (
          <ConfigTab
            agent={agent}
            editedConfig={editedConfig}
            setEditedConfig={setEditedConfig}
            isEditing={isEditing}
            setIsEditing={setIsEditing}
            onSave={handleSaveEdit}
          />
        )}
        {activeTab === 'test' && (
          <TestTab agent={agent} />
        )}
      </div>
    </div>
  );
}

// 概览标签页
function OverviewTab({ agent, onEdit }: { agent: Agent; onEdit: () => void }) {
  return (
    <div className="space-y-6">
      {/* 基本信息 */}
      <div className="rounded-lg border p-4">
        <h3 className="mb-3 font-semibold">基本信息</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">创建者：</span>
            <span>{agent.creator.name || agent.creator.email}</span>
          </div>
          <div>
            <span className="text-muted-foreground">创建时间：</span>
            <span>{new Date(agent.created_at).toLocaleString()}</span>
          </div>
          <div>
            <span className="text-muted-foreground">模型：</span>
            <span>{agent.model_id}</span>
          </div>
          <div>
            <span className="text-muted-foreground">可见性：</span>
            <span>{agent.is_public ? '公开' : '私有'}</span>
          </div>
        </div>
      </div>

      {/* 系统提示词 */}
      <div className="rounded-lg border p-4">
        <h3 className="mb-3 font-semibold">系统提示词</h3>
        <pre className="whitespace-pre-wrap rounded bg-muted p-3 text-sm">
          {agent.system_prompt}
        </pre>
      </div>

      {/* 能力配置 */}
      <div className="rounded-lg border p-4">
        <h3 className="mb-3 font-semibold">能力配置</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-lg border p-3">
            <div className="font-medium">记忆</div>
            <div className="mt-1 text-sm text-muted-foreground">
              {agent.enable_memory
                ? `${agent.memory_type === 'long_term' ? '长期' : '短期'} (${agent.memory_window}轮)`
                : '未启用'}
            </div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="font-medium">知识库</div>
            <div className="mt-1 text-sm text-muted-foreground">
              {agent.enable_knowledge
                ? `${agent.knowledge_base_ids.length} 个`
                : '未启用'}
            </div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="font-medium">工具</div>
            <div className="mt-1 text-sm text-muted-foreground">
              {agent.enable_tools ? '已启用' : '未启用'}
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={onEdit}
        className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        <Pencil className="h-4 w-4" />
        编辑配置
      </button>
    </div>
  );
}

// 配置标签页
function ConfigTab({
  agent,
  editedConfig,
  setEditedConfig,
  isEditing,
  setIsEditing,
  onSave,
}: {
  agent: Agent;
  editedConfig: AgentConfig | null;
  setEditedConfig: (config: AgentConfig | null) => void;
  isEditing: boolean;
  setIsEditing: (editing: boolean) => void;
  onSave: () => void;
}) {
  if (!editedConfig) return null;

  return (
    <div className="space-y-6">
      <div className="flex justify-between">
        <h3 className="text-lg font-semibold">Agent 配置</h3>
        {!isEditing ? (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            <Pencil className="h-4 w-4" />
            编辑
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => {
                setIsEditing(false);
                setEditedConfig(agent);
              }}
              className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              取消
            </button>
            <button
              onClick={onSave}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              保存
            </button>
          </div>
        )}
      </div>

      {/* 配置表单 */}
      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="mb-2 block text-sm font-medium">名称</label>
          <input
            type="text"
            value={editedConfig.name}
            onChange={(e) =>
              setEditedConfig({ ...editedConfig, name: e.target.value })
            }
            disabled={!isEditing}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50"
          />
        </div>
        <div>
          <label className="mb-2 block text-sm font-medium">模型</label>
          <input
            type="text"
            value={editedConfig.model_id}
            disabled
            className="w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50"
          />
        </div>
        <div className="col-span-2">
          <label className="mb-2 block text-sm font-medium">描述</label>
          <input
            type="text"
            value={editedConfig.description || ''}
            onChange={(e) =>
              setEditedConfig({ ...editedConfig, description: e.target.value })
            }
            disabled={!isEditing}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50"
          />
        </div>
        <div className="col-span-2">
          <label className="mb-2 block text-sm font-medium">系统提示词</label>
          <textarea
            value={editedConfig.system_prompt}
            onChange={(e) =>
              setEditedConfig({ ...editedConfig, system_prompt: e.target.value })
            }
            disabled={!isEditing}
            rows={6}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50"
          />
        </div>
      </div>
    </div>
  );
}

// 测试标签页
function TestTab({ agent }: { agent: Agent }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, { role: 'user', content: input }]);
    setInput('');
    // TODO: 调用测试 API
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '这是一个测试回复（API 待集成）' },
      ]);
    }, 500);
  };

  return (
    <div className="flex h-[500px] flex-col">
      <h3 className="mb-4 text-lg font-semibold">测试 Agent</h3>

      {/* 对话区域 */}
      <div className="flex-1 overflow-auto rounded-lg border bg-muted/30 p-4">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            输入消息开始测试
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  'rounded-lg p-3',
                  msg.role === 'user'
                    ? 'ml-auto max-w-[80%] bg-primary text-primary-foreground'
                    : 'max-w-[100%] bg-background'
                )}
              >
                {msg.content}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="输入测试消息..."
          className="flex-1 rounded-md border bg-background px-4 py-2 text-sm"
        />
        <button
          onClick={handleSend}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          发送
        </button>
      </div>
    </div>
  );
}
