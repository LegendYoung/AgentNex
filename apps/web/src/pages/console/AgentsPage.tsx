/**
 * Agent 列表页面
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listAgents } from '@/api/agents';
import type { AgentListItem, PaginatedResponse } from '@/types';
import { Bot, Plus, Search, MoreVertical, Power, Copy, Trash2, Pencil } from 'lucide-react';
import { cn } from '@workspace/ui/lib/utils';

export function AgentsPage() {
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [visibility, setVisibility] = useState<'all' | 'my' | 'shared'>('all');

  const loadAgents = async () => {
    setIsLoading(true);
    try {
      const result: PaginatedResponse<AgentListItem> = await listAgents({
        page,
        page_size: 12,
        search: search || undefined,
        visibility,
      });
      setAgents(result.items);
      setTotal(result.total);
    } catch (err) {
      console.error('Failed to load agents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, [page, visibility]);

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-2xl font-bold">Agent 管理</h1>
          <p className="text-sm text-muted-foreground">创建、管理和测试您的智能 Agent</p>
        </div>
        <Link
          to="/console/agents/create"
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          新建 Agent
        </Link>
      </header>

      {/* 工具栏 */}
      <div className="flex items-center gap-4 border-b px-6 py-3">
        {/* 搜索 */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadAgents()}
            placeholder="搜索 Agent..."
            className="w-full rounded-md border bg-background py-2 pl-9 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* 筛选 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setVisibility('all')}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm transition-colors',
              visibility === 'all' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
            )}
          >
            全部
          </button>
          <button
            onClick={() => setVisibility('my')}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm transition-colors',
              visibility === 'my' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
            )}
          >
            我的
          </button>
          <button
            onClick={() => setVisibility('shared')}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm transition-colors',
              visibility === 'shared' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
            )}
          >
            共享
          </button>
        </div>
      </div>

      {/* 列表 */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : agents.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
            <Bot className="h-16 w-16 mb-4" />
            <p className="text-lg font-medium">暂无 Agent</p>
            <p className="text-sm">点击"新建 Agent"创建您的第一个智能助手</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <AgentCard key={agent.agent_id} agent={agent} onRefresh={loadAgents} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AgentCard({
  agent,
  onRefresh,
}: {
  agent: AgentListItem;
  onRefresh: () => void;
}) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="group relative rounded-lg border bg-card p-4 transition-shadow hover:shadow-md">
      {/* 状态指示 */}
      <div
        className={cn(
          'absolute right-3 top-3 h-2 w-2 rounded-full',
          agent.is_active ? 'bg-green-500' : 'bg-gray-400'
        )}
      />

      {/* 图标 */}
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
        <Bot className="h-6 w-6 text-primary" />
      </div>

      {/* 信息 */}
      <h3 className="font-semibold">{agent.name}</h3>
      <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
        {agent.description || '暂无描述'}
      </p>

      {/* 底部信息 */}
      <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
        <span>{agent.model_id}</span>
        <span>{agent.is_public ? '公开' : '私有'}</span>
      </div>

      {/* 操作按钮 */}
      <div className="absolute bottom-4 right-4 opacity-0 transition-opacity group-hover:opacity-100">
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="rounded-md p-1.5 hover:bg-accent"
          >
            <MoreVertical className="h-4 w-4" />
          </button>

          {showMenu && (
            <div className="absolute bottom-full right-0 mb-1 w-32 rounded-md border bg-popover py-1 shadow-lg">
              <button
                onClick={() => setShowMenu(false)}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                <Pencil className="h-3 w-3" />
                编辑
              </button>
              <button
                onClick={() => setShowMenu(false)}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                <Copy className="h-3 w-3" />
                复制
              </button>
              <button
                onClick={() => setShowMenu(false)}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                <Power className="h-3 w-3" />
                {agent.is_active ? '停用' : '启用'}
              </button>
              <button
                onClick={() => setShowMenu(false)}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-destructive hover:bg-accent"
              >
                <Trash2 className="h-3 w-3" />
                删除
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
