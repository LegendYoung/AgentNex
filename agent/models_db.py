"""
PostgreSQL 数据库模型定义
基于 SQLAlchemy ORM

核心实体：
- User: 用户表
- Role: 角色表（平台角色）
- Team: 团队表
- TeamMember: 团队成员表
- TeamInvitation: 团队邀请表
- Agent: Agent配置表
- KnowledgeBase: 知识库表
- Document: 文档表
- ResourcePermission: 资源权限表
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database_postgres import Base
import uuid
import enum


# ==================== 枚举定义 ====================

class PlatformRole(str, enum.Enum):
    """平台角色（零模糊定义）"""
    SUPER_ADMIN = "super_admin"      # 超级管理员：唯一，部署后自动初始化
    ADMIN = "admin"                  # 平台管理员
    USER = "user"                    # 普通用户


class TeamRole(str, enum.Enum):
    """团队角色（零模糊定义）"""
    ADMIN = "admin"      # 团队管理员：邀请/移除成员、修改角色、管理团队资源
    EDITOR = "editor"    # 团队编辑者：可编辑团队共享资源，不可管理成员
    VIEWER = "viewer"    # 团队查看者：仅可查看团队共享资源


class ResourcePermission(str, enum.Enum):
    """资源权限"""
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"


class UserStatus(str, enum.Enum):
    """用户状态"""
    ACTIVE = "active"
    DISABLED = "disabled"


# ==================== 用户表 ====================

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(32))
    
    # 平台角色
    role = Column(
        Enum(PlatformRole), 
        default=PlatformRole.USER, 
        nullable=False
    )
    
    # 状态
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    require_password_change = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # 关系
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    created_agents = relationship("Agent", back_populates="creator", cascade="all, delete-orphan")
    created_knowledge_bases = relationship("KnowledgeBase", back_populates="creator", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"


# ==================== 团队表 ====================

class Team(Base):
    """团队表"""
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(32), nullable=False)
    description = Column(String(200))
    
    # 创建者
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    invitations = relationship("TeamInvitation", back_populates="team", cascade="all, delete-orphan")
    creator = relationship("User", backref="created_teams")
    
    def __repr__(self):
        return f"<Team {self.name}>"


# ==================== 团队成员表 ====================

class TeamMember(Base):
    """团队成员表"""
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 团队角色
    role = Column(Enum(TeamRole), default=TeamRole.VIEWER, nullable=False)
    
    # 时间戳
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    
    # 唯一约束：一个用户在一个团队中只能有一个角色
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='unique_team_member'),
    )
    
    def __repr__(self):
        return f"<TeamMember team_id={self.team_id} user_id={self.user_id} role={self.role}>"


# ==================== 团队邀请表 ====================

class TeamInvitation(Base):
    """团队邀请表"""
    __tablename__ = "team_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    # 邀请信息
    email = Column(String(255), nullable=False)  # 被邀请人邮箱
    role = Column(Enum(TeamRole), default=TeamRole.VIEWER, nullable=False)
    invite_code = Column(String(64), unique=True, nullable=False, index=True)  # 唯一邀请码
    
    # 过期时间（24小时）
    expires_at = Column(DateTime, nullable=False)
    
    # 状态
    is_used = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    team = relationship("Team", back_populates="invitations")
    
    def __repr__(self):
        return f"<TeamInvitation email={self.email} team_id={self.team_id}>"


# ==================== Agent 表 ====================

class Agent(Base):
    """Agent 配置表"""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基础信息
    name = Column(String(32), nullable=False)
    description = Column(String(200))
    avatar_url = Column(String(512))
    
    # 配置
    system_prompt = Column(Text, nullable=False)
    model_id = Column(String(64), nullable=False, default="qwen-plus")
    temperature = Column(Integer, default=70)  # 0-200，存储时乘100
    top_p = Column(Integer, default=90)  # 0-100
    
    # 能力开关
    enable_memory = Column(Boolean, default=False)
    memory_type = Column(String(20), default="short_term")  # short_term | long_term
    memory_window = Column(Integer, default=10)  # 1-50轮
    
    enable_knowledge = Column(Boolean, default=False)
    knowledge_base_ids = Column(JSON, default=list)  # 关联的知识库ID列表
    
    enable_tools = Column(Boolean, default=False)
    tool_config = Column(JSON, default=dict)  # 工具配置
    
    # 权限
    is_public = Column(Boolean, default=False, nullable=False)  # 是否公开
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 草稿
    is_draft = Column(Boolean, default=False, nullable=False)
    draft_expires_at = Column(DateTime)  # 草稿过期时间（7天）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship("User", back_populates="created_agents")
    permissions = relationship("ResourcePermission", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Agent {self.name}>"


# ==================== 知识库表 ====================

class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基础信息
    name = Column(String(32), nullable=False)
    description = Column(String(200))
    
    # 分块配置
    chunk_size = Column(Integer, default=512)  # 100-2000
    chunk_overlap = Column(Integer, default=128)  # 0-500
    
    # 权限
    is_public = Column(Boolean, default=False, nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 统计
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship("User", back_populates="created_knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    permissions = relationship("ResourcePermission", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase {self.name}>"


# ==================== 文档表 ====================

class Document(Base):
    """文档表"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False)
    
    # 文档信息
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, md
    file_size = Column(Integer, nullable=False)  # 字节数
    
    # 处理状态
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text)
    
    # 统计
    chunk_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    def __repr__(self):
        return f"<Document {self.filename}>"


