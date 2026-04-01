/**
 * Workflow 创建/编辑页面
 * P2阶段：工作流配置与画布编排
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { WorkflowCanvas } from '@/components/workflow/WorkflowCanvas';
import type { CanvasWorkflowNode, CanvasWorkflowEdge, WorkflowVariable } from '@/api/workflows';
import { createWorkflow, getWorkflow, updateWorkflow, saveWorkflowCanvas, activateWorkflow } from '@/api/workflows';
import { listAgents } from '@/api/agents';
import { listAgentTeams } from '@/api/agentTeams';
import { cn } from '@workspace/ui/lib/utils';
import {
  ArrowLeft,
  Save,
  Play,
  Settings,
  GitBranch,
  Loader2,
  ChevronRight,
  ChevronLeft,
  Variable,
} from 'lucide-react';

type Step = 'basic' | 'canvas' | 'variables';

export function WorkflowCreatePage() {
  const navigate = useNavigate();
  const { workflowId } = useParams();
  const isEditing = !!workflowId;

  const [currentStep, setCurrentStep] = useState<Step>('basic');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 基础配置
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [triggerType, setTriggerType] = useState<'manual' | 'api' | 'schedule' | 'webhook' | 'event'>('manual');
  const [isPublic, setIsPublic] = useState(false);

  // 画布配置
  const [canvasNodes, setCanvasNodes] = useState<CanvasWorkflowNode[]>([]);
  const [canvasEdges, setCanvasEdges] = useState<CanvasWorkflowEdge[]>([]);

  // 变量定义
  const [variables, setVariables] = useState<WorkflowVariable[]>([]);

  // 可用资源
  const [availableAgents, setAvailableAgents] = useState<{ agent_id: string; name: string }[]>([]);
  const [availableTeams, setAvailableTeams] = useState<{ team_id: string; name: string }[]>([]);

  // 创建的工作流ID
  const [createdWorkflowId, setCreatedWorkflowId] = useState<string | null>(null);

  // 加载可用资源
  useEffect(() => {
    loadResources();
  }, []);

  // 编辑模式：加载工作流数据
  useEffect(() => {
    if (workflowId) {
      loadWorkflowData(workflowId);
    }
  }, [workflowId]);

  const loadResources = async () => {
    try {
      const [agentsResult, teamsResult] = await Promise.all([
        listAgents({ page_size: 100 }),
        listAgentTeams({ page_size: 100 }),
      ]);
      setAvailableAgents(agentsResult.items.map(a => ({ agent_id: a.agent_id, name: a.name })));
      setAvailableTeams(teamsResult.items.map(t => ({ team_id: t.team_id, name: t.name })));
    } catch (error) {
      console.error('Failed to load resources:', error);
    }
  };

  const loadWorkflowData = async (id: string) => {
    setIsLoading(true);
    try {
      const workflow = await getWorkflow(id);
      setName(workflow.name);
      setDescription(workflow.description || '');
      setTriggerType(workflow.trigger_type);
      setIsPublic(workflow.is_public);
      setVariables(workflow.variables || []);
      setCanvasNodes(workflow.nodes || []);
      setCanvasEdges(workflow.edges || []);
      setCreatedWorkflowId(id);
    } catch (error) {
      console.error('Failed to load workflow:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!name.trim()) {
      alert('请填写工作流名称');
      return;
    }

    setIsSaving(true);
    try {
      if (createdWorkflowId) {
        // 更新工作流
        await updateWorkflow(createdWorkflowId, {
          name,
          description,
          trigger_type: triggerType,
          variables,
          is_public: isPublic,
        });

        // 保存画布
        await saveWorkflowCanvas(createdWorkflowId, {
          nodes: canvasNodes,
          edges: canvasEdges,
        });
      } else {
        // 创建工作流
        const workflow = await createWorkflow({
          name,
          description,
          trigger_type: triggerType,
          variables,
          is_public: isPublic,
        });

        setCreatedWorkflowId(workflow.workflow_id);

        // 保存画布
        await saveWorkflowCanvas(workflow.workflow_id, {
          nodes: canvasNodes,
          edges: canvasEdges,
        });
      }

      alert('保存成功');
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleActivate = async () => {
    if (!createdWorkflowId) {
      alert('请先保存工作流');
      return;
    }

    try {
      await activateWorkflow(createdWorkflowId);
      alert('工作流已激活');
      navigate('/console/workflows');
    } catch (error) {
      console.error('Failed to activate workflow:', error);
      alert('激活失败，请确保工作流配置正确');
    }
  };

  const handleCanvasChange = (nodes: CanvasWorkflowNode[], edges: CanvasWorkflowEdge[]) => {
    setCanvasNodes(nodes);
    setCanvasEdges(edges);
  };

  const addVariable = () => {
    setVariables([...variables, { name: '', type: 'string', required: false }]);
  };

  const updateVariable = (index: number, field: keyof WorkflowVariable, value: unknown) => {
    const updated = [...variables];
    updated[index] = { ...updated[index], [field]: value };
    setVariables(updated);
  };

  const removeVariable = (index: number) => {
    setVariables(variables.filter((_, i) => i !== index));
  };

  const steps = [
    { id: 'basic' as Step, name: '基础配置', icon: <Settings className="h-4 w-4" /> },
    { id: 'canvas' as Step, name: '画布编排', icon: <GitBranch className="h-4 w-4" /> },
    { id: 'variables' as Step, name: '变量定义', icon: <Variable className="h-4 w-4" /> },
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
            onClick={() => navigate('/console/workflows')}
            className="rounded p-1 hover:bg-accent"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold">{isEditing ? '编辑工作流' : '创建工作流'}</h1>
            <p className="text-sm text-muted-foreground">可视化工作流编排</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
          >
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            保存
          </button>
          {createdWorkflowId && (
            <button
              onClick={handleActivate}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Play className="h-4 w-4" />
              激活并运行
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
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">基本信息</h2>

                <div className="space-y-2">
                  <label className="text-sm font-medium">工作流名称 *</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="输入工作流名称"
                    className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">工作流描述</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="描述工作流的功能和用途"
                    rows={3}
                    className="w-full rounded-md border bg-background px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h2 className="text-lg font-semibold">触发方式</h2>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { id: 'manual', name: '手动触发', desc: '通过控制台手动执行' },
                    { id: 'api', name: 'API 触发', desc: '通过 REST API 调用' },
                    { id: 'schedule', name: '定时触发', desc: '按计划定时执行' },
                    { id: 'webhook', name: 'Webhook', desc: '接收外部事件触发' },
                  ].map((mode) => (
                    <button
                      key={mode.id}
                      onClick={() => setTriggerType(mode.id as typeof triggerType)}
                      className={cn(
                        'rounded-lg border p-4 text-left transition-colors',
                        triggerType === mode.id
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
                    公开工作流（其他用户可查看和使用）
                  </label>
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
            <WorkflowCanvas
              initialNodes={canvasNodes}
              initialEdges={canvasEdges}
              availableAgents={availableAgents}
              availableTeams={availableTeams}
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
                onClick={() => setCurrentStep('variables')}
                className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                下一步：变量定义
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {currentStep === 'variables' && (
          <div className="mx-auto max-w-2xl p-6">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">工作流变量</h2>
                <button
                  onClick={addVariable}
                  className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm hover:bg-accent"
                >
                  <Plus className="h-4 w-4" />
                  添加变量
                </button>
              </div>

              {variables.length === 0 ? (
                <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
                  <Variable className="mx-auto h-8 w-8 mb-2" />
                  <p>暂无变量定义</p>
                  <p className="text-xs mt-1">变量可在工作流节点间传递数据</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {variables.map((variable, index) => (
                    <div key={index} className="flex items-center gap-3 rounded-lg border p-3">
                      <input
                        type="text"
                        value={variable.name}
                        onChange={(e) => updateVariable(index, 'name', e.target.value)}
                        placeholder="变量名"
                        className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm"
                      />
                      <select
                        value={variable.type}
                        onChange={(e) => updateVariable(index, 'type', e.target.value)}
                        className="rounded-md border bg-background px-3 py-1.5 text-sm"
                      >
                        <option value="string">字符串</option>
                        <option value="number">数字</option>
                        <option value="boolean">布尔值</option>
                        <option value="object">对象</option>
                        <option value="array">数组</option>
                      </select>
                      <input
                        type="text"
                        value={variable.default_value as string || ''}
                        onChange={(e) => updateVariable(index, 'default_value', e.target.value)}
                        placeholder="默认值"
                        className="w-32 rounded-md border bg-background px-3 py-1.5 text-sm"
                      />
                      <button
                        onClick={() => removeVariable(index)}
                        className="rounded p-1 text-destructive hover:bg-accent"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

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
                  保存工作流
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// 导入缺失的图标
import { Plus, Trash2 } from 'lucide-react';

export default WorkflowCreatePage;
