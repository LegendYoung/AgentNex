"""
Agent Team Pydantic 模型定义
P1阶段：多智能体团队管理
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ==================== 枚举 ====================

class CommunicationMode(str, Enum):
    """团队通信模式"""
    BROADCAST = "broadcast"
    POINT_TO_POINT = "point_to_point"
    TOPIC_BASED = "topic_based"


class DecisionMode(str, Enum):
    """团队决策模式"""
    VOTING = "voting"
    LEADER = "leader"
    UNANIMOUS = "unanimous"


# ==================== 请求模型 ====================

class AgentTeamNodeConfig(BaseModel):
    """Agent节点配置"""
    role_in_team: Optional[str] = Field(None, max_length=32, description="团队中的角色名称")
    responsibilities: Optional[str] = Field(None, max_length=500, description="职责描述")
    allowed_tools: List[str] = Field(default_factory=list, description="允许的工具列表")
    can_call_agents: List[str] = Field(default_factory=list, description="可调用的其他Agent节点ID")


class CanvasNode(BaseModel):
    """画布节点"""
    node_id: Optional[str] = Field(None, description="节点ID，新建时不传")
    agent_id: str = Field(..., description="关联的Agent ID")
    position: Dict[str, int] = Field(..., description="画布位置 {x, y}")
    config: AgentTeamNodeConfig = Field(default_factory=AgentTeamNodeConfig)


class CanvasEdgeCondition(BaseModel):
    """连线条件"""
    type: str = Field(default="always", description="条件类型: always, expression")
    value: Optional[str] = Field(None, description="条件表达式或值")


class CanvasEdge(BaseModel):
    """画布连线"""
    edge_id: Optional[str] = Field(None, description="连线ID，新建时不传")
    source_node_id: str = Field(..., description="源节点ID")
    target_node_id: str = Field(..., description="目标节点ID")
    condition: Optional[CanvasEdgeCondition] = Field(None, description="条件分支")


class TeamConfig(BaseModel):
    """团队配置"""
    max_rounds: int = Field(default=20, ge=1, le=100, description="最大对话轮数")
    timeout_minutes: int = Field(default=10, ge=1, le=60, description="超时时间(分钟)")
    entry_agent_id: Optional[str] = Field(None, description="主入口Agent ID")
    global_prompt: Optional[str] = Field(None, description="团队全局提示词")


class CreateAgentTeamRequest(BaseModel):
    """创建Agent团队请求"""
    name: str = Field(..., min_length=2, max_length=32, description="团队名称")
    description: Optional[str] = Field(None, min_length=10, max_length=200, description="团队描述")
    goal: str = Field(..., min_length=10, max_length=500, description="团队目标")
    team_config: TeamConfig = Field(default_factory=TeamConfig, description="团队配置")
    communication_mode: CommunicationMode = Field(default=CommunicationMode.BROADCAST, description="通信模式")
    decision_mode: DecisionMode = Field(default=DecisionMode.LEADER, description="决策模式")


class UpdateAgentTeamRequest(BaseModel):
    """更新Agent团队请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=32)
    description: Optional[str] = Field(None, min_length=10, max_length=200)
    goal: Optional[str] = Field(None, min_length=10, max_length=500)
    team_config: Optional[TeamConfig] = None
    communication_mode: Optional[CommunicationMode] = None
    decision_mode: Optional[DecisionMode] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class SaveCanvasRequest(BaseModel):
    """保存画布配置请求"""
    nodes: List[CanvasNode] = Field(..., description="节点列表")
    edges: List[CanvasEdge] = Field(..., description="连线列表")


class RunTeamRequest(BaseModel):
    """运行团队任务请求"""
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID，用于继续对话")


# ==================== 响应模型 ====================

class AgentTeamNodeResponse(BaseModel):
    """Agent节点响应"""
    node_id: str
    agent_id: str
    agent_name: Optional[str] = None
    position: Dict[str, int]
    config: AgentTeamNodeConfig
    created_at: datetime


class AgentTeamEdgeResponse(BaseModel):
    """Agent连线响应"""
    edge_id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[CanvasEdgeCondition]


class AgentTeamResponse(BaseModel):
    """Agent团队响应"""
    team_id: str
    name: str
    description: Optional[str]
    goal: str
    team_config: TeamConfig
    communication_mode: CommunicationMode
    decision_mode: DecisionMode
    is_public: bool
    is_active: bool
    creator: Optional[Dict[str, str]] = None
    node_count: int = 0
    created_at: datetime
    updated_at: datetime


class AgentTeamDetailResponse(AgentTeamResponse):
    """Agent团队详情响应（含画布配置）"""
    nodes: List[AgentTeamNodeResponse] = []
    edges: List[AgentTeamEdgeResponse] = []


class AgentTeamListResponse(BaseModel):
    """Agent团队列表响应"""
    items: List[AgentTeamResponse]
    total: int
    page: int
    page_size: int


class CanvasResponse(BaseModel):
    """画布配置响应"""
    team_id: str
    nodes: List[AgentTeamNodeResponse]
    edges: List[AgentTeamEdgeResponse]


class TeamSessionMessage(BaseModel):
    """团队会话消息"""
    role: str  # user, assistant, system
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None  # 工具调用、决策等额外信息


class TeamSessionResponse(BaseModel):
    """团队会话响应"""
    session_id: str
    team_id: str
    status: str
    messages: List[TeamSessionMessage]
    task_status: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class TeamSessionListResponse(BaseModel):
    """团队会话列表响应"""
    items: List[TeamSessionResponse]
    total: int
    page: int
    page_size: int


# ==================== 运行时响应 ====================

class TeamRunEvent(BaseModel):
    """团队运行事件（SSE流式响应）"""
    type: str  # agent_message, agent_transfer, decision, tool_call, complete, error
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    content: Optional[str] = None
    from_agent: Optional[str] = None
    to_agent: Optional[str] = None
    decision: Optional[Dict[str, Any]] = None
    tool_call: Optional[Dict[str, Any]] = None
    result: Optional[str] = None
    error: Optional[str] = None
