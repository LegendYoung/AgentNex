"""
Agent 管理 API 路由
Agent CRUD、草稿、测试、导入导出
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database_postgres import get_db
from models_db import (
    Agent, User, TeamMember, ResourcePermission,
    ResourcePermission as ResPerm, TeamRole
)
from utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# ==================== Pydantic 模型 ====================

class ToolConfig(BaseModel):
    web_search: bool = False
    file_read: bool = False
    python_exec: bool = False
    permission: str = "all"  # all | allow_only | deny_only


class TeamPermissionConfig(BaseModel):
    team_id: str
    permission: str = "view"  # view | edit | manage


class AgentConfig(BaseModel):
    # 基础信息
    name: str = Field(..., min_length=2, max_length=32)
    description: Optional[str] = Field(None, min_length=10, max_length=200)
    avatar_url: Optional[str] = None
    
    # 基础配置
    system_prompt: str = Field(..., min_length=10)
    model_id: str = "qwen-plus"
    temperature: int = Field(70, ge=0, le=200)  # 0-200，存储时乘100
    top_p: int = Field(90, ge=0, le=100)  # 0-100
    
    # 能力开关
    enable_memory: bool = False
    memory_type: str = "short_term"  # short_term | long_term
    memory_window: int = Field(10, ge=1, le=50)
    
    enable_knowledge: bool = False
    knowledge_base_ids: List[str] = []
    
    enable_tools: bool = False
    tool_config: Optional[ToolConfig] = None
    
    # 权限配置
    is_public: bool = False
    team_permissions: Optional[List[TeamPermissionConfig]] = None


class AgentTestRequest(BaseModel):
    agent_config: AgentConfig
    message: str
    session_id: Optional[str] = None


class AgentToggleRequest(BaseModel):
    is_active: bool


class AgentImportRequest(BaseModel):
    code: str


# ==================== 辅助函数 ====================

def check_agent_permission(
    db: Session,
    user_id: str,
    agent: Agent,
    required_permission: str = "view"
) -> bool:
    """
    检查用户对 Agent 的访问权限
    
    权限规则：
    1. 创建者拥有所有权限
    2. 公开 Agent 所有人可查看
    3. 团队共享 Agent 根据权限级别判断
    """
    # 创建者拥有所有权限
    if str(agent.creator_id) == str(user_id):
        return True
    
    # 公开 Agent 所有人可查看
    if agent.is_public and required_permission == "view":
        return True
    
    # 检查团队权限
    permission_record = db.query(ResourcePermission).filter(
        and_(
            ResourcePermission.agent_id == agent.id,
            ResourcePermission.team_id.in_(
                db.query(TeamMember.team_id).filter(
                    TeamMember.user_id == user_id
                )
            )
        )
    ).first()
    
    if permission_record:
        perm_level = {"view": 1, "edit": 2, "manage": 3}
        if perm_level.get(permission_record.permission.value, 0) >= perm_level.get(required_permission, 0):
            return True
    
    return False


# ==================== 创建 Agent ====================

@router.post("")
async def create_agent(
    config: AgentConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建 Agent
    
    流程：
    1. 保存 Agent 配置到数据库
    2. 配置团队权限（如果有）
    3. 返回 Agent ID
    """
    # 创建 Agent
    new_agent = Agent(
        id=uuid.uuid4(),
        name=config.name,
        description=config.description,
        avatar_url=config.avatar_url,
        system_prompt=config.system_prompt,
        model_id=config.model_id,
        temperature=config.temperature,
        top_p=config.top_p,
        enable_memory=config.enable_memory,
        memory_type=config.memory_type,
        memory_window=config.memory_window,
        enable_knowledge=config.enable_knowledge,
        knowledge_base_ids=config.knowledge_base_ids,
        enable_tools=config.enable_tools,
        tool_config=config.tool_config.model_dump() if config.tool_config else {},
        is_public=config.is_public,
        creator_id=current_user.id,
        is_active=True,
        is_draft=False
    )
    
    db.add(new_agent)
    db.flush()
    
    # 配置团队权限
    if config.team_permissions:
        for team_perm in config.team_permissions:
            # 检查用户是否在该团队中
            membership = db.query(TeamMember).filter(
                and_(
                    TeamMember.team_id == team_perm.team_id,
                    TeamMember.user_id == current_user.id
                )
            ).first()
            
            if membership and membership.role in [TeamRole.ADMIN, TeamRole.EDITOR]:
                permission = ResourcePermission(
                    resource_type="agent",
                    agent_id=new_agent.id,
                    team_id=team_perm.team_id,
                    permission=ResPerm(team_perm.permission)
                )
                db.add(permission)
    
    db.commit()
    db.refresh(new_agent)
    
    logger.info(f"Agent created: {new_agent.name} by {current_user.email}")
    
    return {
        "success": True,
        "data": {
            "agent_id": str(new_agent.id),
            "name": new_agent.name,
            "created_at": new_agent.created_at.isoformat()
        }
    }


