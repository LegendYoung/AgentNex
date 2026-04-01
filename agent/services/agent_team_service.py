"""
Agent Team 运行服务
P1阶段：多智能体团队协作运行时
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, List, Any
from sqlalchemy.orm import Session

from ..models_db import (
    Agent, AgentTeam, AgentTeamNode, AgentTeamEdge, AgentTeamSession,
    User, CommunicationMode, DecisionMode
)


class AgentTeamService:
    """Agent团队运行服务"""

    def __init__(self, db: Session):
        self.db = db

    async def run_team_stream(
        self,
        team: AgentTeam,
        message: str,
        session_id: Optional[str],
        user: User
    ) -> AsyncGenerator[str, None]:
        """
        运行团队任务（SSE流式响应）

        生成SSE事件格式：
        data: {"type": "agent_message", "agent_id": "...", "content": "..."}
        """
        # 获取或创建会话
        session = None
        if session_id:
            session = self.db.query(AgentTeamSession).filter(
                AgentTeamSession.id == uuid.UUID(session_id)
            ).first()

        if not session:
            session = AgentTeamSession(
                id=uuid.uuid4(),
                team_id=team.id,
                user_id=user.id,
                status="active",
                messages=[],
                task_status={}
            )
            self.db.add(session)
            self.db.commit()

        # 获取团队节点
        nodes = self.db.query(AgentTeamNode).filter(
            AgentTeamNode.team_id == team.id
        ).all()

        if not nodes:
            yield f"data: {json.dumps({'type': 'error', 'error': 'No agents configured in this team'})}\n\n"
            return

        # 获取节点间的连线关系
        edges = self.db.query(AgentTeamEdge).filter(
            AgentTeamEdge.team_id == team.id
        ).all()

        # 构建节点映射
        node_map = {str(node.id): node for node in nodes}
        agent_ids = [node.agent_id for node in nodes]
        agents = self.db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
        agent_map = {str(agent.id): agent for agent in agents}

        # 添加用户消息到会话
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages = session.messages or []
        session.messages.append(user_message)
        self.db.commit()

        # 发送开始事件
        yield f"data: {json.dumps({'type': 'start', 'team_id': str(team.id), 'session_id': str(session.id)})}\n\n"

        try:
            # 确定入口Agent
            entry_node = None
            if team.entry_agent_id:
                for node in nodes:
                    if str(node.agent_id) == str(team.entry_agent_id):
                        entry_node = node
                        break

            if not entry_node:
                entry_node = nodes[0]

            # 运行团队协作流程
            current_node = entry_node
            round_count = 0
            visited_nodes = set()

            while round_count < team.max_rounds:
                node_id = str(current_node.id)
                if node_id in visited_nodes and team.communication_mode != CommunicationMode.BROADCAST:
                    # 避免循环（广播模式除外）
                    break
                visited_nodes.add(node_id)

                agent = agent_map.get(str(current_node.agent_id))
                if not agent:
                    yield f"data: {json.dumps({'type': 'error', 'error': f'Agent not found: {current_node.agent_id}'})}\n\n"
                    break

                # 发送Agent开始事件
                yield f"data: {json.dumps({'type': 'agent_start', 'agent_id': str(agent.id), 'agent_name': agent.name})}\n\n"

                # 调用Agent获取响应
                try:
                    response = await self._call_agent(agent, message, session)
                    
                    # 发送Agent消息事件
                    yield f"data: {json.dumps({'type': 'agent_message', 'agent_id': str(agent.id), 'agent_name': agent.name, 'content': response})}\n\n"

                    # 记录消息
                    agent_message = {
                        "role": "assistant",
                        "agent_id": str(agent.id),
                        "agent_name": agent.name,
                        "content": response,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    session.messages.append(agent_message)
                    self.db.commit()

                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'agent_id': str(agent.id), 'error': str(e)})}\n\n"
                    break

                # 检查是否需要转移
                next_node = self._get_next_node(current_node, edges, node_map, response)

                if not next_node:
                    # 任务完成
                    break

                # 发送转移事件
                yield f"data: {json.dumps({'type': 'agent_transfer', 'from': str(current_node.agent_id), 'to': str(next_node.agent_id)})}\n\n"

                current_node = next_node
                round_count += 1

            # 会话完成
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            self.db.commit()

            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete', 'session_id': str(session.id), 'result': 'Task completed'})}\n\n"

        except Exception as e:
            session.status = "failed"
            self.db.commit()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    async def _call_agent(
        self,
        agent: Agent,
        message: str,
        session: AgentTeamSession
    ) -> str:
        """
        调用单个Agent获取响应

        TODO: 集成Agno Runtime
        目前返回模拟响应
        """
        # 构建上下文
        context = ""
        if session.messages:
            recent_messages = session.messages[-10:]  # 最近10条消息
            for msg in recent_messages:
                if msg["role"] == "user":
                    context += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    agent_name = msg.get("agent_name", "Assistant")
                    context += f"{agent_name}: {msg['content']}\n"

        # 这里应该调用Agno Runtime
        # 目前返回模拟响应
        await asyncio.sleep(0.5)  # 模拟处理延迟

        # 基于Agent角色返回不同的模拟响应
        if agent.name:
            return f"[{agent.name}] 我已收到任务：{message[:50]}... 正在处理中..."

        return f"Agent响应: {message[:100]}..."

    def _get_next_node(
        self,
        current_node: AgentTeamNode,
        edges: List[AgentTeamEdge],
        node_map: Dict[str, AgentTeamNode],
        response: str
    ) -> Optional[AgentTeamNode]:
        """
        根据连线和条件获取下一个节点
        """
        # 查找从当前节点出发的连线
        outgoing_edges = [
            e for e in edges
            if str(e.source_node_id) == str(current_node.id)
        ]

        if not outgoing_edges:
            return None

        # 如果有多条连线，检查条件
        for edge in outgoing_edges:
            if edge.condition_type == "always" or not edge.condition_type:
                next_node = node_map.get(str(edge.target_node_id))
                if next_node:
                    return next_node

            # TODO: 实现条件表达式解析
            # if edge.condition_type == "expression":
            #     if self._evaluate_condition(edge.condition_value, response):
            #         return node_map.get(str(edge.target_node_id))

        # 默认返回第一条连线指向的节点
        if outgoing_edges:
            return node_map.get(str(outgoing_edges[0].target_node_id))

        return None

    def _evaluate_condition(self, condition: str, response: str) -> bool:
        """
        评估条件表达式

        TODO: 实现安全的表达式解析
        """
        # 简单的条件匹配
        if "approved" in condition.lower():
            return "approve" in response.lower() or "同意" in response
        if "rejected" in condition.lower():
            return "reject" in response.lower() or "拒绝" in response
        return True
