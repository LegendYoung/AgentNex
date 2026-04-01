"""
Workflow 导出服务
P2阶段：导出工作流配置为可执行 Python 代码
"""

from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from agent.models_db import Workflow, WorkflowNode, WorkflowEdge, WorkflowNodeType


def export_workflow_as_python(
    workflow: Workflow,
    nodes: List[WorkflowNode],
    edges: List[WorkflowEdge],
    db: Session
) -> str:
    """
    导出工作流为 Agno 兼容的 Python 代码
    
    Args:
        workflow: 工作流对象
        nodes: 节点列表
        edges: 连线列表
        db: 数据库会话
        
    Returns:
        Python 代码字符串
    """
    lines = [
        '"""',
        f'Workflow: {workflow.name}',
        f'Description: {workflow.description or "N/A"}',
        f'Exported at: {datetime.utcnow().isoformat()}',
        '"""',
        '',
        'from agno.workflow import Workflow, Step',
        'from agno.workflow.router import Router',
        'from agno.workflow.condition import Condition',
        'from agno.agent import Agent',
        '',
        '',
        f'class {workflow.name.replace(" ", "_").replace("-", "_")}Workflow:',
        f'    """工作流: {workflow.name}"""',
        '',
        '    def __init__(self):',
        '        self.workflow = Workflow(',
        f'            name="{workflow.name}",',
        f'            description="{workflow.description or ""}"',
        '        )',
        '        self._setup_steps()',
        '        self._setup_router()',
        '',
        '    def _setup_steps(self):',
        '        """设置工作流步骤"""',
    ]
    
    # 生成步骤代码
    for node in nodes:
        if node.node_type == WorkflowNodeType.START.value:
            continue
        elif node.node_type == WorkflowNodeType.END.value:
            continue
        elif node.node_type == WorkflowNodeType.AGENT.value:
            lines.extend(self._generate_agent_step(node))
        elif node.node_type == WorkflowNodeType.TEAM.value:
            lines.extend(self._generate_team_step(node))
        elif node.node_type == WorkflowNodeType.CONDITION.value:
            lines.extend(self._generate_condition_step(node))
        elif node.node_type == WorkflowNodeType.CODE.value:
            lines.extend(self._generate_code_step(node))
        elif node.node_type == WorkflowNodeType.DELAY.value:
            lines.extend(self._generate_delay_step(node))
    
    lines.extend([
        '',
        '    def _setup_router(self):',
        '        """设置工作流路由"""',
        '        # TODO: 根据边配置设置路由逻辑',
        '        pass',
        '',
        '    def run(self, input_data: dict = None):',
        '        """执行工作流"""',
        '        return self.workflow.run(input_data=input_data)',
        '',
        '',
        '# 使用示例',
        'if __name__ == "__main__":',
        f'    workflow = {workflow.name.replace(" ", "_").replace("-", "_")}Workflow()',
        '    result = workflow.run(input_data={"message": "Hello, Workflow!"})',
        '    print(result)',
        ''
    ])
    
    return '\n'.join(lines)


def _generate_agent_step(self, node: WorkflowNode) -> List[str]:
    """生成 Agent 步骤代码"""
    config = node.config or {}
    agent_id = config.get("agent_id", "")
    label = node.label or "agent_step"
    
    return [
        f'        # Agent 步骤: {label}',
        f'        self.{label} = Step(',
        f'            name="{label}",',
        f'            agent=Agent.get("{agent_id}"),  # 引用已创建的 Agent',
        '        )',
        ''
    ]


def _generate_team_step(self, node: WorkflowNode) -> List[str]:
    """生成 Team 步骤代码"""
    config = node.config or {}
    team_id = config.get("team_id", "")
    label = node.label or "team_step"
    
    return [
        f'        # Team 步骤: {label}',
        f'        self.{label} = Step(',
        f'            name="{label}",',
        f'            # 引用已创建的 Agent Team: {team_id}',
        '        )',
        ''
    ]


def _generate_condition_step(self, node: WorkflowNode) -> List[str]:
    """生成条件步骤代码"""
    config = node.config or {}
    branches = config.get("branches", [])
    label = node.label or "condition_step"
    
    lines = [
        f'        # 条件步骤: {label}',
        f'        self.{label}_conditions = [',
    ]
    
    for branch in branches:
        lines.append(f'            Condition(')
        lines.append(f'                expression="{branch.get("expression", "")}",')
        lines.append(f'                target="{branch.get("target_node_id", "")}"')
        lines.append('            ),')
    
    lines.extend([
        '        ]',
        ''
    ])
    
    return lines


def _generate_code_step(self, node: WorkflowNode) -> List[str]:
    """生成代码步骤代码"""
    config = node.config or {}
    code = config.get("code", "")
    label = node.label or "code_step"
    
    return [
        f'        # 代码步骤: {label}',
        f'        self.{label}_code = """{code}"""',
        ''
    ]


def _generate_delay_step(self, node: WorkflowNode) -> List[str]:
    """生成延迟步骤代码"""
    config = node.config or {}
    delay_seconds = config.get("delay_seconds", 1)
    label = node.label or "delay_step"
    
    return [
        f'        # 延迟步骤: {label}',
        f'        self.{label} = Step(',
        f'            name="{label}",',
        f'            delay={delay_seconds}',
        '        )',
        ''
    ]
