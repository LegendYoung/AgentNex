"""
Workflow 请求/响应模型
P2阶段：工作流引擎
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class WorkflowTriggerType(str, Enum):
    MANUAL = "manual"
    API = "api"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    EVENT = "event"


class WorkflowNodeType(str, Enum):
    START = "start"
    END = "end"
    AGENT = "agent"
    TEAM = "team"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    HUMAN_INPUT = "human_input"
    CODE = "code"
    API_CALL = "api_call"
    DELAY = "delay"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# ==================== 节点配置模型 ====================

class AgentNodeConfig(BaseModel):
    """Agent 节点配置"""
    agent_id: str
    input_mapping: Optional[Dict[str, str]] = None   # 变量映射
    output_mapping: Optional[Dict[str, str]] = None  # 输出映射
    timeout_seconds: Optional[int] = 300


class TeamNodeConfig(BaseModel):
    """Agent Team 节点配置"""
    team_id: str
    input_mapping: Optional[Dict[str, str]] = None
    output_mapping: Optional[Dict[str, str]] = None
    timeout_seconds: Optional[int] = 600


class ConditionBranch(BaseModel):
    """条件分支"""
    label: str
    expression: str  # CEL 表达式
    target_node_id: Optional[str] = None


class ConditionNodeConfig(BaseModel):
    """条件节点配置"""
    branches: List[ConditionBranch]
    default_branch: Optional[str] = None  # 默认分支的 target_node_id


class LoopNodeConfig(BaseModel):
    """循环节点配置"""
    loop_var: str = "item"           # 循环变量名
    iterable_expression: str         # 可迭代对象表达式
    max_iterations: Optional[int] = 100
    body_start_node_id: Optional[str] = None


class ParallelNodeConfig(BaseModel):
    """并行节点配置"""
    branches: List[str]  # 并行分支的起始节点 ID 列表
    wait_all: bool = True  # True: 等待所有分支完成; False: 任一完成即可


class HumanInputConfig(BaseModel):
    """人工输入节点配置"""
    prompt: str                       # 提示信息
    input_type: str = "text"          # text, select, multiselect, file
    options: Optional[List[str]] = None  # 选项（select/multiselect 时使用）
    default_value: Optional[str] = None
    timeout_seconds: Optional[int] = 3600  # 超时时间（秒）
    timeout_action: str = "default"   # default, fail, skip


class CodeNodeConfig(BaseModel):
    """代码节点配置"""
    language: str = "python"          # python, javascript
    code: str
    timeout_seconds: Optional[int] = 60


class ApiCallNodeConfig(BaseModel):
    """API 调用节点配置"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = 30


class DelayNodeConfig(BaseModel):
    """延迟节点配置"""
    delay_seconds: int
    delay_until: Optional[str] = None  # ISO 格式时间字符串，定时执行


# ==================== 画布节点/连线 ====================

class WorkflowNodeData(BaseModel):
    """工作流节点数据"""
    node_type: WorkflowNodeType
    label: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class CanvasWorkflowNode(BaseModel):
    """画布上的工作流节点"""
    node_id: Optional[str] = None
    node_type: WorkflowNodeType
    label: Optional[str] = None
    description: Optional[str] = None
    position: Dict[str, float]  # {x, y}
    config: Dict[str, Any] = Field(default_factory=dict)


class CanvasWorkflowEdge(BaseModel):
    """画布上的工作流连线"""
    edge_id: Optional[str] = None
    source_node_id: str
    target_node_id: str
    label: Optional[str] = None
    condition_type: Optional[str] = None  # always, expression, output_match
    condition_value: Optional[str] = None


class SaveWorkflowCanvasRequest(BaseModel):
    """保存工作流画布请求"""
    nodes: List[CanvasWorkflowNode]
    edges: List[CanvasWorkflowEdge]


# ==================== 工作流 CRUD ====================

class WorkflowVariable(BaseModel):
    """工作流变量定义"""
    name: str
    type: str = "string"  # string, number, boolean, object, array
    default_value: Optional[Any] = None
    description: Optional[str] = None
    required: bool = False


class CreateWorkflowRequest(BaseModel):
    """创建工作流请求"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    trigger_type: WorkflowTriggerType = WorkflowTriggerType.MANUAL
    trigger_config: Optional[Dict[str, Any]] = None
    variables: Optional[List[WorkflowVariable]] = None
    is_public: bool = False


class UpdateWorkflowRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    trigger_type: Optional[WorkflowTriggerType] = None
    trigger_config: Optional[Dict[str, Any]] = None
    variables: Optional[List[WorkflowVariable]] = None
    status: Optional[WorkflowStatus] = None
    is_public: Optional[bool] = None


# ==================== 工作流执行 ====================

class RunWorkflowRequest(BaseModel):
    """执行工作流请求"""
    input_data: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None


class ContinueWorkflowRequest(BaseModel):
    """继续执行工作流请求（提供人工输入）"""
    execution_id: str
    node_id: str
    input_value: Any


# ==================== 响应模型 ====================

class WorkflowNodeResponse(BaseModel):
    """工作流节点响应"""
    node_id: str
    node_type: str
    label: Optional[str] = None
    description: Optional[str] = None
    position: Dict[str, float]
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class WorkflowEdgeResponse(BaseModel):
    """工作流连线响应"""
    edge_id: str
    source_node_id: str
    target_node_id: str
    label: Optional[str] = None
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    variables: List[WorkflowVariable] = Field(default_factory=list)
    status: str
    is_public: bool
    version: int
    execution_count: int
    last_execution_at: Optional[datetime] = None
    creator: Optional[Dict[str, str]] = None
    created_at: datetime
    updated_at: datetime


class WorkflowDetailResponse(WorkflowResponse):
    """工作流详情响应（含节点和连线）"""
    nodes: List[WorkflowNodeResponse] = Field(default_factory=list)
    edges: List[WorkflowEdgeResponse] = Field(default_factory=list)


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    items: List[WorkflowResponse]
    total: int
    page: int
    page_size: int


class ExecutionLogResponse(BaseModel):
    """执行日志响应"""
    log_id: str
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    node_label: Optional[str] = None
    event_type: str
    message: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    timestamp: datetime


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    execution_id: str
    workflow_id: str
    status: str
    current_node_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_node_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class WorkflowExecutionDetailResponse(WorkflowExecutionResponse):
    """工作流执行详情响应（含日志）"""
    logs: List[ExecutionLogResponse] = Field(default_factory=list)


class WorkflowExecutionListResponse(BaseModel):
    """工作流执行列表响应"""
    items: List[WorkflowExecutionResponse]
    total: int
    page: int
    page_size: int


# ==================== SSE 事件 ====================

class WorkflowRunEvent(BaseModel):
    """工作流运行事件"""
    event_type: str  # started, node_started, node_completed, node_failed, waiting_input, completed, failed
    execution_id: str
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    node_label: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
