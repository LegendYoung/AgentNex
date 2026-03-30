"""
Agent 导入服务
解析 Agno Python 代码，提取配置信息
"""

import re
import ast
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def parse_agent_code(code: str) -> Dict[str, Any]:
    """
    解析 Agno Python 代码，提取 Agent 配置
    
    Args:
        code: Python 代码字符串
    
    Returns:
        Agent 配置字典
    """
    config = {
        "name": "",
        "description": "",
        "system_prompt": "",
        "model_id": "qwen-plus",
        "temperature": 70,
        "top_p": 90,
        "enable_memory": False,
        "memory_type": "short_term",
        "memory_window": 10,
        "enable_knowledge": False,
        "knowledge_base_ids": [],
        "enable_tools": False,
        "tool_config": {
            "web_search": False,
            "file_read": False,
            "python_exec": False,
            "permission": "all"
        }
    }
    
    try:
        # 解析代码为 AST
        tree = ast.parse(code)
        
        # 遍历 AST 查找 Agent 实例化
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # 查找 agent = Agent(...) 的赋值
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "agent":
                        if isinstance(node.value, ast.Call):
                            config.update(extract_agent_config(node.value))
            
            elif isinstance(node, ast.Call):
                # 直接查找 Agent(...) 调用
                if isinstance(node.func, ast.Name) and node.func.id == "Agent":
                    config.update(extract_agent_config(node))
        
        # 使用正则表达式补充提取（备用方法）
        config.update(extract_with_regex(code))
        
        logger.info(f"Agent code parsed successfully: {config.get('name')}")
        
    except Exception as e:
        logger.error(f"Failed to parse agent code: {e}")
        # 尝试使用正则表达式提取
        config.update(extract_with_regex(code))
    
    return config


def extract_agent_config(call_node: ast.Call) -> Dict[str, Any]:
    """
    从 AST Call 节点提取 Agent 配置
    
    Args:
        call_node: AST Call 节点
    
    Returns:
        配置字典
    """
    config = {}
    
    for keyword in call_node.keywords:
        arg_name = keyword.arg
        arg_value = keyword.value
        
        # 提取字符串参数
        if isinstance(arg_value, ast.Constant) and isinstance(arg_value.value, str):
            if arg_name == "name":
                config["name"] = arg_value.value
            elif arg_name == "instructions":
                config["system_prompt"] = arg_value.value
        
        # 提取数值参数
        elif isinstance(arg_value, ast.Constant) and isinstance(arg_value.value, (int, float)):
            if arg_name == "temperature":
                # 转换为整数（乘以 100）
                config["temperature"] = int(arg_value.value * 100)
            elif arg_name == "top_p":
                # 转换为整数（乘以 100）
                config["top_p"] = int(arg_value.value * 100)
        
        # 提取布尔参数
        elif isinstance(arg_value, ast.Constant) and isinstance(arg_value.value, bool):
            if arg_name == "update_memory_on_run":
                config["enable_memory"] = arg_value.value
            elif arg_name == "search_knowledge":
                config["enable_knowledge"] = arg_value.value
        
        # 提取列表参数（工具）
        elif arg_name == "tools" and isinstance(arg_value, ast.List):
            if arg_value.elts:
                config["enable_tools"] = True
                # 提取工具名称
                tool_config = {
                    "web_search": False,
                    "file_read": False,
                    "python_exec": False,
                    "permission": "all"
                }
                for tool in arg_value.elts:
                    if isinstance(tool, ast.Name):
                        if "web_search" in tool.id.lower():
                            tool_config["web_search"] = True
                        elif "file_read" in tool.id.lower():
                            tool_config["file_read"] = True
                        elif "python_exec" in tool.id.lower():
                            tool_config["python_exec"] = True
                config["tool_config"] = tool_config
    
    return config


def extract_with_regex(code: str) -> Dict[str, Any]:
    """
    使用正则表达式从代码中提取配置（备用方法）
    
    Args:
        code: Python 代码字符串
    
    Returns:
        配置字典
    """
    config = {}
    
    # 提取 name
    name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', code)
    if name_match:
        config["name"] = name_match.group(1)
    
    # 提取 instructions（系统提示词）
    instructions_match = re.search(r'instructions\s*=\s*"""([^"]+)"""', code, re.DOTALL)
    if not instructions_match:
        instructions_match = re.search(r'instructions\s*=\s*["\']([^"\']+)["\']', code)
    if instructions_match:
        config["system_prompt"] = instructions_match.group(1).strip()
    
    # 提取 temperature
    temp_match = re.search(r'temperature\s*=\s*([0-9.]+)', code)
    if temp_match:
        config["temperature"] = int(float(temp_match.group(1)) * 100)
    
    # 提取 top_p
    top_p_match = re.search(r'top_p\s*=\s*([0-9.]+)', code)
    if top_p_match:
        config["top_p"] = int(float(top_p_match.group(1)) * 100)
    
    # 提取模型 ID
    model_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', code)
    if model_match:
        config["model_id"] = model_match.group(1)
    
    # 检测是否启用记忆
    if "update_memory_on_run" in code or "add_memories_to_context" in code:
        config["enable_memory"] = True
    
    # 检测是否启用知识库
    if "search_knowledge" in code or "Knowledge(" in code:
        config["enable_knowledge"] = True
    
    # 检测是否启用工具
    if "tools=" in code:
        config["enable_tools"] = True
        
        # 提取工具配置
        tool_config = {
            "web_search": False,
            "file_read": False,
            "python_exec": False,
            "permission": "all"
        }
        
        if "web_search" in code.lower():
            tool_config["web_search"] = True
        if "file_read" in code.lower():
            tool_config["file_read"] = True
        if "python_exec" in code.lower() or "python" in code.lower():
            tool_config["python_exec"] = True
        
        config["tool_config"] = tool_config
    
    return config


def validate_agent_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证 Agent 配置的完整性和有效性
    
    Args:
        config: Agent 配置字典
    
    Returns:
        (是否有效, 错误信息)
    """
    # 检查必填字段
    if not config.get("name"):
        return False, "Agent name is required"
    
    if not config.get("system_prompt"):
        return False, "System prompt is required"
    
    # 检查字段范围
    if not (2 <= len(config.get("name", "")) <= 32):
        return False, "Agent name must be between 2 and 32 characters"
    
    if not (10 <= len(config.get("system_prompt", ""))):
        return False, "System prompt must be at least 10 characters"
    
    # 检查温度参数
    if not (0 <= config.get("temperature", 70) <= 200):
        return False, "Temperature must be between 0 and 200"
    
    # 检查 top_p 参数
    if not (0 <= config.get("top_p", 90) <= 100):
        return False, "Top-P must be between 0 and 100"
    
    return True, ""
