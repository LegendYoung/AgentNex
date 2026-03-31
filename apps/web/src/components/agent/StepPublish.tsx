/**
 * 步骤4：发布确认
 * 权限配置、发布 Agent
 */

import { useState, useEffect } from 'react';
import type { AgentConfig, TeamPermissionConfig } from '@/types';
import { cn } from '@workspace/ui/lib/utils';
import { ChevronLeft, Rocket, Loader2, Check } from 'lucide-react';

interface StepPublishProps {
  config: AgentConfig;
  updateConfig: (updates: Partial<AgentConfig>) => void;
  onPublish: () => void;
  onPrev: () => void;
  isSaving: boolean;
}

// 模拟团队数据
const MOCK_TEAMS = [
  { id: 'team-1', name: '产品团队', member_count: 8 },
  { id: 'team-2', name: '技术团队', member_count: 15 },
  { id: 'team-3', name: '运营团队', member_count: 6 },
];

export function StepPublish({
  config,
  updateConfig,
  onPublish,
  onPrev,
  isSaving,
}: StepPublishProps) {
  const [teams, setTeams] = useState(MOCK_TEAMS);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [selectedPermission, setSelectedPermission] = useState<'view' | 'edit' | 'manage'>(
    'view'
  );

  // 权限选项说明
  const PERMISSION_LABELS = {
    view: { label: '查看', desc: '仅可查看 Agent 配置和对话' },
    edit: { label: '编辑', desc: '可修改 Agent 配置' },
    manage: { label: '管理', desc: '可修改配置和管理权限' },
  };

  // 添加团队权限
  const addTeamPermission = () => {
    if (!selectedTeam) return;

    // 检查是否已存在
    const exists = config.team_permissions?.some((p) => p.team_id === selectedTeam);
    if (exists) {
      alert('该团队已添加');
      return;
    }

    const newPermission: TeamPermissionConfig = {
      team_id: selectedTeam,
      permission: selectedPermission,
    };

    updateConfig({
      team_permissions: [...(config.team_permissions || []), newPermission],
    });

    setSelectedTeam('');
    setSelectedPermission('view');
  };

  // 移除团队权限
  const removeTeamPermission = (teamId: string) => {
    updateConfig({
      team_permissions: config.team_permissions?.filter((p) => p.team_id !== teamId),
    });
  };

  // 获取团队名称
  const getTeamName = (teamId: string) => {
    return teams.find((t) => t.id === teamId)?.name || '未知团队';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">发布确认</h2>
        <p className="text-sm text-muted-foreground">
          配置 Agent 的可见性和权限，准备发布
        </p>
      </div>

      {/* 配置摘要 */}
      <div className="rounded-lg border bg-muted/30 p-4">
        <h3 className="mb-3 font-semibold">配置摘要</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">名称：</span>
            <span className="font-medium">{config.name || '未设置'}</span>
          </div>
          <div>
            <span className="text-muted-foreground">模型：</span>
            <span className="font-medium">{config.model_id}</span>
          </div>
          <div>
            <span className="text-muted-foreground">记忆：</span>
            <span className="font-medium">
              {config.enable_memory
                ? `${config.memory_type === 'long_term' ? '长期' : '短期'} (${config.memory_window}轮)`
                : '未启用'}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">知识库：</span>
            <span className="font-medium">
              {config.enable_knowledge
                ? `${config.knowledge_base_ids.length} 个`
                : '未启用'}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">工具：</span>
            <span className="font-medium">
              {config.enable_tools
                ? `${Object.values(config.tool_config || {}).filter((v) => v === true).length} 个`
                : '未启用'}
            </span>
          </div>
        </div>
      </div>

      {/* 权限配置 */}
      <div className="space-y-4">
        <h3 className="font-semibold">可见性配置</h3>

        {/* 可见性选择 */}
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => {
              updateConfig({ is_public: false, team_permissions: [] });
            }}
            className={cn(
              'rounded-lg border p-4 text-left transition-colors',
              !config.is_public
                ? 'border-primary bg-primary/5'
                : 'hover:bg-accent'
            )}
          >
            <div className="font-medium">仅自己可见</div>
            <div className="mt-1 text-sm text-muted-foreground">
              私有 Agent，仅自己可查看和编辑
            </div>
            {!config.is_public && (
              <Check className="mt-2 h-5 w-5 text-primary" />
            )}
          </button>

          <button
            onClick={() => updateConfig({ is_public: false })}
            className={cn(
              'rounded-lg border p-4 text-left transition-colors',
              config.team_permissions && config.team_permissions.length > 0
                ? 'border-primary bg-primary/5'
                : 'hover:bg-accent'
            )}
          >
            <div className="font-medium">指定团队共享</div>
            <div className="mt-1 text-sm text-muted-foreground">
              选择团队并设置权限
            </div>
            {config.team_permissions && config.team_permissions.length > 0 && (
              <Check className="mt-2 h-5 w-5 text-primary" />
            )}
          </button>
        </div>

        {/* 团队权限配置 */}
        {config.team_permissions !== undefined && (
          <div className="rounded-lg border p-4">
            <h4 className="mb-3 font-medium">团队权限配置</h4>

            {/* 添加团队权限 */}
            <div className="mb-4 flex gap-2">
              <select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                className="flex-1 rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="">选择团队</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name} ({team.member_count} 人)
                  </option>
                ))}
              </select>

              <select
                value={selectedPermission}
                onChange={(e) =>
                  setSelectedPermission(e.target.value as 'view' | 'edit' | 'manage')
                }
                className="rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="view">查看</option>
                <option value="edit">编辑</option>
                <option value="manage">管理</option>
              </select>

              <button
                onClick={addTeamPermission}
                disabled={!selectedTeam}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                添加
              </button>
            </div>

            {/* 已添加的团队权限列表 */}
            {config.team_permissions && config.team_permissions.length > 0 ? (
              <div className="space-y-2">
                {config.team_permissions.map((perm) => (
                  <div
                    key={perm.team_id}
                    className="flex items-center justify-between rounded-md border bg-background p-3"
                  >
                    <div>
                      <span className="font-medium">{getTeamName(perm.team_id)}</span>
                      <span className="ml-2 rounded bg-primary/10 px-2 py-0.5 text-xs text-primary">
                        {PERMISSION_LABELS[perm.permission].label}
                      </span>
                    </div>
                    <button
                      onClick={() => removeTeamPermission(perm.team_id)}
                      className="text-sm text-muted-foreground hover:text-destructive"
                    >
                      移除
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-sm text-muted-foreground">
                暂未添加团队权限
              </div>
            )}
          </div>
        )}
      </div>

      {/* 底部按钮 */}
      <div className="flex justify-between border-t pt-4">
        <button
          onClick={onPrev}
          disabled={isSaving}
          className="flex items-center gap-2 rounded-md border px-6 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
        >
          <ChevronLeft className="h-4 w-4" />
          上一步
        </button>
        <button
          onClick={onPublish}
          disabled={isSaving || !config.name || !config.system_prompt}
          className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              发布中...
            </>
          ) : (
            <>
              <Rocket className="h-4 w-4" />
              发布 Agent
            </>
          )}
        </button>
      </div>
    </div>
  );
}
