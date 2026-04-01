/**
 * Workflows 管理页面
 * P2阶段：工作流引擎管理
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Workflow, WorkflowStatus } from '@/api/workflows';
import { listWorkflows, deleteWorkflow, activateWorkflow, deactivateWorkflow } from '@/api/workflows';
import { cn } from '@workspace/ui/lib/utils';
import {
  GitBranch,
  Plus,
  Search,
  Trash2,
  Edit,
  Play,
  Download,
  MoreVertical,
  Loader2,
  Pause,
  CheckCircle,
  FileText,
} from 'lucide-react';

export function WorkflowsPage() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | 'all'>('all');

  useEffect(() => {
    loadWorkflows();
  }, [statusFilter]);

  const loadWorkflows = async () => {
    setIsLoading(true);
    try {
      const result = await listWorkflows({
        status: statusFilter === 'all' ? undefined : statusFilter,
        search: searchQuery || undefined,
      });
      setWorkflows(result.items);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    loadWorkflows();
  };

  const handleDelete = async (workflowId: string) => {
    if (!confirm('确定要删除这个工作流吗？此操作不可恢复。')) return;

    try {
      await deleteWorkflow(workflowId);
      setWorkflows(workflows.filter(w => w.workflow_id !== workflowId));
    } catch (error) {
      console.error('Failed to delete workflow:', error);
      alert('删除失败');
    }
  };

  const handleToggleStatus = async (workflow: Workflow) => {
    try {
      if (workflow.status === 'active') {
        await deactivateWorkflow(workflow.workflow_id);
      } else {
        await activateWorkflow(workflow.workflow_id);
      }
      loadWorkflows();
    } catch (error) {
      console.error('Failed to toggle status:', error);
      alert('操作失败');
    }
  };

  const getStatusIcon = (status: WorkflowStatus) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'draft':
        return <FileText className="h-4 w-4 text-gray-500" />;
      case 'archived':
        return <Pause className="h-4 w-4 text-orange-500" />;
    }
  };

  const getStatusLabel = (status: WorkflowStatus) => {
    switch (status) {
      case 'active': return '已激活';
      case 'draft': return '草稿';
      case 'archived': return '已归档';
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <div className="border-b p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">工作流</h1>
            <p className="text-sm text-muted-foreground">可视化工作流编排与自动化</p>
          </div>
          <button
            onClick={() => navigate('/console/workflows/create')}
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            创建工作流
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
              placeholder="搜索工作流..."
              className="w-full rounded-md border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex items-center gap-2">
            {(['all', 'draft', 'active', 'archived'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  statusFilter === status ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
                )}
              >
                {status === 'all' ? '全部' : getStatusLabel(status)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 工作流列表 */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : workflows.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
            <GitBranch className="h-16 w-16 mb-4" />
            <p className="text-lg font-medium">暂无工作流</p>
            <p className="text-sm">点击"创建工作流"开始构建自动化流程</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workflows.map((workflow) => (
              <WorkflowCard
                key={workflow.workflow_id}
                workflow={workflow}
                onEdit={() => navigate(`/console/workflows/${workflow.workflow_id}`)}
                onRun={() => navigate(`/console/workflows/${workflow.workflow_id}/run`)}
                onToggleStatus={() => handleToggleStatus(workflow)}
                onDelete={() => handleDelete(workflow.workflow_id)}
                getStatusIcon={getStatusIcon}
                getStatusLabel={getStatusLabel}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// 工作流卡片组件
interface WorkflowCardProps {
  workflow: Workflow;
  onEdit: () => void;
  onRun: () => void;
  onToggleStatus: () => void;
  onDelete: () => void;
  getStatusIcon: (status: WorkflowStatus) => React.ReactNode;
  getStatusLabel: (status: WorkflowStatus) => string;
}

function WorkflowCard({
  workflow,
  onEdit,
  onRun,
  onToggleStatus,
  onDelete,
  getStatusIcon,
  getStatusLabel,
}: WorkflowCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="rounded-lg border bg-card p-4 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <GitBranch className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold">{workflow.name}</h3>
            <p className="text-xs text-muted-foreground">
              v{workflow.version} · {workflow.execution_count} 次执行
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
            <div className="absolute right-0 top-full z-10 mt-1 w-40 rounded-md border bg-background py-1 shadow-lg">
              <button
                onClick={() => { setShowMenu(false); onEdit(); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                <Edit className="h-4 w-4" />
                编辑配置
              </button>
              <button
                onClick={() => { setShowMenu(false); onToggleStatus(); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent"
              >
                {workflow.status === 'active' ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {workflow.status === 'active' ? '停用' : '激活'}
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
                删除工作流
              </button>
            </div>
          )}
        </div>
      </div>

      <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
        {workflow.description || '暂无描述'}
      </p>

      <div className="mt-4 flex items-center gap-2">
        <span className="flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs">
          {getStatusIcon(workflow.status)}
          {getStatusLabel(workflow.status)}
        </span>
        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
          {workflow.trigger_type === 'manual' ? '手动触发' :
           workflow.trigger_type === 'api' ? 'API触发' :
           workflow.trigger_type === 'schedule' ? '定时触发' :
           workflow.trigger_type === 'webhook' ? 'Webhook' : '事件触发'}
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
          disabled={workflow.status !== 'active'}
          className="flex-1 rounded-md bg-primary py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          运行工作流
        </button>
      </div>
    </div>
  );
}

export default WorkflowsPage;
