/**
 * Agent Team 画布组件
 * P1阶段：基于React Flow的拖拽编排画布
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
import { Bot, Settings, Trash2, Plus } from 'lucide-react';
import type { CanvasNode, CanvasEdge, AgentTeamNodeConfig } from '@/api/agentTeams';

// Agent节点自定义组件
interface AgentNodeData {
  agent_id: string;
  agent_name: string;
  config: AgentTeamNodeConfig;
  onEdit?: (nodeId: string) => void;
  onDelete?: (nodeId: string) => void;
}

function AgentNodeComponent({ data, id }: { data: AgentNodeData; id: string }) {
  return (
    <div className="min-w-[200px] rounded-lg border-2 border-primary/50 bg-background shadow-lg">
      {/* 头部 */}
      <div className="flex items-center gap-2 border-b bg-primary/10 px-3 py-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
          <Bot className="h-4 w-4 text-primary-foreground" />
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold">{data.agent_name}</div>
          <div className="text-xs text-muted-foreground">
            {data.config.role_in_team || '成员'}
          </div>
        </div>
      </div>

      {/* 内容 */}
      <div className="p-3">
        {data.config.responsibilities && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {data.config.responsibilities}
          </p>
        )}

        {/* 工具标签 */}
        {data.config.allowed_tools.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {data.config.allowed_tools.slice(0, 3).map((tool, i) => (
              <span key={i} className="rounded bg-muted px-1.5 py-0.5 text-xs">
                {tool}
              </span>
            ))}
            {data.config.allowed_tools.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{data.config.allowed_tools.length - 3}
              </span>
            )}
          </div>
        )}
      </div>

      {/* 操作按钮 */}
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

      {/* 连接点 */}
      <div
        className="absolute left-0 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-primary bg-background"
        style={{ left: -6 }}
      />
      <div
        className="absolute right-0 top-1/2 h-3 w-3 translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-primary bg-background"
        style={{ right: -6 }}
      />
    </div>
  );
}

const nodeTypes = {
  agent: AgentNodeComponent,
};

interface TeamCanvasProps {
  initialNodes?: CanvasNode[];
  initialEdges?: CanvasEdge[];
  availableAgents: { agent_id: string; name: string }[];
  onChange?: (nodes: CanvasNode[], edges: CanvasEdge[]) => void;
  onSave?: (nodes: CanvasNode[], edges: CanvasEdge[]) => void;
}

export function TeamCanvas({
  initialNodes = [],
  initialEdges = [],
  availableAgents,
  onChange,
  onSave,
}: TeamCanvasProps) {
  // 转换为React Flow格式
  const [nodes, setNodes, onNodesChange] = useNodesState(
    initialNodes.map((n) => ({
      id: n.node_id || `node-${Date.now()}-${Math.random()}`,
      type: 'agent',
      position: n.position,
      data: {
        agent_id: n.agent_id,
        agent_name: n.agent_name || 'Agent',
        config: n.config,
      },
    }))
  );

  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialEdges.map((e) => ({
      id: e.edge_id || `edge-${Date.now()}-${Math.random()}`,
      source: e.source_node_id,
      target: e.target_node_id,
      markerEnd: { type: MarkerType.ArrowClosed },
      animated: true,
    }))
  );

  // 节点编辑
  const handleEditNode = useCallback((nodeId: string) => {
    // TODO: 打开节点配置弹窗
    console.log('Edit node:', nodeId);
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

  // 添加Agent节点
  const handleAddAgent = useCallback((agentId: string) => {
    const agent = availableAgents.find((a) => a.agent_id === agentId);
    if (!agent) return;

    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'agent',
      position: { x: 250 + nodes.length * 50, y: 150 + nodes.length * 50 },
      data: {
        agent_id: agent.agent_id,
        agent_name: agent.name,
        config: {
          role_in_team: '',
          responsibilities: '',
          allowed_tools: [],
          can_call_agents: [],
        },
        onEdit: handleEditNode,
        onDelete: handleDeleteNode,
      },
    };

    setNodes((nds) => [...nds, newNode]);
  }, [nodes.length, availableAgents, setNodes, handleEditNode, handleDeleteNode]);

  // 更新节点数据，添加编辑/删除回调
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
  const exportConfig = useCallback((): { nodes: CanvasNode[]; edges: CanvasEdge[] } => {
    const canvasNodes: CanvasNode[] = nodes.map((n) => ({
      node_id: n.id,
      agent_id: n.data.agent_id,
      agent_name: n.data.agent_name,
      position: n.position,
      config: n.data.config,
    }));

    const canvasEdges: CanvasEdge[] = edges.map((e) => ({
      edge_id: e.id,
      source_node_id: e.source,
      target_node_id: e.target,
      condition: e.data?.condition,
    }));

    return { nodes: canvasNodes, edges: canvasEdges };
  }, [nodes, edges]);

  // 节点/边变化时通知父组件
  const handleNodesChange = useCallback((changes: NodeChange[]) => {
    onNodesChange(changes);
    if (onChange) {
      setTimeout(() => onChange(exportConfig().nodes, exportConfig().edges), 0);
    }
  }, [onNodesChange, onChange, exportConfig]);

  const handleEdgesChange = useCallback((changes: EdgeChange[]) => {
    onEdgesChange(changes);
    if (onChange) {
      setTimeout(() => onChange(exportConfig().nodes, exportConfig().edges), 0);
    }
  }, [onEdgesChange, onChange, exportConfig]);

  // 保存方法
  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(exportConfig().nodes, exportConfig().edges);
    }
  }, [onSave, exportConfig]);

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

        {/* 左侧Agent选择面板 */}
        <Panel position="top-left" className="w-64">
          <div className="rounded-lg border bg-background p-3 shadow-lg">
            <h3 className="mb-2 text-sm font-semibold">可用 Agents</h3>
            <div className="max-h-[300px] space-y-1 overflow-auto">
              {availableAgents.map((agent) => (
                <button
                  key={agent.agent_id}
                  onClick={() => handleAddAgent(agent.agent_id)}
                  className="flex w-full items-center gap-2 rounded-md p-2 text-left text-sm hover:bg-accent"
                >
                  <Bot className="h-4 w-4 text-primary" />
                  <span>{agent.name}</span>
                  <Plus className="ml-auto h-4 w-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          </div>
        </Panel>

        {/* 提示信息 */}
        <Panel position="bottom-center">
          <div className="rounded-md bg-muted/80 px-3 py-1.5 text-xs text-muted-foreground">
            从左侧拖拽Agent到画布 · 连接节点创建协作流程 · 点击节点配置
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default TeamCanvas;