# ==================== 资源权限表 ====================

class ResourcePermission(Base):
    """资源权限表（用于团队共享）"""
    __tablename__ = "resource_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 资源类型和ID
    resource_type = Column(String(20), nullable=False)  # agent, knowledge_base
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"))
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"))
    
    # 团队
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    # 权限级别
    permission = Column(Enum(ResourcePermission), default=ResourcePermission.VIEW, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    agent = relationship("Agent", back_populates="permissions")
    knowledge_base = relationship("KnowledgeBase", back_populates="permissions")
    
    def __repr__(self):
        return f"<ResourcePermission resource_type={self.resource_type} team_id={self.team_id}>"


# ==================== Agent Team 表 (P1阶段) ====================

class CommunicationMode(str, enum.Enum):
    """团队通信模式"""
    BROADCAST = "broadcast"      # 广播：所有Agent都收到消息
    POINT_TO_POINT = "point_to_point"  # 点对点：指定接收者
    TOPIC_BASED = "topic_based"  # 主题订阅：按主题分发


class DecisionMode(str, enum.Enum):
    """团队决策模式"""
    VOTING = "voting"            # 投票制：超过半数同意
    LEADER = "leader"            # 负责人制：指定主Agent决策
    UNANIMOUS = "unanimous"      # 一致通过制：所有Agent同意


class AgentTeam(Base):
    """Agent团队表"""
    __tablename__ = "agent_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 基础信息
    name = Column(String(32), nullable=False)
    description = Column(String(200))
    goal = Column(String(500), nullable=False)  # 团队目标

    # 团队配置
    max_rounds = Column(Integer, default=20)  # 最大对话轮数 1-100
    timeout_minutes = Column(Integer, default=10)  # 超时时间 1-60分钟
    global_prompt = Column(Text)  # 团队全局提示词
    entry_agent_id = Column(UUID(as_uuid=True))  # 主入口Agent ID

    # 通信与决策配置
    communication_mode = Column(
        Enum(CommunicationMode),
        default=CommunicationMode.BROADCAST,
        nullable=False
    )
    decision_mode = Column(
        Enum(DecisionMode),
        default=DecisionMode.LEADER,
        nullable=False
    )

    # 权限
    is_public = Column(Boolean, default=False, nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    creator = relationship("User", backref="created_agent_teams")
    nodes = relationship("AgentTeamNode", back_populates="team", cascade="all, delete-orphan")
    edges = relationship("AgentTeamEdge", back_populates="team", cascade="all, delete-orphan")
    sessions = relationship("AgentTeamSession", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AgentTeam {self.name}>"


class AgentTeamNode(Base):
    """Agent团队节点表（画布上的Agent节点）"""
    __tablename__ = "agent_team_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

    # 画布位置
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)

    # 节点配置
    role_in_team = Column(String(32))  # 团队中的角色名称
    responsibilities = Column(String(500))  # 职责描述
    allowed_tools = Column(JSON, default=list)  # 允许的工具列表
    can_call_agents = Column(JSON, default=list)  # 可调用的其他Agent节点ID

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    team = relationship("AgentTeam", back_populates="nodes")
    agent = relationship("Agent")

    def __repr__(self):
        return f"<AgentTeamNode team_id={self.team_id} agent_id={self.agent_id}>"


class AgentTeamEdge(Base):
    """Agent团队连线表（节点间的连接）"""
    __tablename__ = "agent_team_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=False)

    # 连接关系
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("agent_team_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("agent_team_nodes.id", ondelete="CASCADE"), nullable=False)

    # 条件分支（可选）
    condition_type = Column(String(20))  # expression, always
    condition_value = Column(Text)  # 条件表达式或值

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    team = relationship("AgentTeam", back_populates="edges")
    source_node = relationship("AgentTeamNode", foreign_keys=[source_node_id])
    target_node = relationship("AgentTeamNode", foreign_keys=[target_node_id])

    def __repr__(self):
        return f"<AgentTeamEdge {self.source_node_id} -> {self.target_node_id}>"


class AgentTeamSession(Base):
    """Agent团队会话表（对话历史）"""
    __tablename__ = "agent_team_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 会话状态
    status = Column(String(20), default="active", nullable=False)  # active, completed, failed

    # 对话历史（JSON格式存储完整对话）
    messages = Column(JSON, default=list)

    # 任务状态追踪
    task_status = Column(JSON, default=dict)  # 每个Agent的任务状态

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # 关系
    team = relationship("AgentTeam", back_populates="sessions")
    user = relationship("User")

    def __repr__(self):
        return f"<AgentTeamSession team_id={self.team_id} status={self.status}>"


# ==================== 工作流引擎模型 (P2) ====================

class WorkflowTriggerType(str, enum.Enum):
    """工作流触发类型"""
    MANUAL = "manual"           # 手动触发
    API = "api"                 # API 触发
    SCHEDULE = "schedule"       # 定时触发
    WEBHOOK = "webhook"         # Webhook 触发
    EVENT = "event"             # 事件触发


class WorkflowNodeType(str, enum.Enum):
    """工作流节点类型"""
    START = "start"             # 开始节点
    END = "end"                 # 结束节点
    AGENT = "agent"             # Agent 节点
    TEAM = "team"               # Agent Team 节点
    CONDITION = "condition"     # 条件分支节点
    LOOP = "loop"               # 循环节点
    PARALLEL = "parallel"       # 并行节点
    HUMAN_INPUT = "human_input" # 人工输入节点
    CODE = "code"               # 代码执行节点
    API_CALL = "api_call"       # API 调用节点
    DELAY = "delay"             # 延迟节点


class WorkflowStatus(str, enum.Enum):
    """工作流状态"""
    DRAFT = "draft"             # 草稿
    ACTIVE = "active"           # 激活
    ARCHIVED = "archived"       # 已归档


class ExecutionStatus(str, enum.Enum):
    """执行状态"""
    PENDING = "pending"         # 待执行
    RUNNING = "running"         # 执行中
    PAUSED = "paused"           # 已暂停（等待人工输入）
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 执行失败
    CANCELLED = "cancelled"     # 已取消
    TIMEOUT = "timeout"         # 超时


class Workflow(Base):
    """工作流模板表"""
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 工作流配置
    trigger_type = Column(String(20), default=WorkflowTriggerType.MANUAL.value, nullable=False)
    trigger_config = Column(JSON, default=dict)  # 触发配置（定时规则、Webhook配置等）
    variables = Column(JSON, default=list)       # 工作流变量定义
    
    # 状态
    status = Column(String(20), default=WorkflowStatus.DRAFT.value, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # 版本管理
    version = Column(Integer, default=1, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))  # 父版本（版本管理）
    
    # 统计
    execution_count = Column(Integer, default=0)
    last_execution_at = Column(DateTime)
    
    # 创建者
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship("User")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow {self.name} v{self.version}>"


class WorkflowNode(Base):
    """工作流节点表"""
    __tablename__ = "workflow_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    
    # 节点信息
    node_type = Column(String(20), nullable=False)
    label = Column(String(100))
    description = Column(Text)
    
    # 位置（画布坐标）
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    
    # 节点配置（JSON格式，根据节点类型不同而不同）
    # agent: {agent_id, input_mapping, output_mapping}
    # team: {team_id, ...}
    # condition: {expression, branches}
    # loop: {max_iterations, ...}
    # human_input: {prompt, timeout, default_value}
    # code: {language, code}
    # api_call: {url, method, headers, body}
    config = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    workflow = relationship("Workflow", back_populates="nodes")
    
    def __repr__(self):
        return f"<WorkflowNode {self.node_type}: {self.label}>"


class WorkflowEdge(Base):
    """工作流连线表"""
    __tablename__ = "workflow_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    
    # 连接关系
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id"), nullable=False)
    
    # 条件配置
    label = Column(String(100))                          # 连线标签
    condition_type = Column(String(20))                   # always, expression, output_match
    condition_value = Column(Text)                        # 条件值/表达式
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    workflow = relationship("Workflow", back_populates="edges")
    source_node = relationship("WorkflowNode", foreign_keys=[source_node_id])
    target_node = relationship("WorkflowNode", foreign_keys=[target_node_id])
    
    def __repr__(self):
        return f"<WorkflowEdge {self.source_node_id} -> {self.target_node_id}>"


class WorkflowExecution(Base):
    """工作流执行实例表"""
    __tablename__ = "workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 执行状态
    status = Column(String(20), default=ExecutionStatus.PENDING.value, nullable=False)
    
    # 当前执行节点
    current_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id"))
    
    # 执行数据
    input_data = Column(JSON, default=dict)       # 输入参数
    output_data = Column(JSON, default=dict)      # 输出结果
    variables = Column(JSON, default=dict)        # 运行时变量
    
    # 错误信息
    error_message = Column(Text)
    error_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id"))
    
    # 时间戳
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    workflow = relationship("Workflow", back_populates="executions")
    user = relationship("User")
    current_node = relationship("WorkflowNode", foreign_keys=[current_node_id])
    error_node = relationship("WorkflowNode", foreign_keys=[error_node_id])
    logs = relationship("WorkflowExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkflowExecution {self.workflow_id} status={self.status}>"


class WorkflowExecutionLog(Base):
    """工作流执行日志表"""
    __tablename__ = "workflow_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False)
    
    # 节点信息
    node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id"))
    node_type = Column(String(20))
    node_label = Column(String(100))
    
    # 事件信息
    event_type = Column(String(20), nullable=False)  # started, completed, failed, skipped, waiting_input
    message = Column(Text)
    
    # 执行数据
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # 错误信息
    error_message = Column(Text)
    
    # 性能指标
    duration_ms = Column(Integer)  # 执行耗时（毫秒）
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="logs")
    node = relationship("WorkflowNode")
    
    def __repr__(self):
        return f"<WorkflowExecutionLog {self.event_type}: {self.node_label}>"
