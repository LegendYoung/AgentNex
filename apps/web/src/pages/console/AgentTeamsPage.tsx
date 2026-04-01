/**
 * Agent Teams 管理页面
 * P1阶段：多智能体团队管理
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { AgentTeam } from '@/api/agentTeams';
import { listAgentTeams, deleteAgentTeam } from '@/api/agentTeams';
import { cn } from '@workspace/ui/lib/utils';
import {
  Users,
  Plus,
  Search,
  Trash2,
  Edit,
  Play,
  Download,
  MoreVertical,
  Loader2,
} from 'lucide-react';

export function AgentTeamsPage() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<AgentTeam[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [visibility, setVisibility] = useState<'all' | 'my' | 'shared'>('all');

  // 加载团队列表
  useEffect(() => {
    loadTeams();
  }, [visibility]);

  const loadTeams = async () => {
    setIsLoading(true);
    try {
      const result = await listAgentTeams({ visibility, search: searchQuery || undefined });
      setTeams(result.items);
    } catch (error) {
      console.error('Failed to load teams:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 搜索
  const handleSearch = () => {
    loadTeams();
  };

  // 删除团队
  const handleDelete = async (teamId: string) => {
    if (!confirm('确定要删除这个团队吗？此操作不可恢复。')) return;

    try {
      await deleteAgentTeam(teamId);
      setTeams(teams.filter(t => t.team_id !== teamId));
    } catch (error) {
      console.error('Failed to delete team:', error);
      alert('删除失败');
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <div className="border-b p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Agent Teams</h1>
            <p className="text-sm text-muted-foreground">多智能体团队编排与管理</p>
          </div>
          <button
            onClick={() => navigate('/console/agent-teams/create')}
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            创建团队
          </button>
        </div>

        {/* 搜索和筛选 */}
        <div className="mt-4 flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索团队..."
              className="w-full rounded-md border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setVisibility('all')}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                visibility === 'all' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              )}
            >
              全部
            </button>
            <button
              onClick={() => setVisibility('my')}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                visibility === 'my' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              )}
            >
              我的
            </button>
            <button
              onClick={() => setVisibility('shared')}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                visibility === 'shared' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              )}
            >
              共享
            </button>
          </div>
        </div>
      </div>

      {/* 团队列表 */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : teams.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
            <Users className="h-16 w-16 mb-4" />
            <p className="text-lg font-medium">暂无团队</p>
            <p className="text-sm">点击"创建团队"开始构建你的多智能体团队</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {teams.map((team) => (
              <TeamCard
                key={team.team_id}
                team={team}
                onEdit={() => navigate(`/console/agent-teams/${team.team_id}`)}
                onRun={() => navigate(`/console/agent-teams/${team.team_id}/run`)}
                onDelete={() => handleDelete(team.team_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// 团队卡片组件
interface TeamCardProps {
  team: AgentTeam;
  onEdit: () => void;
  onRun: () => void;
  onDelete: () => void;
}

function TeamCard({ team, onEdit, onRun, onDelete }: TeamCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="rounded-lg border bg-card p-4 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Users className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold">{team.name}</h3>
            <p className="text-xs text-muted-foreground">
              {team.node_count || 0} 个Agent
            </p>
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="rounded p-1 hover:bg-accent"
          >
            <MoreVertical className="h-4 w-4" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-full z-10 mt-1 w-36 rounded-md border bg-background py-1 shadow-lg">
              <button
                onClick={() => { setShowMenu(false); onEdit(); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                <Edit className="h-4 w-4" />
                编辑配置
              </button>
              <button
                onClick={() => { setShowMenu(false); onRun(); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                <Play className="h-4 w-4" />
                运行测试
              </button>
              <button
                onClick={() => setShowMenu(false)}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                <Download className="h-4 w-4" />
                导出配置
              </button>
              <div className="my-1 border-t" />
              <button
                onClick={() => { setShowMenu(false); onDelete(); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-destructive hover:bg-accent"
              >
                <Trash2 className="h-4 w-4" />
                删除团队
              </button>
            </div>
          )}
        </div>
      </div>

      <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
        {team.description || team.goal}
      </p>

      <div className="mt-4 flex items-center gap-2">
        <span className={cn(
          'rounded-full px-2 py-0.5 text-xs',
          team.is_public ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
        )}>
          {team.is_public ? '公开' : '私有'}
        </span>
        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
          {team.decision_mode === 'voting' ? '投票制' : 
           team.decision_mode === 'leader' ? '负责人制' : '一致通过'}
        </span>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={onEdit}
          className="flex-1 rounded-md border py-1.5 text-sm font-medium hover:bg-accent"
        >
          编辑画布
        </button>
        <button
          onClick={onRun}
          className="flex-1 rounded-md bg-primary py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          运行团队
        </button>
      </div>
    </div>
  );
}

export default AgentTeamsPage;
