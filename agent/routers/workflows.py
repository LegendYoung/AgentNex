"""
Workflow API 路由
P2阶段：工作流引擎管理
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
    User, Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowExecutionLog,
    WorkflowTriggerType, WorkflowNodeType, WorkflowStatus, ExecutionStatus
)
from agent.models_workflow import (
    CreateWorkflowRequest, UpdateWorkflowRequest, SaveWorkflowCanvasRequest,
    RunWorkflowRequest, ContinueWorkflowRequest, WorkflowResponse, WorkflowDetailResponse,
    WorkflowListResponse, WorkflowExecutionResponse, WorkflowExecutionDetailResponse,
    WorkflowExecutionListResponse, WorkflowRunEvent, CanvasWorkflowNode, CanvasWorkflowEdge,
    WorkflowVariable
)
from agent.utils.auth import get_current_user, require_role
from agent.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])


# ==================== 工作流 CRUD ====================

@router.post("", response_model=dict)
async def create_workflow(
    request: CreateWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建工作流
    
    - **name**: 工作流名称（2-100字符）
    - **description**: 工作流描述
    - **trigger_type**: 触发类型（manual/api/schedule/webhook/event）
    - **trigger_config**: 触发配置
    - **variables**: 工作流变量定义
    """
    # 创建工作流
    workflow = Workflow(
        id=uuid.uuid4(),
        name=request.name,
        description=request.description,
        trigger_type=request.trigger_type.value,
        trigger_config=request.trigger_config or {},
        variables=[v.model_dump() for v in request.variables] if request.variables else [],
        is_public=request.is_public,
        creator_id=current_user.id
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    # 创建默认的开始和结束节点
    start_node = WorkflowNode(
        id=uuid.uuid4(),
        workflow_id=workflow.id,
        node_type=WorkflowNodeType.START.value,
        label="开始",
        position_x=100,
        position_y=200
    )
    end_node = WorkflowNode(
        id=uuid.uuid4(),
        workflow_id=workflow.id,
        node_type=WorkflowNodeType.END.value,
        label="结束",
        position_x=600,
        position_y=200
    )
    db.add_all([start_node, end_node])
    db.commit()
    
    return {
        "success": True,
        "data": {
            "workflow_id": str(workflow.id),
            "name": workflow.name,
            "created_at": workflow.created_at.isoformat()
        }
    }


@router.get("", response_model=dict)
async def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(draft|active|archived)$"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作流列表
    
    - **status**: 按状态筛选（draft/active/archived）
    - **search**: 搜索关键词
    """
    query = db.query(Workflow)
    
    # 权限过滤：自己的或公开的
    query = query.filter(
        or_(
            Workflow.creator_id == current_user.id,
            Workflow.is_public == True
        )
    )
    
    # 状态筛选
    if status:
        query = query.filter(Workflow.status == status)
    
    # 搜索
    if search:
        query = query.filter(
            or_(
                Workflow.name.ilike(f"%{search}%"),
                Workflow.description.ilike(f"%{search}%")
            )
        )
    
    # 统计
    total = query.count()
    
    # 分页
    workflows = query.order_by(Workflow.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 构建响应
    items = []
    for wf in workflows:
        items.append({
            "workflow_id": str(wf.id),
            "name": wf.name,
            "description": wf.description,
            "trigger_type": wf.trigger_type,
            "trigger_config": wf.trigger_config or {},
            "variables": wf.variables or [],
            "status": wf.status,
            "is_public": wf.is_public,
            "version": wf.version,
            "execution_count": wf.execution_count,
            "last_execution_at": wf.last_execution_at.isoformat() if wf.last_execution_at else None,
            "creator": {
                "user_id": str(wf.creator.id),
                "name": wf.creator.name,
                "email": wf.creator.email
            } if wf.creator else None,
            "created_at": wf.created_at.isoformat(),
            "updated_at": wf.updated_at.isoformat()
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


@router.get("/{workflow_id}", response_model=dict)
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作流详情（含节点和连线）
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 权限检查
    if workflow.creator_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this workflow")
    
    # 获取节点
    nodes = db.query(WorkflowNode).filter(
        WorkflowNode.workflow_id == workflow.id
    ).all()
    
    # 获取连线
    edges = db.query(WorkflowEdge).filter(
        WorkflowEdge.workflow_id == workflow.id
    ).all()
    
    # 构建响应
    node_responses = [{
        "node_id": str(n.id),
        "node_type": n.node_type,
        "label": n.label,
        "description": n.description,
        "position": {"x": n.position_x, "y": n.position_y},
        "config": n.config or {},
        "created_at": n.created_at.isoformat()
    } for n in nodes]
    
    edge_responses = [{
        "edge_id": str(e.id),
        "source_node_id": str(e.source_node_id),
        "target_node_id": str(e.target_node_id),
        "label": e.label,
        "condition_type": e.condition_type,
        "condition_value": e.condition_value
    } for e in edges]
    
    return {
        "success": True,
        "data": {
            "workflow_id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "trigger_type": workflow.trigger_type,
            "trigger_config": workflow.trigger_config or {},
            "variables": workflow.variables or [],
            "status": workflow.status,
            "is_public": workflow.is_public,
            "version": workflow.version,
            "execution_count": workflow.execution_count,
            "last_execution_at": workflow.last_execution_at.isoformat() if workflow.last_execution_at else None,
            "creator": {
                "user_id": str(workflow.creator.id),
                "name": workflow.creator.name,
                "email": workflow.creator.email
            } if workflow.creator else None,
            "nodes": node_responses,
            "edges": edge_responses,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat()
        }
    }


@router.put("/{workflow_id}", response_model=dict)
async def update_workflow(
    workflow_id: str,
    request: UpdateWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新工作流配置
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 权限检查：仅创建者可修改
    if workflow.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to modify this workflow")
    
    # 更新字段
    if request.name is not None:
        workflow.name = request.name
    if request.description is not None:
        workflow.description = request.description
    if request.trigger_type is not None:
        workflow.trigger_type = request.trigger_type.value
    if request.trigger_config is not None:
        workflow.trigger_config = request.trigger_config
    if request.variables is not None:
        workflow.variables = [v.model_dump() for v in request.variables]
    if request.status is not None:
        workflow.status = request.status.value
    if request.is_public is not None:
        workflow.is_public = request.is_public
    
    db.commit()
    db.refresh(workflow)
    
    return {
        "success": True,
        "data": {
            "workflow_id": str(workflow.id),
            "name": workflow.name,
            "updated_at": workflow.updated_at.isoformat()
        }
    }


@router.delete("/{workflow_id}", response_model=dict)
async def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除工作流
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 权限检查：仅创建者可删除
    if workflow.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to delete this workflow")
    
    db.delete(workflow)
    db.commit()
    
    return {"success": True, "message": "Workflow deleted successfully"}


# ==================== 画布配置管理 ====================

@router.post("/{workflow_id}/canvas", response_model=dict)
async def save_canvas(
    workflow_id: str,
    request: SaveWorkflowCanvasRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    保存工作流画布配置（节点+连线）
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 权限检查
    if workflow.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to modify this workflow")
    
    # 删除现有节点和连线
    db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow.id).delete()
    db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow.id).delete()
    
    # 创建新节点
    node_id_map = {}  # 前端node_id -> 数据库node_id
    for node_data in request.nodes:
        node = WorkflowNode(
            id=uuid.uuid4(),
            workflow_id=workflow.id,
            node_type=node_data.node_type.value if isinstance(node_data.node_type, str) else node_data.node_type.value,
            label=node_data.label,
            description=node_data.description,
            position_x=node_data.position.get("x", 0),
            position_y=node_data.position.get("y", 0),
            config=node_data.config
        )
        db.add(node)
        db.flush()  # 获取生成的 ID
        node_id_map[node_data.node_id or str(node.id)] = str(node.id)
    
    # 创建新连线
    for edge_data in request.edges:
        source_id = node_id_map.get(edge_data.source_node_id, edge_data.source_node_id)
        target_id = node_id_map.get(edge_data.target_node_id, edge_data.target_node_id)
        
        edge = WorkflowEdge(
            id=uuid.uuid4(),
            workflow_id=workflow.id,
            source_node_id=uuid.UUID(source_id),
            target_node_id=uuid.UUID(target_id),
            label=edge_data.label,
            condition_type=edge_data.condition_type,
            condition_value=edge_data.condition_value
        )
        db.add(edge)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Canvas saved successfully",
        "data": {
            "node_count": len(request.nodes),
            "edge_count": len(request.edges)
        }
    }


@router.get("/{workflow_id}/canvas", response_model=dict)
async def get_canvas(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作流画布配置
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 权限检查
    if workflow.creator_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this workflow")
    
    # 获取节点
    nodes = db.query(WorkflowNode).filter(
        WorkflowNode.workflow_id == workflow.id
    ).all()
    
    # 获取连线
    edges = db.query(WorkflowEdge).filter(
        WorkflowEdge.workflow_id == workflow.id
    ).all()
    
    # 构建响应
    node_responses = [{
        "node_id": str(n.id),
        "node_type": n.node_type,
        "label": n.label,
        "description": n.description,
        "position": {"x": n.position_x, "y": n.position_y},
        "config": n.config or {}
    } for n in nodes]
    
    edge_responses = [{
        "edge_id": str(e.id),
        "source_node_id": str(e.source_node_id),
        "target_node_id": str(e.target_node_id),
        "label": e.label,
        "condition_type": e.condition_type,
        "condition_value": e.condition_value
    } for e in edges]
    
    return {
        "success": True,
        "data": {
            "workflow_id": str(workflow.id),
            "nodes": node_responses,
            "edges": edge_responses
        }
    }


# ==================== 工作流执行 ====================

@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    request: RunWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行工作流（SSE流式响应）
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 权限检查
    if workflow.creator_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this workflow")
    
    # 检查工作流状态
    if workflow.status != WorkflowStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Workflow is not active")
    
    # 获取工作流服务
    service = WorkflowService(db)
    
    # 返回SSE流式响应
    return StreamingResponse(
        service.run_workflow_stream(workflow, request.input_data, request.variables, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/continue", response_model=dict)
async def continue_workflow(
    request: ContinueWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    继续执行工作流（提供人工输入）
    """
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == uuid.UUID(request.execution_id)
    ).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # 权限检查
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to access this execution")
    
    # 检查执行状态
    if execution.status != ExecutionStatus.PAUSED.value:
        raise HTTPException(status_code=400, detail="Execution is not waiting for input")
    
    # 获取工作流服务并继续执行
    service = WorkflowService(db)
    return await service.continue_execution(execution, request.node_id, request.input_value)


