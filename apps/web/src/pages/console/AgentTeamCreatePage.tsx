/**
 * Agent Team 创建/编辑页面
 * P1阶段：团队配置与画布编排
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { TeamCanvas } from '@/components/agentTeam/TeamCanvas';
import type { CanvasNode, CanvasEdge } from '@/api/agentTeams';
import { createAgentTeam, getAgentTeam, updateAgentTeam, saveCanvas } from '@/api/agentTeams';
import { listAgents } from '@/api/agents';
import { cn } from '@workspace/ui/lib/utils';
import {
  ArrowLeft,
  Save,
  Play,
  Settings,
  Palette,
  Loader2,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react';

type Step = 'basic' | 'canvas' | 'settings';

export function AgentTeamCreatePage() {
  const navigate = useNavigate();
  const { teamId } = useParams();
  const isEditing = !!teamId;

  const [currentStep, setCurrentStep] = useState<Step>('basic');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 基础配置
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [goal, setGoal] = useState('');
  const [maxRounds, setMaxRounds] = useState(20);
  const [timeoutMinutes, setTimeoutMinutes] = useState(10);
  const [globalPrompt, setGlobalPrompt] = useState('');
  const [communicationMode, setCommunicationMode] = useState<'broadcast' | 'point_to_point' | 'topic_based'>('broadcast');
  const [decisionMode, setDecisionMode] = useState<'voting' | 'leader' | 'unanimous'>('leader');
  const [isPublic, setIsPublic] = useState(false);

  // 画布配置
  const [canvasNodes, setCanvasNodes] = useState<CanvasNode[]>([]);
  const [canvasEdges, setCanvasEdges] = useState<CanvasEdge[]>([]);
  const [availableAgents, setAvailableAgents] = useState<{ agent_id: string; name: string }[]>([]);

  // 创建的团队ID
  const [createdTeamId, setCreatedTeamId] = useState<string | null>(null);

  // 加载可用Agents
  useEffect(() => {
    loadAvailableAgents();
  }, []);

  // 编辑模式：加载团队数据
  useEffect(() => {
    if (teamId) {
      loadTeamData(teamId);
    }
  }, [teamId]);

  const loadAvailableAgents = async () => {
    try {
      const result = await listAgents({ page_size: 100 });
      setAvailableAgents(
        result.items.map((a) => ({
          agent_id: a.agent_id,
          name: a.name,
        }))
      );
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const loadTeamData = async (id: string) => {
    setIsLoading(true);
    try {
      const team = await getAgentTeam(id);
      setName(team.name);
      setDescription(team.description || '');
      setGoal(team.goal);
      setMaxRounds(team.team_config.max_rounds);
      setTimeoutMinutes(team.team_config.timeout_minutes);
      setGlobalPrompt(team.team_config.global_prompt || '');
      setCommunicationMode(team.communication_mode);
      setDecisionMode(team.decision_mode);
      setIsPublic(team.is_public);
      setCanvasNodes(team.nodes || []);
      setCanvasEdges(team.edges || []);
      setCreatedTeamId(id);
    } catch (error) {
      console.error('Failed to load team:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 保存团队
  const handleSave = async () => {
    if (!name.trim() || !goal.trim()) {
      alert('请填写团队名称和目标');
      return;
    }

    setIsSaving(true);
    try {
      if (createdTeamId) {
        // 更新团队
        await updateAgentTeam(createdTeamId, {
          name,
          description,
          goal,
          team_config: {
            max_rounds: maxRounds,
            timeout_minutes: timeoutMinutes,
            global_prompt: globalPrompt || undefined,
          },
          communication_mode: communicationMode,
          decision_mode: decisionMode,
          is_public: isPublic,
        });

        // 保存画布
        await saveCanvas(createdTeamId, {
          nodes: canvasNodes,
          edges: canvasEdges,
        });
      } else {
        // 创建团队
        const team = await createAgentTeam({
          name,
          description,
          goal,
          team_config: {
            max_rounds: maxRounds,
            timeout_minutes: timeoutMinutes,
            global_prompt: globalPrompt || undefined,
          },
          communication_mode: communicationMode,
          decision_mode: decisionMode,
        });

        setCreatedTeamId(team.team_id);

        // 保存画布
        await saveCanvas(team.team_id, {
          nodes: canvasNodes,
          edges: canvasEdges,
        });
      }

      alert('保存成功');
      navigate('/console/agent-teams');
    } catch (error) {
      console.error('Failed to save team:', error);
      alert('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  // 画布变更
  const handleCanvasChange = (nodes: CanvasNode[], edges: CanvasEdge[]) => {
    setCanvasNodes(nodes);
    setCanvasEdges(edges);
  };

  // 步骤配置
  const steps: { id: Step; name: string; icon: React.ReactNode }[] = [
    { id: 'basic', name: '基础配置', icon: <Settings className="h-4 w-4" /> },
    { id: 'canvas', name: '画布编排', icon: <Palette className="h-4 w-4" /> },
    { id: 'settings', name: '运行设置', icon: <Settings className="h-4 w-4" /> },
  ];

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/console/agent-teams')}
            className="rounded p-1 hover:bg-accent"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold">
              {isEditing ? '编辑团队' : '创建团队'}
            </h1>
            <p className="text-sm text-muted-foreground">
              配置多智能体团队协作流程
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            保存
          </button>
          {createdTeamId && (
            <button
              onClick={() => navigate(`/console/agent-teams/${createdTeamId}/run`)}
              className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              <Play className="h-4 w-4" />
              运行测试
            </button>
          )}
        </div>
      </div>

      {/* 步骤指示器 */}
      <div className="border-b bg-muted/30 px-6 py-3">
        <div className="flex items-center gap-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <button
                onClick={() => setCurrentStep(step.id)}
                className={cn(
                  'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  currentStep === step.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                )}
              >
                {step.icon}
                {step.name}
              </button>
              {index < steps.length - 1 && (
                <ChevronRight className="mx-2 h-4 w-4 text-muted-foreground" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto">
        {currentStep === 'basic' && (
          <div className="mx-auto max-w-2xl p-6">
            <div className="space-y-6">
              {/* 基本信息 */}
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">基本信息</h2>

                <div className="space-y-2">
                  <label className="text-sm font-medium">团队名称 *</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="输入团队名称"
                    className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">团队描述</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="描述团队的功能和用途"
                    rows={3}
                    className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">团队目标 *</label>
                  <textarea
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="定义团队的协作目标"
                    rows={2}
                    className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              {/* 团队配置 */}
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">团队配置</h2>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">最大对话轮数</label>
                    <input
                      type="number"
                      value={maxRounds}
                      onChange={(e) => setMaxRounds(parseInt(e.target.value) || 20)}
                      min={1}
                      max={100}
                      className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">超时时间（分钟）</label>
                    <input
                      type="number"
                      value={timeoutMinutes}
                      onChange={(e) => setTimeoutMinutes(parseInt(e.target.value) || 10)}
                      min={1}
                      max={60}
                      className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">全局提示词</label>
                  <textarea
                    value={globalPrompt}
                    onChange={(e) => setGlobalPrompt(e.target.value)}
                    placeholder="为团队成员添加全局指导"
                    rows={3}
                    className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => setCurrentStep('canvas')}
                  className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                >
                  下一步：画布编排
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {currentStep === 'canvas' && (
          <div className="h-full">
            <TeamCanvas
              initialNodes={canvasNodes}
              initialEdges={canvasEdges}
              availableAgents={availableAgents}
              onChange={handleCanvasChange}
            />
            <div className="absolute bottom-4 right-4 flex gap-2">
              <button
                onClick={() => setCurrentStep('basic')}
                className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
              >
                <ChevronLeft className="h-4 w-4" />
                上一步
              </button>
              <button
                onClick={() => setCurrentStep('settings')}
                className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                下一步：运行设置
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {currentStep === 'settings' && (
          <div className="mx-auto max-w-2xl p-6">
            <div className="space-y-6">
              {/* 通信模式 */}
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">通信模式</h2>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { id: 'broadcast', name: '广播模式', desc: '所有Agent都收到消息' },
                    { id: 'point_to_point', name: '点对点', desc: '指定接收者通信' },
                    { id: 'topic_based', name: '主题订阅', desc: '按主题分发消息' },
                  ].map((mode) => (
                    <button
                      key={mode.id}
                      onClick={() => setCommunicationMode(mode.id as typeof communicationMode)}
                      className={cn(
                        'rounded-lg border p-4 text-left transition-colors',
                        communicationMode === mode.id
                          ? 'border-primary bg-primary/10'
                          : 'hover:border-primary/50'
                      )}
                    >
                      <div className="font-medium">{mode.name}</div>
                      <div className="mt-1 text-xs text-muted-foreground">{mode.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* 决策模式 */}
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">决策模式</h2>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { id: 'voting', name: '投票制', desc: '超过半数Agent同意' },
                    { id: 'leader', name: '负责人制', desc: '由主Agent决策' },
                    { id: 'unanimous', name: '一致通过', desc: '所有Agent同意' },
                  ].map((mode) => (
                    <button
                      key={mode.id}
                      onClick={() => setDecisionMode(mode.id as typeof decisionMode)}
                      className={cn(
                        'rounded-lg border p-4 text-left transition-colors',
                        decisionMode === mode.id
                          ? 'border-primary bg-primary/10'
                          : 'hover:border-primary/50'
                      )}
                    >
                      <div className="font-medium">{mode.name}</div>
                      <div className="mt-1 text-xs text-muted-foreground">{mode.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* 权限设置 */}
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">权限设置</h2>
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="isPublic"
                    checked={isPublic}
                    onChange={(e) => setIsPublic(e.target.checked)}
                    className="h-4 w-4"
                  />
                  <label htmlFor="isPublic" className="text-sm">
                    公开团队（其他用户可查看和使用）
                  </label>
                </div>
              </div>

              <div className="flex justify-between">
                <button
                  onClick={() => setCurrentStep('canvas')}
                  className="flex items-center gap-2 rounded-md border px-6 py-2 text-sm font-medium hover:bg-accent"
                >
                  <ChevronLeft className="h-4 w-4" />
                  上一步
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  保存团队
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentTeamCreatePage;
