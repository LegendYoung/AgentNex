"""
Workflow 执行服务
P2阶段：工作流引擎核心执行逻辑
"""

import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid

from agent.models_db import (
    Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, WorkflowExecutionLog,
    WorkflowNodeType, ExecutionStatus, Agent, AgentTeam
)
from agent.models_workflow import WorkflowRunEvent


class WorkflowService:
    """工作流执行服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def run_workflow_stream(
        self,
        workflow: Workflow,
        input_data: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        user = None
    ) -> AsyncGenerator[str, None]:
        """
        执行工作流并返回 SSE 流
        
        Yields:
            SSE 格式的事件字符串
        """
        # 创建执行实例
        execution = WorkflowExecution(
            id=uuid.uuid4(),
            workflow_id=workflow.id,
            user_id=user.id if user else None,
            status=ExecutionStatus.RUNNING.value,
            input_data=input_data or {},
            variables={**(variables or {}), **{v['name']: v.get('default_value') for v in (workflow.variables or []) if v.get('default_value') is not None}},
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        
        # 更新工作流统计
        workflow.execution_count += 1
        workflow.last_execution_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # 发送开始事件
            yield self._format_event("started", {
                "execution_id": str(execution.id),
                "message": f"开始执行工作流: {workflow.name}"
            })
            
            # 获取所有节点和连线
            nodes = self.db.query(WorkflowNode).filter(
                WorkflowNode.workflow_id == workflow.id
            ).all()
            edges = self.db.query(WorkflowEdge).filter(
                WorkflowEdge.workflow_id == workflow.id
            ).all()
            
            # 构建节点映射
            node_map = {str(n.id): n for n in nodes}
            
            # 构建边映射：source_node_id -> [(target_node_id, condition)]
            edge_map = {}
            for edge in edges:
                source_id = str(edge.source_node_id)
                if source_id not in edge_map:
                    edge_map[source_id] = []
                edge_map[source_id].append({
                    "target_node_id": str(edge.target_node_id),
                    "condition_type": edge.condition_type,
                    "condition_value": edge.condition_value
                })
            
            # 找到开始节点
            start_node = next((n for n in nodes if n.node_type == WorkflowNodeType.START.value), None)
            if not start_node:
                yield self._format_event("error", {
                    "execution_id": str(execution.id),
                    "error": "No start node found"
                })
                return
            
            # 从开始节点执行
            current_node_id = str(start_node.id)
            visited_nodes = set()
            
            while current_node_id and current_node_id not in visited_nodes:
                visited_nodes.add(current_node_id)
                current_node = node_map.get(current_node_id)
                
                if not current_node:
                    break
                
                # 更新当前执行节点
                execution.current_node_id = current_node.id
                self.db.commit()
                
                # 记录节点开始日志
                log_start = WorkflowExecutionLog(
                    id=uuid.uuid4(),
                    execution_id=execution.id,
                    node_id=current_node.id,
                    node_type=current_node.node_type,
                    node_label=current_node.label,
                    event_type="started",
                    timestamp=datetime.utcnow()
                )
                self.db.add(log_start)
                self.db.commit()
                
                # 发送节点开始事件
                yield self._format_event("node_started", {
                    "execution_id": str(execution.id),
                    "node_id": current_node_id,
                    "node_type": current_node.node_type,
                    "node_label": current_node.label,
                    "message": f"开始执行节点: {current_node.label or current_node.node_type}"
                })
                
                # 执行节点
                node_output = None
                error = None
                start_time = datetime.utcnow()
                
                try:
                    node_output = await self._execute_node(current_node, execution, input_data)
                except Exception as e:
                    error = str(e)
                
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # 记录节点完成日志
                log_end = WorkflowExecutionLog(
                    id=uuid.uuid4(),
                    execution_id=execution.id,
                    node_id=current_node.id,
                    node_type=current_node.node_type,
                    node_label=current_node.label,
                    event_type="completed" if not error else "failed",
                    output_data=node_output,
                    error_message=error,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow()
                )
                self.db.add(log_end)
                self.db.commit()
                
                if error:
                    # 节点执行失败
                    execution.status = ExecutionStatus.FAILED.value
                    execution.error_message = error
                    execution.error_node_id = current_node.id
                    execution.completed_at = datetime.utcnow()
                    self.db.commit()
                    
                    yield self._format_event("node_failed", {
                        "execution_id": str(execution.id),
                        "node_id": current_node_id,
                        "node_type": current_node.node_type,
                        "node_label": current_node.label,
                        "error": error
                    })
                    
                    yield self._format_event("failed", {
                        "execution_id": str(execution.id),
                        "error": f"工作流执行失败: {error}"
                    })
                    return
                
                # 发送节点完成事件
                yield self._format_event("node_completed", {
                    "execution_id": str(execution.id),
                    "node_id": current_node_id,
                    "node_type": current_node.node_type,
                    "node_label": current_node.label,
                    "data": node_output,
                    "duration_ms": duration_ms
                })
                
                # 检查是否到达结束节点
                if current_node.node_type == WorkflowNodeType.END.value:
                    break
                
                # 检查是否需要人工输入
                if current_node.node_type == WorkflowNodeType.HUMAN_INPUT.value:
                    execution.status = ExecutionStatus.PAUSED.value
                    self.db.commit()
                    
                    yield self._format_event("waiting_input", {
                        "execution_id": str(execution.id),
                        "node_id": current_node_id,
                        "node_type": current_node.node_type,
                        "node_label": current_node.label,
                        "message": current_node.config.get("prompt", "请提供输入"),
                        "data": current_node.config
                    })
                    return
                
                # 获取下一个节点
                next_nodes = edge_map.get(current_node_id, [])
                if not next_nodes:
                    break
                
                # 简单实现：选择第一个满足条件的边
                next_node_id = None
                for edge_info in next_nodes:
                    condition_type = edge_info.get("condition_type")
                    condition_value = edge_info.get("condition_value")
                    
                    if condition_type == "always" or not condition_type:
                        next_node_id = edge_info["target_node_id"]
                        break
                    elif condition_type == "expression":
                        # TODO: 实现表达式求值
                        next_node_id = edge_info["target_node_id"]
                        break
                    elif condition_type == "output_match":
                        # TODO: 实现输出匹配
                        next_node_id = edge_info["target_node_id"]
                        break
                
                current_node_id = next_node_id
            
            # 工作流执行完成
            execution.status = ExecutionStatus.COMPLETED.value
            execution.output_data = node_output or {}
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            
            yield self._format_event("completed", {
                "execution_id": str(execution.id),
                "message": "工作流执行完成",
                "data": execution.output_data
            })
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED.value
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            
            yield self._format_event("failed", {
                "execution_id": str(execution.id),
                "error": str(e)
            })
    
    async def _execute_node(
        self,
        node: WorkflowNode,
        execution: WorkflowExecution,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        执行单个节点
        
        Args:
            node: 工作流节点
            execution: 执行实例
            input_data: 输入数据
            
        Returns:
            节点输出数据
        """
        config = node.config or {}
        
        if node.node_type == WorkflowNodeType.START.value:
            return input_data or {}
        
        elif node.node_type == WorkflowNodeType.END.value:
            return {"status": "completed"}
        
        elif node.node_type == WorkflowNodeType.AGENT.value:
            return await self._execute_agent_node(config, execution, input_data)
        
        elif node.node_type == WorkflowNodeType.TEAM.value:
            return await self._execute_team_node(config, execution, input_data)
        
        elif node.node_type == WorkflowNodeType.CONDITION.value:
            # 条件节点：返回分支信息
            return {"branches": config.get("branches", [])}
        
        elif node.node_type == WorkflowNodeType.LOOP.value:
            # 循环节点：简化实现
            return {"iterations": 0}
        
        elif node.node_type == WorkflowNodeType.PARALLEL.value:
            # 并行节点：简化实现
            return {"branches_completed": []}
        
        elif node.node_type == WorkflowNodeType.HUMAN_INPUT.value:
            # 人工输入节点：在主流程中处理
            return {"waiting_for_input": True}
        
        elif node.node_type == WorkflowNodeType.CODE.value:
            return await self._execute_code_node(config, execution, input_data)
        
        elif node.node_type == WorkflowNodeType.API_CALL.value:
            return await self._execute_api_call_node(config, execution, input_data)
        
        elif node.node_type == WorkflowNodeType.DELAY.value:
            delay_seconds = config.get("delay_seconds", 1)
            await asyncio.sleep(delay_seconds)
            return {"delayed": delay_seconds}
        
        return {}
    
    async def _execute_agent_node(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行 Agent 节点"""
        agent_id = config.get("agent_id")
        if not agent_id:
            raise ValueError("Agent node missing agent_id")
        
        agent = self.db.query(Agent).filter(Agent.id == uuid.UUID(agent_id)).first()
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # TODO: 实际调用 Agent 执行
        # 这里简化实现，返回模拟结果
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": "completed",
            "output": f"Agent {agent.name} executed successfully"
        }
    
    async def _execute_team_node(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行 Agent Team 节点"""
        team_id = config.get("team_id")
        if not team_id:
            raise ValueError("Team node missing team_id")
        
        team = self.db.query(AgentTeam).filter(AgentTeam.id == uuid.UUID(team_id)).first()
        if not team:
            raise ValueError(f"Team not found: {team_id}")
        
        # TODO: 实际调用 Team 执行
        return {
            "team_id": team_id,
            "team_name": team.name,
            "status": "completed",
            "output": f"Team {team.name} executed successfully"
        }
    
    async def _execute_code_node(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行代码节点"""
        language = config.get("language", "python")
        code = config.get("code", "")
        
        if language == "python":
            # 安全执行 Python 代码（受限环境）
            try:
                local_vars = {"input": input_data, "output": None}
                exec(code, {"__builtins__": {}}, local_vars)
                return {"result": local_vars.get("output")}
            except Exception as e:
                raise ValueError(f"Code execution failed: {str(e)}")
        
        return {"status": "unsupported_language"}
    
    async def _execute_api_call_node(
        self,
        config: Dict[str, Any],
        execution: WorkflowExecution,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行 API 调用节点"""
        import aiohttp
        
        url = config.get("url")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        body = config.get("body")
        timeout = config.get("timeout_seconds", 30)
        
        if not url:
            raise ValueError("API call node missing URL")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    json=body if body else None,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    result = await response.json() if response.content_type == "application/json" else await response.text()
                    return {
                        "status_code": response.status,
                        "result": result
                    }
        except Exception as e:
            raise ValueError(f"API call failed: {str(e)}")
    
    async def continue_execution(
        self,
        execution: WorkflowExecution,
        node_id: str,
        input_value: Any
    ) -> Dict[str, Any]:
        """
        继续执行工作流（提供人工输入后）
        """
        # 记录输入
        log = WorkflowExecutionLog(
            id=uuid.uuid4(),
            execution_id=execution.id,
            node_id=uuid.UUID(node_id),
            event_type="input_received",
            input_data={"input_value": input_value},
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        
        # 更新变量
        execution.variables["human_input"] = input_value
        execution.status = ExecutionStatus.RUNNING.value
        self.db.commit()
        
        return {
            "success": True,
            "message": "Input received, workflow continuing",
            "execution_id": str(execution.id)
        }
    
    def _format_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """格式化 SSE 事件"""
        event = WorkflowRunEvent(
            event_type=event_type,
            execution_id=data.get("execution_id", ""),
            node_id=data.get("node_id"),
            node_type=data.get("node_type"),
            node_label=data.get("node_label"),
            message=data.get("message"),
            data=data.get("data"),
            error=data.get("error")
        )
        
        return f"event: {event_type}\ndata: {event.model_dump_json()}\n\n"