@router.get("/{workflow_id}/executions", response_model=dict)
async def list_workflow_executions(
    workflow_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作流执行历史
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 权限检查
    if workflow.creator_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this workflow")
    
    query = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow.id
    )
    
    # 状态筛选
    if status:
        query = query.filter(WorkflowExecution.status == status)
    
    total = query.count()
    executions = query.order_by(
        WorkflowExecution.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "success": True,
        "data": {
            "items": [{
                "execution_id": str(e.id),
                "workflow_id": str(e.workflow_id),
                "status": e.status,
                "current_node_id": str(e.current_node_id) if e.current_node_id else None,
                "input_data": e.input_data or {},
                "output_data": e.output_data or {},
                "variables": e.variables or {},
                "error_message": e.error_message,
                "error_node_id": str(e.error_node_id) if e.error_node_id else None,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "created_at": e.created_at.isoformat()
            } for e in executions],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/executions/{execution_id}", response_model=dict)
async def get_execution_detail(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取执行详情（含日志）
    """
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == uuid.UUID(execution_id)
    ).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # 权限检查
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to access this execution")
    
    # 获取日志
    logs = db.query(WorkflowExecutionLog).filter(
        WorkflowExecutionLog.execution_id == execution.id
    ).order_by(WorkflowExecutionLog.timestamp).all()
    
    return {
        "success": True,
        "data": {
            "execution_id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "status": execution.status,
            "current_node_id": str(execution.current_node_id) if execution.current_node_id else None,
            "input_data": execution.input_data or {},
            "output_data": execution.output_data or {},
            "variables": execution.variables or {},
            "error_message": execution.error_message,
            "error_node_id": str(execution.error_node_id) if execution.error_node_id else None,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "created_at": execution.created_at.isoformat(),
            "logs": [{
                "log_id": str(l.id),
                "node_id": str(l.node_id) if l.node_id else None,
                "node_type": l.node_type,
                "node_label": l.node_label,
                "event_type": l.event_type,
                "message": l.message,
                "input_data": l.input_data,
                "output_data": l.output_data,
                "error_message": l.error_message,
                "duration_ms": l.duration_ms,
                "timestamp": l.timestamp.isoformat()
            } for l in logs]
        }
    }


# ==================== 激活/停用工作流 ====================

@router.post("/{workflow_id}/activate", response_model=dict)
async def activate_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    激活工作流（使其可执行）
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to modify this workflow")
    
    # 验证工作流是否有开始和结束节点
    nodes = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow.id).all()
    has_start = any(n.node_type == WorkflowNodeType.START.value for n in nodes)
    has_end = any(n.node_type == WorkflowNodeType.END.value for n in nodes)
    
    if not has_start or not has_end:
        raise HTTPException(status_code=400, detail="Workflow must have start and end nodes")
    
    workflow.status = WorkflowStatus.ACTIVE.value
    db.commit()
    
    return {"success": True, "message": "Workflow activated successfully"}


@router.post("/{workflow_id}/deactivate", response_model=dict)
async def deactivate_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    停用工作流
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to modify this workflow")
    
    workflow.status = WorkflowStatus.DRAFT.value
    db.commit()
    
    return {"success": True, "message": "Workflow deactivated successfully"}


# ==================== 导入导出 ====================

@router.post("/import", response_model=dict)
async def import_workflow(
    file: bytes,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导入工作流配置（JSON格式）
    """
    try:
        config = json.loads(file.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    if "name" not in config:
        raise HTTPException(status_code=400, detail="Missing required field: name")
    
    # 创建工作流
    workflow = Workflow(
        id=uuid.uuid4(),
        name=config["name"],
        description=config.get("description"),
        trigger_type=config.get("trigger_type", "manual"),
        trigger_config=config.get("trigger_config", {}),
        variables=config.get("variables", []),
        creator_id=current_user.id,
        is_public=False
    )
    
    db.add(workflow)
    db.flush()
    
    # 导入节点
    node_id_map = {}
    if "nodes" in config:
        for node_data in config["nodes"]:
            node = WorkflowNode(
                id=uuid.uuid4(),
                workflow_id=workflow.id,
                node_type=node_data.get("node_type", "agent"),
                label=node_data.get("label"),
                description=node_data.get("description"),
                position_x=node_data.get("position", {}).get("x", 0),
                position_y=node_data.get("position", {}).get("y", 0),
                config=node_data.get("config", {})
            )
            db.add(node)
            db.flush()
            node_id_map[node_data.get("node_id", str(node.id))] = str(node.id)
    
    # 导入连线
    if "edges" in config:
        for edge_data in config["edges"]:
            source_id = node_id_map.get(edge_data.get("source_node_id"), edge_data.get("source_node_id"))
            target_id = node_id_map.get(edge_data.get("target_node_id"), edge_data.get("target_node_id"))
            
            if source_id and target_id:
                edge = WorkflowEdge(
                    id=uuid.uuid4(),
                    workflow_id=workflow.id,
                    source_node_id=uuid.UUID(source_id),
                    target_node_id=uuid.UUID(target_id),
                    label=edge_data.get("label"),
                    condition_type=edge_data.get("condition_type"),
                    condition_value=edge_data.get("condition_value")
                )
                db.add(edge)
    
    db.commit()
    
    return {
        "success": True,
        "data": {
            "workflow_id": str(workflow.id),
            "name": workflow.name,
            "message": "Workflow imported successfully"
        }
    }


@router.get("/{workflow_id}/export")
async def export_workflow(
    workflow_id: str,
    format: str = Query("json", regex="^(json|python)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出工作流配置
    """
    workflow = db.query(Workflow).filter(Workflow.id == uuid.UUID(workflow_id)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.creator_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="No permission to access this workflow")
    
    nodes = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow.id).all()
    edges = db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow.id).all()
    
    if format == "json":
        config = {
            "name": workflow.name,
            "description": workflow.description,
            "trigger_type": workflow.trigger_type,
            "trigger_config": workflow.trigger_config,
            "variables": workflow.variables,
            "nodes": [{
                "node_id": str(n.id),
                "node_type": n.node_type,
                "label": n.label,
                "description": n.description,
                "position": {"x": n.position_x, "y": n.position_y},
                "config": n.config
            } for n in nodes],
            "edges": [{
                "edge_id": str(e.id),
                "source_node_id": str(e.source_node_id),
                "target_node_id": str(e.target_node_id),
                "label": e.label,
                "condition_type": e.condition_type,
                "condition_value": e.condition_value
            } for e in edges]
        }
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=config,
            headers={
                "Content-Disposition": f"attachment; filename={workflow.name}_workflow.json"
            }
        )
    else:
        # Python 代码导出
        from agent.services.workflow_export import export_workflow_as_python
        code = export_workflow_as_python(workflow, nodes, edges, db)
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=code,
            media_type="text/x-python",
            headers={
                "Content-Disposition": f"attachment; filename={workflow.name}_workflow.py"
            }
        )