# ==================== 保存草稿 ====================

@router.post("/draft")
async def save_draft(
    config: AgentConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    保存草稿
    
    草稿 7 天后自动过期
    """
    # 检查是否已有草稿（同一用户同名草稿覆盖）
    existing_draft = db.query(Agent).filter(
        and_(
            Agent.creator_id == current_user.id,
            Agent.name == config.name,
            Agent.is_draft == True
        )
    ).first()
    
    if existing_draft:
        # 更新现有草稿
        existing_draft.description = config.description
        existing_draft.system_prompt = config.system_prompt
        existing_draft.model_id = config.model_id
        existing_draft.temperature = config.temperature
        existing_draft.top_p = config.top_p
        existing_draft.enable_memory = config.enable_memory
        existing_draft.memory_type = config.memory_type
        existing_draft.memory_window = config.memory_window
        existing_draft.enable_knowledge = config.enable_knowledge
        existing_draft.knowledge_base_ids = config.knowledge_base_ids
        existing_draft.enable_tools = config.enable_tools
        existing_draft.tool_config = config.tool_config.model_dump() if config.tool_config else {}
        existing_draft.draft_expires_at = datetime.utcnow() + timedelta(days=7)
        
        db.commit()
        
        return {
            "success": True,
            "data": {
                "draft_id": str(existing_draft.id),
                "expires_at": existing_draft.draft_expires_at.isoformat()
            }
        }
    
    # 创建新草稿
    new_draft = Agent(
        id=uuid.uuid4(),
        name=config.name,
        description=config.description,
        avatar_url=config.avatar_url,
        system_prompt=config.system_prompt,
        model_id=config.model_id,
        temperature=config.temperature,
        top_p=config.top_p,
        enable_memory=config.enable_memory,
        memory_type=config.memory_type,
        memory_window=config.memory_window,
        enable_knowledge=config.enable_knowledge,
        knowledge_base_ids=config.knowledge_base_ids,
        enable_tools=config.enable_tools,
        tool_config=config.tool_config.model_dump() if config.tool_config else {},
        is_public=False,
        creator_id=current_user.id,
        is_active=False,
        is_draft=True,
        draft_expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.add(new_draft)
    db.commit()
    
    logger.info(f"Draft saved: {new_draft.name} by {current_user.email}")
    
    return {
        "success": True,
        "data": {
            "draft_id": str(new_draft.id),
            "expires_at": new_draft.draft_expires_at.isoformat(),
            "created_at": new_draft.created_at.isoformat()
        }
    }


# ==================== 获取草稿列表 ====================

@router.get("/draft")
async def list_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的草稿列表"""
    # 清理过期草稿
    db.query(Agent).filter(
        and_(
            Agent.creator_id == current_user.id,
            Agent.is_draft == True,
            Agent.draft_expires_at < datetime.utcnow()
        )
    ).delete()
    db.commit()
    
    # 查询草稿
    drafts = db.query(Agent).filter(
        and_(
            Agent.creator_id == current_user.id,
            Agent.is_draft == True
        )
    ).order_by(Agent.updated_at.desc()).all()
    
    result = []
    for draft in drafts:
        result.append({
            "draft_id": str(draft.id),
            "name": draft.name,
            "description": draft.description,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat(),
            "expires_at": draft.draft_expires_at.isoformat()
        })
    
    return {
        "success": True,
        "data": {
            "drafts": result,
            "total": len(result)
        }
    }


# ==================== 获取草稿详情 ====================

@router.get("/draft/{draft_id}")
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取草稿详情"""
    draft = db.query(Agent).filter(
        and_(
            Agent.id == draft_id,
            Agent.creator_id == current_user.id,
            Agent.is_draft == True
        )
    ).first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return {
        "success": True,
        "data": {
            "draft_id": str(draft.id),
            "name": draft.name,
            "description": draft.description,
            "avatar_url": draft.avatar_url,
            "system_prompt": draft.system_prompt,
            "model_id": draft.model_id,
            "temperature": draft.temperature,
            "top_p": draft.top_p,
            "enable_memory": draft.enable_memory,
            "memory_type": draft.memory_type,
            "memory_window": draft.memory_window,
            "enable_knowledge": draft.enable_knowledge,
            "knowledge_base_ids": draft.knowledge_base_ids,
            "enable_tools": draft.enable_tools,
            "tool_config": draft.tool_config,
            "expires_at": draft.draft_expires_at.isoformat()
        }
    }


# ==================== 删除草稿 ====================

@router.delete("/draft/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除草稿"""
    draft = db.query(Agent).filter(
        and_(
            Agent.id == draft_id,
            Agent.creator_id == current_user.id,
            Agent.is_draft == True
        )
    ).first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    db.delete(draft)
    db.commit()
    
    return {
        "success": True,
        "message": "Draft deleted successfully"
    }


# ==================== 测试 Agent ====================

@router.post("/test")
async def test_agent(
    request: AgentTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    测试 Agent
    
    使用临时 Agent 实例运行测试，返回完整的执行日志
    """
    try:
        from agno.agent import Agent as AgnoAgent
        from agno.models.dashscope import DashScope
        from database import knowledge
        from tools import get_all_tools
        import os
        
        # 创建临时 Agent
        test_agent = AgnoAgent(
            model=DashScope(
                id=request.agent_config.model_id,
                api_key=os.environ.get("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            ),
            instructions=request.agent_config.system_prompt,
            markdown=True,
            # 记忆配置
            add_memories=request.agent_config.enable_memory,
            # 知识库配置
            knowledge=knowledge if request.agent_config.enable_knowledge else None,
            search_knowledge=request.agent_config.enable_knowledge,
            # 工具配置
            tools=get_all_tools() if request.agent_config.enable_tools else [],
            # 温度参数
            temperature=request.agent_config.temperature / 100.0,
        )
        
        # 运行测试
        response = test_agent.run(
            request.message,
            user_id=str(current_user.id),
            session_id=request.session_id
        )
        
        # 提取执行日志
        result = {
            "response": response.content if hasattr(response, 'content') else str(response),
            "tool_calls": [],
            "knowledge_retrieved": [],
            "memory_used": []
        }
        
        # 提取工具调用日志
        if hasattr(response, 'tools') and response.tools:
            for tool_call in response.tools:
                result["tool_calls"].append({
                    "tool": tool_call.get("tool", "unknown"),
                    "input": tool_call.get("input", ""),
                    "output": tool_call.get("output", ""),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # 提取知识库检索结果
        if hasattr(response, 'knowledge') and response.knowledge:
            for kb_result in response.knowledge:
                result["knowledge_retrieved"].append({
                    "content": kb_result.get("content", ""),
                    "similarity": kb_result.get("similarity", 0),
                    "document": kb_result.get("document", "")
                })
        
        # 提取记忆调用
        if hasattr(response, 'memories') and response.memories:
            for memory in response.memories:
                result["memory_used"].append({
                    "memory_id": str(memory.get("id", "")),
                    "content": memory.get("memory", "")
                })
        
        logger.info(f"Agent tested by {current_user.email}")
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Agent test error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent test failed: {str(e)}")


# ==================== 获取 Agent 列表 ====================

@router.get("")
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    visibility: str = Query("all"),  # all | my | shared
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取 Agent 列表"""
    query = db.query(Agent).filter(Agent.is_draft == False)
    
    # 可见性筛选
    if visibility == "my":
        query = query.filter(Agent.creator_id == current_user.id)
    elif visibility == "shared":
        # 团队共享的 Agent
        query = query.filter(
            or_(
                Agent.is_public == True,
                Agent.id.in_(
                    db.query(ResourcePermission.agent_id).filter(
                        ResourcePermission.team_id.in_(
                            db.query(TeamMember.team_id).filter(
                                TeamMember.user_id == current_user.id
                            )
                        )
                    )
                )
            )
        )
    else:
        # all: 自己创建 + 公开 + 团队共享
        query = query.filter(
            or_(
                Agent.creator_id == current_user.id,
                Agent.is_public == True,
                Agent.id.in_(
                    db.query(ResourcePermission.agent_id).filter(
                        ResourcePermission.team_id.in_(
                            db.query(TeamMember.team_id).filter(
                                TeamMember.user_id == current_user.id
                            )
                        )
                    )
                )
            )
        )
    
    # 搜索
    if search:
        query = query.filter(
            or_(
                Agent.name.ilike(f"%{search}%"),
                Agent.description.ilike(f"%{search}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    agents = query.order_by(Agent.created_at.desc()).offset(offset).limit(page_size).all()
    
    result = []
    for agent in agents:
        result.append({
            "agent_id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "model_id": agent.model_id,
            "is_public": agent.is_public,
            "is_active": agent.is_active,
            "creator": {
                "user_id": str(agent.creator.id),
                "name": agent.creator.name,
                "email": agent.creator.email
            },
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        })
    
    return {
        "success": True,
        "data": {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


# ==================== 获取 Agent 详情 ====================

@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取 Agent 详情"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 权限检查
    if not check_agent_permission(db, str(current_user.id), agent, "view"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return {
        "success": True,
        "data": {
            "agent_id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "avatar_url": agent.avatar_url,
            "system_prompt": agent.system_prompt,
            "model_id": agent.model_id,
            "temperature": agent.temperature,
            "top_p": agent.top_p,
            "enable_memory": agent.enable_memory,
            "memory_type": agent.memory_type,
            "memory_window": agent.memory_window,
            "enable_knowledge": agent.enable_knowledge,
            "knowledge_base_ids": agent.knowledge_base_ids,
            "enable_tools": agent.enable_tools,
            "tool_config": agent.tool_config,
            "is_public": agent.is_public,
            "is_active": agent.is_active,
            "creator": {
                "user_id": str(agent.creator.id),
                "name": agent.creator.name,
                "email": agent.creator.email
            },
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
    }


# ==================== 更新 Agent ====================

@router.put("/{agent_id}")
async def update_agent(
    agent_id: str,
    config: AgentConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 权限检查（需要 edit 权限）
    if not check_agent_permission(db, str(current_user.id), agent, "edit"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 更新配置
    agent.name = config.name
    agent.description = config.description
    agent.avatar_url = config.avatar_url
    agent.system_prompt = config.system_prompt
    agent.model_id = config.model_id
    agent.temperature = config.temperature
    agent.top_p = config.top_p
    agent.enable_memory = config.enable_memory
    agent.memory_type = config.memory_type
    agent.memory_window = config.memory_window
    agent.enable_knowledge = config.enable_knowledge
    agent.knowledge_base_ids = config.knowledge_base_ids
    agent.enable_tools = config.enable_tools
    agent.tool_config = config.tool_config.model_dump() if config.tool_config else {}
    agent.is_public = config.is_public
    
    db.commit()
    
    logger.info(f"Agent updated: {agent.name} by {current_user.email}")
    
    return {
        "success": True,
        "message": "Agent updated successfully"
    }


# ==================== 删除 Agent ====================

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 权限检查（需要 manage 权限）
    if not check_agent_permission(db, str(current_user.id), agent, "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db.delete(agent)
    db.commit()
    
    logger.info(f"Agent deleted: {agent.name} by {current_user.email}")
    
    return {
        "success": True,
        "message": "Agent deleted successfully"
    }


# ==================== 复制 Agent ====================

@router.post("/{agent_id}/copy")
async def copy_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """复制 Agent"""
    original = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not original:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 权限检查
    if not check_agent_permission(db, str(current_user.id), original, "view"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 创建副本
    copy = Agent(
        id=uuid.uuid4(),
        name=f"{original.name} (Copy)",
        description=original.description,
        avatar_url=original.avatar_url,
        system_prompt=original.system_prompt,
        model_id=original.model_id,
        temperature=original.temperature,
        top_p=original.top_p,
        enable_memory=original.enable_memory,
        memory_type=original.memory_type,
        memory_window=original.memory_window,
        enable_knowledge=original.enable_knowledge,
        knowledge_base_ids=original.knowledge_base_ids,
        enable_tools=original.enable_tools,
        tool_config=original.tool_config,
        is_public=False,  # 复制的 Agent 默认私有
        creator_id=current_user.id,
        is_active=True,
        is_draft=False
    )
    
    db.add(copy)
    db.commit()
    
    logger.info(f"Agent copied: {original.name} -> {copy.name} by {current_user.email}")
    
    return {
        "success": True,
        "data": {
            "agent_id": str(copy.id),
            "name": copy.name
        }
    }


# ==================== 启停 Agent ====================

@router.post("/{agent_id}/toggle")
async def toggle_agent(
    agent_id: str,
    request: AgentToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启停 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 权限检查
    if not check_agent_permission(db, str(current_user.id), agent, "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    agent.is_active = request.is_active
    db.commit()
    
    status = "activated" if request.is_active else "deactivated"
    logger.info(f"Agent {status}: {agent.name} by {current_user.email}")
    
    return {
        "success": True,
        "message": f"Agent {status} successfully"
    }
