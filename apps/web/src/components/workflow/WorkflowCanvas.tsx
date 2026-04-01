/**
 * Workflow 画布组件
 * P2阶段：基于React Flow的工作流可视化编排
 */

import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Controls,
  Background,
  BackgroundVariant,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from 'reactflow';
import type { Node, Connection, NodeChange, EdgeChange } from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Play,
  Square,
  Bot,
  Users,
  GitBranch,
  Repeat,
  GitFork,
  UserCircle,
  Code,
  Globe,
  Clock,
  Settings,
  Trash2,
  Plus,
} from 'lucide-react';
import type { CanvasWorkflowNode, CanvasWorkflowEdge, WorkflowNodeType } from '@/api/workflows';

// 节点类型配置
const NODE_TYPES_CONFIG: Record<WorkflowNodeType, { icon: React.ReactNode; color: string; label: string }> = {
  start: { icon: <Play className="h-4 w-4" />, color: 'bg-green-500', label: '开始' },
  end: { icon: <Square className="h-4 w-4" />, color: 'bg-red-500', label: '结束' },
  agent: { icon: <Bot className="h-4 w-4" />, color: 'bg-blue-500', label: 'Agent' },
  team: { icon: <Users className="h-4 w-4" />, color: 'bg-purple-500', label: '团队' },
  condition: { icon: <GitBranch className="h-4 w-4" />, color: 'bg-orange-500', label: '条件' },
  loop: { icon: <Repeat className="h-4 w-4" />, color: 'bg-yellow-500', label: '循环' },
  parallel: { icon: <GitFork className="h-4 w-4" />, color: 'bg-cyan-500', label: '并行' },
  human_input: { icon: <UserCircle className="h-4 w-4" />, color: 'bg-pink-500', label: '人工输入' },
  code: { icon: <Code className="h-4 w-4" />, color: 'bg-gray-500', label: '代码' },
  api_call: { icon: <Globe className="h-4 w-4" />, color: 'bg-indigo-500', label: 'API调用' },
  delay: { icon: <Clock className="h-4 w-4" />, color: 'bg-teal-500', label: '延迟' },
};

// 通用节点组件
interface WorkflowNodeData {
  node_type: WorkflowNodeType;
  label?: string;
  config: Record<string, unknown>;
  onEdit?: (nodeId: string) => void;
  onDelete?: (nodeId: string) => void;
}

function WorkflowNodeComponent({ data, id }: { data: WorkflowNodeData; id: string }) {
  const config = NODE_TYPES_CONFIG[data.node_type] || NODE_TYPES_CONFIG.agent;

  return (
    <div className="min-w-[180px] rounded-lg border-2 border-primary/30 bg-background shadow-lg">
      {/* 头部 */}
      <div className={cn('flex items-center gap-2 rounded-t-lg px-3 py-2 text-white', config.color)}>
        <div className="flex h-6 w-6 items-center justify-center rounded bg-white/20">
          {config.icon}
        </div>
        <div className="flex-1 text-sm font-semibold">
          {data.label || config.label}
        </div>
      </div>

      {/* 内容 */}
      <div className="p-3">
        <div className="text-xs text-muted-foreground">
          {data.node_type === 'agent' && data.config.agent_id != null && (
            <span>Agent ID: {String(data.config.agent_id).slice(0, 8)}...</span>
          )}
          {data.node_type === 'team' && data.config.team_id != null && (
            <span>Team ID: {String(data.config.team_id).slice(0, 8)}...</span>
          )}
          {data.node_type === 'delay' && data.config.delay_seconds != null && (
            <span>延迟: {String(data.config.delay_seconds)}秒</span>
          )}
          {data.node_type === 'condition' && (
            <span>条件分支节点</span>
          )}
          {data.node_type === 'human_input' && data.config.prompt != null && (
            <span className="line-clamp-2">{String(data.config.prompt)}</span>
          )}
          {data.node_type === 'code' && data.config.language != null && (
            <span>语言: {String(data.config.language)}</span>
          )}
          {data.node_type === 'api_call' && data.config.url != null && (
            <span className="truncate">{String(data.config.url)}</span>
          )}
        </div>
      </div>

      {/* 操作按钮（非开始/结束节点） */}
      {data.node_type !== 'start' && data.node_type !== 'end' && (
        <div className="flex border-t">
          <button
            onClick={() => data.onEdit?.(id)}
            className="flex flex-1 items-center justify-center gap-1 py-1.5 text-xs hover:bg-accent"
          >
            <Settings className="h-3 w-3" />
            配置
          </button>
          <button
            onClick={() => data.onDelete?.(id)}
            className="flex flex-1 items-center justify-center gap-1 py-1.5 text-xs text-destructive hover:bg-accent"
          >
            <Trash2 className="h-3 w-3" />
            删除
          </button>
        </div>
      )}

      {/* 连接点 */}
      {data.node_type !== 'end' && (
        <div
          className="absolute right-0 top-1/2 h-3 w-3 translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-primary bg-background"
          style={{ right: -6 }}
        />
      )}
      {data.node_type !== 'start' && (
        <div
          className="absolute left-0 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-primary bg-background"
          style={{ left: -6 }}
        />
      )}
    </div>
  );
}

