"""
Agent Teams API 路由
P1阶段：多智能体团队管理
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from datetime import datetime
import uuid
import json
import asyncio

from agent.database_postgres import get_db
from agent.models_db import (
    User, Agent, AgentTeam, AgentTeamNode, AgentTeamEdge, AgentTeamSession,
    TeamMember, PlatformRole, CommunicationMode, DecisionMode, ResourcePermission
)
from agent.models_agent_team import (
    CreateAgentTeamRequest, UpdateAgentTeamRequest, SaveCanvasRequest,
    RunTeamRequest, AgentTeamResponse, AgentTeamDetailResponse,
    AgentTeamListResponse, CanvasResponse, TeamSessionResponse,
    TeamSessionListResponse, TeamRunEvent, AgentTeamNodeResponse,
    AgentTeamEdgeResponse, TeamConfig, AgentTeamNodeConfig
)
from agent.utils.auth import get_current_user, require_role
from agent.services.agent_team_service import AgentTeamService

router = APIRouter(prefix="/api/v1/agent-teams", tags=["Agent Teams"])


# ==================== 团队 CRUD ====================

@router.post("", response_model=dict)
async def create_agent_team(
    request: CreateAgentTeamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建Agent团队

    - **name**: 团队名称（2-32字符）
    - **description**: 团队描述（可选）
    - **goal**: 团队目标（10-500字符）
    - **team_config**: 团队配置（最大轮数、超时时间等）
    """
    # 创建团队
    team = AgentTeam(
        id=uuid.uuid4(),
        name=request.name,
        description=request.description,
        goal=request.goal,
        max_rounds=request.team_config.max_rounds,
        timeout_minutes=request.team_config.timeout_minutes,
        entry_agent_id=uuid.UUID(request.team_config.entry_agent_id) if request.team_config.entry_agent_id else None,
        global_prompt=request.team_config.global_prompt,
        communication_mode=request.communication_mode,
        decision_mode=request.decision_mode,
        creator_id=current_user.id,
        is_public=False,
        is_active=True
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    return {
        "success": True,
        "data": {
            "team_id": str(team.id),
            "name": team.name,
            "goal": team.goal,
            "created_at": team.created_at.isoformat()
        }
    }


@router.get("", response_model=dict)
async def list_agent_teams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    visibility: str = Query("all", regex="^(all|my|shared)$"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent团队列表

    - **visibility**: all(全部), my(我的), shared(共享给我)
    - **search**: 搜索关键词
    """
    query = db.query(AgentTeam).filter(AgentTeam.is_active == True)

    # 权限过滤
    if visibility == "my":
        query = query.filter(AgentTeam.creator_id == current_user.id)
    elif visibility == "shared":
        # 通过团队成员关系获取共享的团队
        team_ids = db.query(TeamMember.team_id).filter(
            TeamMember.user_id == current_user.id
        ).all()
        team_ids = [t[0] for t in team_ids]
        query = query.filter(
            or_(
                AgentTeam.creator_id == current_user.id,
                and_(AgentTeam.is_public == True, AgentTeam.id.in_(team_ids))
            )
        )
    else:  # all
        query = query.filter(
            or_(
                AgentTeam.creator_id == current_user.id,
                AgentTeam.is_public == True
            )
        )

    # 搜索
    if search:
        query = query.filter(
            or_(
                AgentTeam.name.ilike(f"%{search}%"),
                AgentTeam.description.ilike(f"%{search}%"),
                AgentTeam.goal.ilike(f"%{search}%")
            )
        )

    # 统计
    total = query.count()

    # 分页
    teams = query.order_by(AgentTeam.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 构建响应
    items = []
    for team in teams:
        node_count = db.query(AgentTeamNode).filter(
            AgentTeamNode.team_id == team.id
        ).count()

        items.append({
            "team_id": str(team.id),
            "name": team.name,
            "description": team.description,
            "goal": team.goal,
            "team_config": {
                "max_rounds": team.max_rounds,
                "timeout_minutes": team.timeout_minutes,
                "entry_agent_id": str(team.entry_agent_id) if team.entry_agent_id else None,
                "global_prompt": team.global_prompt
            },
            "communication_mode": team.communication_mode.value,
            "decision_mode": team.decision_mode.value,
            "is_public": team.is_public,
            "is_active": team.is_active,
            "creator": {
                "user_id": str(team.creator.id),
                "name": team.creator.name,
                "email": team.creator.email
            },
            "node_count": node_count,
            "created_at": team.created_at.isoformat(),
            "updated_at": team.updated_at.isoformat()
        })

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/{team_id}", response_model=dict)
async def get_agent_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent团队详情（含画布配置）
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查
    if team.creator_id != current_user.id and not team.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this team")

    # 获取节点
    nodes = db.query(AgentTeamNode).filter(
        AgentTeamNode.team_id == team.id
    ).all()

    # 获取连线
    edges = db.query(AgentTeamEdge).filter(
        AgentTeamEdge.team_id == team.id
    ).all()

    # 构建节点响应
    node_responses = []
    for node in nodes:
        agent = db.query(Agent).filter(Agent.id == node.agent_id).first()
        node_responses.append({
            "node_id": str(node.id),
            "agent_id": str(node.agent_id),
            "agent_name": agent.name if agent else None,
            "position": {"x": node.position_x, "y": node.position_y},
            "config": {
                "role_in_team": node.role_in_team,
                "responsibilities": node.responsibilities,
                "allowed_tools": node.allowed_tools or [],
                "can_call_agents": node.can_call_agents or []
            },
            "created_at": node.created_at.isoformat()
        })

    # 构建连线响应
    edge_responses = []
    for edge in edges:
        edge_responses.append({
            "edge_id": str(edge.id),
            "source_node_id": str(edge.source_node_id),
            "target_node_id": str(edge.target_node_id),
            "condition": {
                "type": edge.condition_type or "always",
                "value": edge.condition_value
            } if edge.condition_type else None
        })

    return {
        "success": True,
        "data": {
            "team_id": str(team.id),
            "name": team.name,
            "description": team.description,
            "goal": team.goal,
            "team_config": {
                "max_rounds": team.max_rounds,
                "timeout_minutes": team.timeout_minutes,
                "entry_agent_id": str(team.entry_agent_id) if team.entry_agent_id else None,
                "global_prompt": team.global_prompt
            },
            "communication_mode": team.communication_mode.value,
            "decision_mode": team.decision_mode.value,
            "is_public": team.is_public,
            "is_active": team.is_active,
            "creator": {
                "user_id": str(team.creator.id),
                "name": team.creator.name,
                "email": team.creator.email
            },
            "nodes": node_responses,
            "edges": edge_responses,
            "created_at": team.created_at.isoformat(),
            "updated_at": team.updated_at.isoformat()
        }
    }


@router.put("/{team_id}", response_model=dict)
async def update_agent_team(
    team_id: str,
    request: UpdateAgentTeamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新Agent团队配置
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查：仅创建者可修改
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to modify this team")

    # 更新字段
    if request.name is not None:
        team.name = request.name
    if request.description is not None:
        team.description = request.description
    if request.goal is not None:
        team.goal = request.goal
    if request.team_config is not None:
        team.max_rounds = request.team_config.max_rounds
        team.timeout_minutes = request.team_config.timeout_minutes
        if request.team_config.entry_agent_id:
            team.entry_agent_id = uuid.UUID(request.team_config.entry_agent_id)
        team.global_prompt = request.team_config.global_prompt
    if request.communication_mode is not None:
        team.communication_mode = request.communication_mode
    if request.decision_mode is not None:
        team.decision_mode = request.decision_mode
    if request.is_public is not None:
        team.is_public = request.is_public
    if request.is_active is not None:
        team.is_active = request.is_active

    db.commit()
    db.refresh(team)

    return {
        "success": True,
        "data": {
            "team_id": str(team.id),
            "name": team.name,
            "updated_at": team.updated_at.isoformat()
        }
    }


@router.delete("/{team_id}", response_model=dict)
async def delete_agent_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除Agent团队
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查：仅创建者可删除
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to delete this team")

    db.delete(team)
    db.commit()

    return {"success": True, "message": "Team deleted successfully"}


# ==================== 画布配置管理 ====================

@router.post("/{team_id}/canvas", response_model=dict)
async def save_canvas(
    team_id: str,
    request: SaveCanvasRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    保存画布配置（节点+连线）
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查
    if team.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to modify this team")

    # 验证所有Agent是否存在且有权限
    agent_ids = [node.agent_id for node in request.nodes]
    agents = db.query(Agent).filter(Agent.id.in_([uuid.UUID(aid) for aid in agent_ids])).all()
    if len(agents) != len(agent_ids):
        raise HTTPException(status_code=400, detail="Some agents not found")

    # 删除现有节点和连线
    db.query(AgentTeamEdge).filter(AgentTeamEdge.team_id == team.id).delete()
    db.query(AgentTeamNode).filter(AgentTeamNode.team_id == team.id).delete()

    # 创建新节点
    node_id_map = {}  # 前端node_id -> 数据库node_id
    for node_data in request.nodes:
        node = AgentTeamNode(
            id=uuid.uuid4(),
            team_id=team.id,
            agent_id=uuid.UUID(node_data.agent_id),
            position_x=node_data.position.get("x", 0),
            position_y=node_data.position.get("y", 0),
            role_in_team=node_data.config.role_in_team,
            responsibilities=node_data.config.responsibilities,
            allowed_tools=node_data.config.allowed_tools,
            can_call_agents=node_data.config.can_call_agents
        )
        db.add(node)
        node_id_map[node_data.node_id or str(node.id)] = str(node.id)

    # 创建新连线
    for edge_data in request.edges:
        source_id = node_id_map.get(edge_data.source_node_id, edge_data.source_node_id)
        target_id = node_id_map.get(edge_data.target_node_id, edge_data.target_node_id)

        edge = AgentTeamEdge(
            id=uuid.uuid4(),
            team_id=team.id,
            source_node_id=uuid.UUID(source_id),
            target_node_id=uuid.UUID(target_id),
            condition_type=edge_data.condition.type if edge_data.condition else "always",
            condition_value=edge_data.condition.value if edge_data.condition else None
        )
        db.add(edge)

    # 如果没有设置入口Agent，使用第一个节点
    if not team.entry_agent_id and request.nodes:
        first_node = db.query(AgentTeamNode).filter(
            AgentTeamNode.team_id == team.id
        ).first()
        if first_node:
            team.entry_agent_id = first_node.agent_id

    db.commit()

    return {
        "success": True,
        "message": "Canvas saved successfully",
        "data": {
            "node_count": len(request.nodes),
            "edge_count": len(request.edges)
        }
    }


@router.get("/{team_id}/canvas", response_model=dict)
async def get_canvas(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取画布配置
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查
    if team.creator_id != current_user.id and not team.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this team")

    # 获取节点
    nodes = db.query(AgentTeamNode).filter(
        AgentTeamNode.team_id == team.id
    ).all()

    # 获取连线
    edges = db.query(AgentTeamEdge).filter(
        AgentTeamEdge.team_id == team.id
    ).all()

    # 构建响应
    node_responses = []
    for node in nodes:
        agent = db.query(Agent).filter(Agent.id == node.agent_id).first()
        node_responses.append({
            "node_id": str(node.id),
            "agent_id": str(node.agent_id),
            "agent_name": agent.name if agent else None,
            "position": {"x": node.position_x, "y": node.position_y},
            "config": {
                "role_in_team": node.role_in_team,
                "responsibilities": node.responsibilities,
                "allowed_tools": node.allowed_tools or [],
                "can_call_agents": node.can_call_agents or []
            }
        })

    edge_responses = []
    for edge in edges:
        edge_responses.append({
            "edge_id": str(edge.id),
            "source_node_id": str(edge.source_node_id),
            "target_node_id": str(edge.target_node_id),
            "condition": {
                "type": edge.condition_type or "always",
                "value": edge.condition_value
            } if edge.condition_type else None
        })

    return {
        "success": True,
        "data": {
            "team_id": str(team.id),
            "nodes": node_responses,
            "edges": edge_responses
        }
    }


# ==================== 团队运行 ====================

@router.post("/{team_id}/run")
async def run_team(
    team_id: str,
    request: RunTeamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    运行团队任务（SSE流式响应）
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查
    if team.creator_id != current_user.id and not team.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this team")

    # 获取团队服务
    service = AgentTeamService(db)

    # 返回SSE流式响应
    return StreamingResponse(
        service.run_team_stream(team, request.message, request.session_id, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{team_id}/sessions", response_model=dict)
async def list_team_sessions(
    team_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取团队对话历史
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查
    if team.creator_id != current_user.id and not team.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this team")

    query = db.query(AgentTeamSession).filter(
        AgentTeamSession.team_id == team.id
    )

    total = query.count()
    sessions = query.order_by(
        AgentTeamSession.updated_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": {
            "items": [{
                "session_id": str(s.id),
                "team_id": str(s.team_id),
                "status": s.status,
                "messages": s.messages or [],
                "task_status": s.task_status or {},
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            } for s in sessions],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


# ==================== 导入导出 ====================

@router.post("/import", response_model=dict)
async def import_team(
    file: bytes,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导入团队配置（JSON格式）
    """
    try:
        config = json.loads(file.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    # 验证必要字段
    if "name" not in config or "goal" not in config:
        raise HTTPException(status_code=400, detail="Missing required fields: name, goal")

    # 创建团队
    team = AgentTeam(
        id=uuid.uuid4(),
        name=config["name"],
        description=config.get("description"),
        goal=config["goal"],
        max_rounds=config.get("max_rounds", 20),
        timeout_minutes=config.get("timeout_minutes", 10),
        global_prompt=config.get("global_prompt"),
        communication_mode=config.get("communication_mode", "broadcast"),
        decision_mode=config.get("decision_mode", "leader"),
        creator_id=current_user.id,
        is_public=False,
        is_active=True
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    # 导入节点
    if "nodes" in config:
        for node_data in config["nodes"]:
            # 验证Agent是否存在
            agent = db.query(Agent).filter(
                Agent.id == uuid.UUID(node_data["agent_id"])
            ).first()
            if not agent:
                continue

            node = AgentTeamNode(
                id=uuid.uuid4(),
                team_id=team.id,
                agent_id=agent.id,
                position_x=node_data.get("position", {}).get("x", 0),
                position_y=node_data.get("position", {}).get("y", 0),
                role_in_team=node_data.get("role_in_team"),
                responsibilities=node_data.get("responsibilities"),
                allowed_tools=node_data.get("allowed_tools", []),
                can_call_agents=node_data.get("can_call_agents", [])
            )
            db.add(node)

        db.commit()

    return {
        "success": True,
        "data": {
            "team_id": str(team.id),
            "name": team.name,
            "message": "Team imported successfully"
        }
    }


@router.get("/{team_id}/export")
async def export_team(
    team_id: str,
    format: str = Query("json", regex="^(json|python)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出团队配置为JSON或Agno兼容Python代码
    """
    team = db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 权限检查
    if team.creator_id != current_user.id and not team.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this team")

    # 获取节点和连线
    nodes = db.query(AgentTeamNode).filter(AgentTeamNode.team_id == team.id).all()
    edges = db.query(AgentTeamEdge).filter(AgentTeamEdge.team_id == team.id).all()

    if format == "json":
        # JSON格式导出
        config = {
            "name": team.name,
            "description": team.description,
            "goal": team.goal,
            "max_rounds": team.max_rounds,
            "timeout_minutes": team.timeout_minutes,
            "global_prompt": team.global_prompt,
            "communication_mode": team.communication_mode.value,
            "decision_mode": team.decision_mode.value,
            "nodes": [{
                "node_id": str(n.id),
                "agent_id": str(n.agent_id),
                "position": {"x": n.position_x, "y": n.position_y},
                "role_in_team": n.role_in_team,
                "responsibilities": n.responsibilities,
                "allowed_tools": n.allowed_tools or [],
                "can_call_agents": n.can_call_agents or []
            } for n in nodes],
            "edges": [{
                "edge_id": str(e.id),
                "source_node_id": str(e.source_node_id),
                "target_node_id": str(e.target_node_id),
                "condition": {
                    "type": e.condition_type,
                    "value": e.condition_value
                } if e.condition_type else None
            } for e in edges]
        }

        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=config,
            headers={
                "Content-Disposition": f"attachment; filename={team.name}_config.json"
            }
        )
    else:
        # Python代码导出（Agno兼容格式）
        from agent.services.agent_team_export import export_team_as_python
        code = export_team_as_python(team, nodes, edges, db)

        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=code,
            media_type="text/x-python",
            headers={
                "Content-Disposition": f"attachment; filename={team.name}_team.py"
            }
        )
