/**
 * 团队管理页面
 * 团队列表、创建、成员邀请、权限管理
 */

import { useState, useEffect } from 'react';
import { cn } from '@workspace/ui/lib/utils';
import {
  Users,
  Plus,
  Mail,
  Copy,
  Trash2,
  MoreVertical,
  X,
  Check,
  Loader2,
  UserPlus,
  Shield,
  Edit,
  Eye,
  Clock,
} from 'lucide-react';

// 团队类型定义
interface Team {
  team_id: string;
  name: string;
  description?: string;
  member_count: number;
  creator: {
    user_id: string;
    name: string;
    email: string;
  };
  created_at: string;
}

// 成员类型定义
interface TeamMember {
  user_id: string;
  name: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  joined_at: string;
}

// 邀请类型定义
interface TeamInvitation {
  invite_code: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  status: 'pending' | 'accepted' | 'expired';
  expires_at: string;
  created_at: string;
}

export function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 加载团队列表
  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setIsLoading(true);
    try {
      // TODO: 调用实际 API
      setTeams([
        {
          team_id: 'team-1',
          name: '产品团队',
          description: '产品相关团队',
          member_count: 8,
          creator: { user_id: '1', name: 'Admin', email: 'admin@agentnex.io' },
          created_at: '2026-03-30T10:00:00',
        },
        {
          team_id: 'team-2',
          name: '技术团队',
          description: '技术相关团队',
          member_count: 15,
          creator: { user_id: '1', name: 'Admin', email: 'admin@agentnex.io' },
          created_at: '2026-03-29T08:00:00',
        },
      ]);
    } catch (error) {
      console.error('Failed to load teams:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-2xl font-bold">团队管理</h1>
          <p className="text-sm text-muted-foreground">
            创建团队，邀请成员，协作共享资源
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          创建团队
        </button>
      </header>

      {/* 内容区域 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：团队列表 */}
        <div className="w-80 border-r overflow-auto">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : teams.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
              <Users className="h-12 w-12 mb-4" />
              <p className="text-sm">暂无团队</p>
            </div>
          ) : (
            <div className="divide-y">
              {teams.map((team) => (
                <button
                  key={team.team_id}
                  onClick={() => setSelectedTeam(team)}
                  className={cn(
                    'w-full p-4 text-left transition-colors hover:bg-accent',
                    selectedTeam?.team_id === team.team_id && 'bg-accent'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{team.name}</div>
                      <div className="mt-1 text-xs text-muted-foreground truncate">
                        {team.description || '暂无描述'}
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                        <Users className="h-3 w-3" />
                        <span>{team.member_count} 个成员</span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 右侧：团队详情 */}
        <div className="flex-1 overflow-auto">
          {selectedTeam ? (
            <TeamDetail team={selectedTeam} onUpdate={loadTeams} />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <div className="text-center">
                <Users className="mx-auto h-16 w-16 mb-4" />
                <p className="text-lg font-medium">选择团队</p>
                <p className="text-sm">从左侧列表选择团队查看详情</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 创建团队弹窗 */}
      {showCreateModal && (
        <CreateTeamModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadTeams();
          }}
        />
      )}
    </div>
  );
}

// 团队详情组件
function TeamDetail({ team, onUpdate }: { team: Team; onUpdate: () => void }) {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<TeamInvitation[]>([]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'members' | 'invitations'>('members');

  useEffect(() => {
    loadData();
  }, [team.team_id]);

  const loadData = async () => {
    try {
      // TODO: 调用实际 API
      setMembers([
        {
          user_id: '1',
          name: 'Admin',
          email: 'admin@agentnex.io',
          role: 'admin',
          joined_at: '2026-03-30T10:00:00',
        },
        {
          user_id: '2',
          name: 'User1',
          email: 'user1@example.com',
          role: 'editor',
          joined_at: '2026-03-30T11:00:00',
        },
      ]);

      setInvitations([
        {
          invite_code: 'ABC123',
          email: 'invited@example.com',
          role: 'viewer',
          status: 'pending',
          expires_at: '2026-04-01T10:00:00',
          created_at: '2026-03-31T10:00:00',
        },
      ]);
    } catch (error) {
      console.error('Failed to load team data:', error);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!confirm('确定要移除此成员吗？')) return;
    try {
      // TODO: 调用实际 API
      setMembers(members.filter((m) => m.user_id !== userId));
    } catch (error) {
      console.error('Failed to remove member:', error);
    }
  };

  const handleChangeRole = async (userId: string, newRole: TeamMember['role']) => {
    if (!confirm(`确定要将该成员的角色修改为 ${newRole} 吗？`)) return;
    try {
      // TODO: 调用实际 API
      setMembers(
        members.map((m) => (m.user_id === userId ? { ...m, role: newRole } : m))
      );
    } catch (error) {
      console.error('Failed to change role:', error);
    }
  };

  const handleDeleteTeam = async () => {
    if (!confirm('确定要删除此团队吗？此操作不可恢复。')) return;
    try {
      // TODO: 调用实际 API
      alert('团队已删除');
      onUpdate();
    } catch (error) {
      console.error('Failed to delete team:', error);
    }
  };

  return (
    <div className="p-6">
      {/* 团队信息 */}
      <div className="mb-6 rounded-lg border p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="text-xl font-semibold">{team.name}</h2>
            <p className="text-sm text-muted-foreground">
              {team.description || '暂无描述'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowInviteModal(true)}
              className="flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <UserPlus className="h-4 w-4" />
              邀请成员
            </button>
            <button
              onClick={handleDeleteTeam}
              className="rounded-md border border-destructive px-3 py-1.5 text-sm font-medium text-destructive hover:bg-destructive hover:text-destructive-foreground"
            >
              删除团队
            </button>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">创建者：</span>
            <span className="font-medium">{team.creator.name || team.creator.email}</span>
          </div>
          <div>
            <span className="text-muted-foreground">成员数量：</span>
            <span className="font-medium">{team.member_count} 人</span>
          </div>
          <div>
            <span className="text-muted-foreground">创建时间：</span>
            <span className="font-medium">
              {new Date(team.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b mb-4">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('members')}
            className={cn(
              'border-b-2 py-3 text-sm font-medium',
              activeTab === 'members'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            成员列表
          </button>
          <button
            onClick={() => setActiveTab('invitations')}
            className={cn(
              'border-b-2 py-3 text-sm font-medium',
              activeTab === 'invitations'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            邀请记录
          </button>
        </div>
      </div>

      {/* 成员列表 */}
      {activeTab === 'members' && (
        <div className="rounded-lg border divide-y">
          {members.map((member) => (
            <div key={member.user_id} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  {member.name?.charAt(0).toUpperCase() || member.email.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="font-medium">{member.name || member.email}</div>
                  <div className="text-xs text-muted-foreground">{member.email}</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <select
                  value={member.role}
                  onChange={(e) =>
                    handleChangeRole(member.user_id, e.target.value as TeamMember['role'])
                  }
                  className="rounded-md border bg-background px-2 py-1 text-sm"
                >
                  <option value="admin">管理员</option>
                  <option value="editor">编辑者</option>
                  <option value="viewer">查看者</option>
                </select>

                <button
                  onClick={() => handleRemoveMember(member.user_id)}
                  className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 邀请记录 */}
      {activeTab === 'invitations' && (
        <div className="rounded-lg border divide-y">
          {invitations.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              暂无邀请记录
            </div>
          ) : (
            invitations.map((inv) => (
              <div key={inv.invite_code} className="flex items-center justify-between p-4">
                <div>
                  <div className="font-medium">{inv.email}</div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span>角色: {inv.role}</span>
                    <span
                      className={cn(
                        inv.status === 'pending' && 'text-blue-600',
                        inv.status === 'accepted' && 'text-green-600',
                        inv.status === 'expired' && 'text-red-600'
                      )}
                    >
                      {inv.status === 'pending'
                        ? '待注册'
                        : inv.status === 'accepted'
                          ? '已加入'
                          : '已过期'}
                    </span>
                  </div>
                </div>

                {inv.status === 'pending' && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(
                          `${window.location.origin}/register?invite=${inv.invite_code}&email=${inv.email}`
                        );
                        alert('邀请链接已复制');
                      }}
                      className="flex items-center gap-1 rounded-md border px-3 py-1 text-sm hover:bg-accent"
                    >
                      <Copy className="h-3 w-3" />
                      复制链接
                    </button>
                    <div className="text-xs text-muted-foreground">
                      <Clock className="mr-1 inline h-3 w-3" />
                      {new Date(inv.expires_at).toLocaleDateString()}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* 邀请成员弹窗 */}
      {showInviteModal && (
        <InviteMemberModal
          teamId={team.team_id}
          onClose={() => setShowInviteModal(false)}
          onSuccess={() => {
            setShowInviteModal(false);
            loadData();
          }}
        />
      )}
    </div>
  );
}

// 创建团队弹窗
function CreateTeamModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) {
      alert('请输入团队名称');
      return;
    }

    setIsCreating(true);
    try {
      // TODO: 调用实际 API
      await new Promise((resolve) => setTimeout(resolve, 1000));
      alert('团队创建成功');
      onSuccess();
    } catch (error) {
      console.error('Failed to create team:', error);
      alert('创建失败');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-background p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">创建团队</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium">
              团队名称 <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：产品团队"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">描述</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="团队描述"
              rows={2}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isCreating ? '创建中...' : '创建'}
          </button>
        </div>
      </div>
    </div>
  );
}

// 邀请成员弹窗
function InviteMemberModal({
  teamId,
  onClose,
  onSuccess,
}: {
  teamId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'admin' | 'editor' | 'viewer'>('viewer');
  const [isInviting, setIsInviting] = useState(false);
  const [inviteLink, setInviteLink] = useState('');

  const handleInvite = async () => {
    if (!email.trim()) {
      alert('请输入邮箱地址');
      return;
    }

    setIsInviting(true);
    try {
      // TODO: 调用实际 API
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // 模拟生成邀请链接
      const code = Math.random().toString(36).substring(7).toUpperCase();
      const link = `${window.location.origin}/register?invite=${code}&email=${email}`;
      setInviteLink(link);
    } catch (error) {
      console.error('Failed to invite:', error);
      alert('邀请失败');
    } finally {
      setIsInviting(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(inviteLink);
    alert('邀请链接已复制到剪贴板');
  };

  const handleDone = () => {
    onSuccess();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-background p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">邀请成员</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        {!inviteLink ? (
          <>
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium">
                  邮箱地址 <span className="text-destructive">*</span>
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium">团队角色</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'admin', label: '管理员', icon: Shield },
                    { value: 'editor', label: '编辑者', icon: Edit },
                    { value: 'viewer', label: '查看者', icon: Eye },
                  ].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setRole(option.value as typeof role)}
                      className={cn(
                        'flex flex-col items-center gap-1 rounded-md border p-3 transition-colors',
                        role === option.value
                          ? 'border-primary bg-primary/5'
                          : 'hover:bg-accent'
                      )}
                    >
                      <option.icon className="h-5 w-5" />
                      <span className="text-xs">{option.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={onClose}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
              >
                取消
              </button>
              <button
                onClick={handleInvite}
                disabled={isInviting}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {isInviting ? '生成中...' : '生成邀请链接'}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="space-y-4">
              <div className="rounded-lg bg-muted p-4">
                <div className="mb-2 text-sm font-medium">邀请链接已生成</div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={inviteLink}
                    readOnly
                    className="flex-1 rounded-md border bg-background px-3 py-2 text-xs"
                  />
                  <button
                    onClick={handleCopyLink}
                    className="flex items-center gap-1 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                  >
                    <Copy className="h-4 w-4" />
                    复制
                  </button>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">
                  链接有效期：24 小时
                </div>
              </div>

              <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-3 text-xs text-yellow-900">
                <strong>提示：</strong>请将邀请链接发送给 {email}，对方点击链接即可注册并加入团队。
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={handleDone}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                完成
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