// 导入 cn 工具
import { cn } from '@workspace/ui/lib/utils';

const nodeTypes = {
  workflow: WorkflowNodeComponent,
};

interface WorkflowCanvasProps {
  initialNodes?: CanvasWorkflowNode[];
  initialEdges?: CanvasWorkflowEdge[];
  availableAgents: { agent_id: string; name: string }[];
  availableTeams: { team_id: string; name: string }[];
  onChange?: (nodes: CanvasWorkflowNode[], edges: CanvasWorkflowEdge[]) => void;
  onSave?: (nodes: CanvasWorkflowNode[], edges: CanvasWorkflowEdge[]) => void;
}

export function WorkflowCanvas({
  initialNodes = [],
  initialEdges = [],
  availableAgents,
  availableTeams,
  onChange,
  onSave,
}: WorkflowCanvasProps) {
  // 转换为React Flow格式
  const [nodes, setNodes, onNodesChange] = useNodesState(
    initialNodes.map((n) => ({
      id: n.node_id || `node-${Date.now()}-${Math.random()}`,
      type: 'workflow',
      position: n.position,
      data: {
        node_type: n.node_type,
        label: n.label,
        config: n.config,
      },
    }))
  );

  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialEdges.map((e) => ({
      id: e.edge_id || `edge-${Date.now()}-${Math.random()}`,
      source: e.source_node_id,
      target: e.target_node_id,
      label: e.label,
      markerEnd: { type: MarkerType.ArrowClosed },
      animated: true,
    }))
  );

  // 节点编辑
  const handleEditNode = useCallback((nodeId: string) => {
    console.log('Edit node:', nodeId);
    // TODO: 打开节点配置弹窗
  }, []);

  // 节点删除
  const handleDeleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
  }, [setNodes, setEdges]);

  // 连接处理
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            markerEnd: { type: MarkerType.ArrowClosed },
            animated: true,
          },
          eds
        )
      );
    },
    [setEdges]
  );

  // 添加节点
  const handleAddNode = useCallback((nodeType: WorkflowNodeType) => {
    const config = NODE_TYPES_CONFIG[nodeType];
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'workflow',
      position: { x: 250 + nodes.length * 50, y: 150 + nodes.length * 50 },
      data: {
        node_type: nodeType,
        label: config.label,
        config: {},
        onEdit: handleEditNode,
        onDelete: handleDeleteNode,
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodes.length, setNodes, handleEditNode, handleDeleteNode]);

  // 更新节点数据
  const nodesWithCallbacks = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        onEdit: handleEditNode,
        onDelete: handleDeleteNode,
      },
    }));
  }, [nodes, handleEditNode, handleDeleteNode]);

  // 导出配置
  const exportConfig = useCallback((): { nodes: CanvasWorkflowNode[]; edges: CanvasWorkflowEdge[] } => {
    const canvasNodes: CanvasWorkflowNode[] = nodes.map((n) => ({
      node_id: n.id,
      node_type: n.data.node_type,
      label: n.data.label,
      position: n.position,
      config: n.data.config,
    }));

    const canvasEdges: CanvasWorkflowEdge[] = edges.map((e) => ({
      edge_id: e.id,
      source_node_id: e.source,
      target_node_id: e.target,
      label: e.label as string | undefined,
    }));

    return { nodes: canvasNodes, edges: canvasEdges };
  }, [nodes, edges]);

  // 节点/边变化时通知父组件
  const handleNodesChange = useCallback((changes: NodeChange[]) => {
    onNodesChange(changes);
    if (onChange) {
      setTimeout(() => {
        const config = exportConfig();
        onChange(config.nodes, config.edges);
      }, 0);
    }
  }, [onNodesChange, onChange, exportConfig]);

  const handleEdgesChange = useCallback((changes: EdgeChange[]) => {
    onEdgesChange(changes);
    if (onChange) {
      setTimeout(() => {
        const config = exportConfig();
        onChange(config.nodes, config.edges);
      }, 0);
    }
  }, [onEdgesChange, onChange, exportConfig]);

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodesWithCallbacks}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <Controls />

        {/* 左侧节点类型面板 */}
        <Panel position="top-left" className="w-56">
          <div className="rounded-lg border bg-background p-3 shadow-lg">
            <h3 className="mb-2 text-sm font-semibold">节点类型</h3>
            <div className="max-h-[400px] space-y-1 overflow-auto">
              {Object.entries(NODE_TYPES_CONFIG).map(([type, config]) => (
                <button
                  key={type}
                  onClick={() => handleAddNode(type as WorkflowNodeType)}
                  className="flex w-full items-center gap-2 rounded-md p-2 text-left text-sm hover:bg-accent"
                >
                  <div className={cn('flex h-6 w-6 items-center justify-center rounded text-white', config.color)}>
                    {config.icon}
                  </div>
                  <span>{config.label}</span>
                  <Plus className="ml-auto h-4 w-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          </div>
        </Panel>

        {/* 右侧资源面板 */}
        <Panel position="top-right" className="w-56">
          <div className="space-y-3">
            {/* Agents */}
            <div className="rounded-lg border bg-background p-3 shadow-lg">
              <h3 className="mb-2 text-sm font-semibold">可用 Agents</h3>
              <div className="max-h-[150px] space-y-1 overflow-auto">
                {availableAgents.map((agent) => (
                  <button
                    key={agent.agent_id}
                    onClick={() => {
                      handleAddNode('agent');
                      // TODO: 设置 agent_id 配置
                    }}
                    className="flex w-full items-center gap-2 rounded-md p-2 text-left text-sm hover:bg-accent"
                  >
                    <Bot className="h-4 w-4 text-blue-500" />
                    <span className="truncate">{agent.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Teams */}
            <div className="rounded-lg border bg-background p-3 shadow-lg">
              <h3 className="mb-2 text-sm font-semibold">可用 Teams</h3>
              <div className="max-h-[150px] space-y-1 overflow-auto">
                {availableTeams.map((team) => (
                  <button
                    key={team.team_id}
                    onClick={() => {
                      handleAddNode('team');
                      // TODO: 设置 team_id 配置
                    }}
                    className="flex w-full items-center gap-2 rounded-md p-2 text-left text-sm hover:bg-accent"
                  >
                    <Users className="h-4 w-4 text-purple-500" />
                    <span className="truncate">{team.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Panel>

        {/* 提示信息 */}
        <Panel position="bottom-center">
          <div className="rounded-md bg-muted/80 px-3 py-1.5 text-xs text-muted-foreground">
            从左侧选择节点类型添加到画布 · 连接节点创建执行流程 · 点击节点配置参数
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default WorkflowCanvas;
