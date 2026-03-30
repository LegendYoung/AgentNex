"""
Agent 导出服务
将数据库中的 Agent 配置转换为 Agno Runtime 兼容的 Python 代码
"""

import logging
from typing import Dict, Any
from models_db import Agent

logger = logging.getLogger(__name__)


def export_agent_to_code(agent: Agent) -> str:
    """
    将 Agent 配置导出为 Agno Runtime 兼容的 Python 代码
    
    Args:
        agent: Agent 数据库模型实例
    
    Returns:
        可直接运行的 Python 代码字符串
    """
    # 导入语句
    imports = [
        "from agno.agent import Agent",
        "from agno.models.dashscope import DashScope",
    ]
    
    # 如果启用记忆，导入记忆相关模块
    if agent.enable_memory:
        imports.append("from agno.memory import MemoryManager")
        imports.append("from agno.db.sqlite import SqliteDb")
    
    # 如果启用知识库，导入知识库相关模块
    if agent.enable_knowledge:
        imports.append("from agno.knowledge.knowledge import Knowledge")
        imports.append("from agno.vectordb.chroma import ChromaDb")
        imports.append("from agno.knowledge.embedder.openai import OpenAIEmbedder")
    
    # 如果启用工具，导入工具相关模块
    if agent.enable_tools:
        imports.append("from agno.tools import tool")
    
    # 模型配置
    model_config = f'''DashScope(
        id="{agent.model_id}",
        api_key="your-dashscope-api-key",  # 请替换为您的 API Key
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )'''
    
    # Agent 配置参数
    agent_params = []
    agent_params.append(f'name="{agent.name}"')
    agent_params.append(f'model={model_config}')
    agent_params.append(f'instructions="""{agent.system_prompt}"""')
    agent_params.append('markdown=True')
    
    # 温度参数（需要除以100）
    agent_params.append(f'temperature={agent.temperature / 100.0}')
    
    # Top-p 参数（需要除以100）
    agent_params.append(f'top_p={agent.top_p / 100.0}')
    
    # 记忆配置
    if agent.enable_memory:
        memory_config = '''
    # 记忆配置
    db = SqliteDb(db_file="agents.db")
    memory_manager = MemoryManager(
        db=db,
        model=DashScope(
            id="qwen-plus",
            api_key="your-dashscope-api-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    )
'''
        agent_params.append('db=db')
        agent_params.append('memory_manager=memory_manager')
        agent_params.append('update_memory_on_run=True')
        agent_params.append('add_memories_to_context=True')
    
    # 知识库配置
    if agent.enable_knowledge:
        knowledge_config = '''
    # 知识库配置
    embedder = OpenAIEmbedder(
        id="text-embedding-v3",
        api_key="your-dashscope-api-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        dimensions=1024
    )
    
    chroma_db = ChromaDb(
        collection="agentnex_knowledge",
        path="./chromadb",
        embedder=embedder
    )
    
    knowledge = Knowledge(vector_db=chroma_db)
'''
        agent_params.append('knowledge=knowledge')
        agent_params.append('search_knowledge=True')
    
    # 工具配置
    if agent.enable_tools:
        tools_config = []
        
        tool_config = agent.tool_config or {}
        
        if tool_config.get("web_search"):
            tools_config.append('web_search_tool')
        
        if tool_config.get("file_read"):
            tools_config.append('file_read_tool')
        
        if tool_config.get("python_exec"):
            tools_config.append('python_exec_tool')
        
        if tools_config:
            agent_params.append(f'tools=[{", ".join(tools_config)}]')
    
    # 构建 Agent 代码
    code = '\n'.join(imports) + '\n\n'
    
    # 添加记忆配置
    if agent.enable_memory:
        code += memory_config + '\n'
    
    # 添加知识库配置
    if agent.enable_knowledge:
        code += knowledge_config + '\n'
    
    # 添加工具定义
    if agent.enable_tools:
        code += '''
# 自定义工具示例
@tool
def web_search_tool(query: str) -> str:
    """搜索互联网获取实时信息"""
    # 实现搜索逻辑
    return f"搜索结果: {query}"

@tool
def file_read_tool(file_path: str) -> str:
    """读取文件内容"""
    # 实现文件读取逻辑
    with open(file_path, 'r') as f:
        return f.read()

@tool
def python_exec_tool(code: str) -> str:
    """执行 Python 代码"""
    # 实现代码执行逻辑
    exec(code)
    return "代码执行成功"

'''
    
    # 创建 Agent 实例
    code += f'''
# 创建 Agent 实例
agent = Agent(
    {',\n    '.join(agent_params)}
)

# 运行 Agent
if __name__ == "__main__":
    response = agent.run("你好，请介绍一下你自己")
    print(response.content)
'''
    
    return code


def generate_agent_readme(agent: Agent) -> str:
    """
    生成 Agent 的 README 文档
    
    Args:
        agent: Agent 数据库模型实例
    
    Returns:
        Markdown 格式的 README 内容
    """
    readme = f'''# {agent.name}

{agent.description or '这是一个基于 Agno Runtime 的 AI Agent'}

## 配置信息

- **模型**: {agent.model_id}
- **温度**: {agent.temperature / 100.0}
- **Top-P**: {agent.top_p / 100.0}

## 功能特性

'''
    
    if agent.enable_memory:
        readme += f'- ✅ **记忆功能**: {agent.memory_type}（记忆窗口: {agent.memory_window} 轮）\n'
    else:
        readme += '- ❌ **记忆功能**: 未启用\n'
    
    if agent.enable_knowledge:
        readme += f'- ✅ **知识库**: 已启用（关联 {len(agent.knowledge_base_ids)} 个知识库）\n'
    else:
        readme += '- ❌ **知识库**: 未启用\n'
    
    if agent.enable_tools:
        readme += '- ✅ **工具调用**: 已启用\n'
        tool_config = agent.tool_config or {}
        if tool_config.get("web_search"):
            readme += '  - 网页搜索\n'
        if tool_config.get("file_read"):
            readme += '  - 文件读取\n'
        if tool_config.get("python_exec"):
            readme += '  - Python 执行\n'
    else:
        readme += '- ❌ **工具调用**: 未启用\n'
    
    readme += f'''
## 系统提示词

```
{agent.system_prompt}
```

## 使用方法

1. 安装依赖：
```bash
pip install agno dashscope
```

2. 配置 API Key：
```bash
export DASHSCOPE_API_KEY=your-api-key
```

3. 运行代码：
```bash
python {agent.name.replace(" ", "_").lower()}.py
```

## 注意事项

- 请确保已配置 DashScope API Key
- 如需使用知识库功能，请先创建并配置 ChromaDB
- 如需使用工具功能，请根据实际需求实现对应的工具函数

---

生成时间: {agent.created_at.strftime("%Y-%m-%d %H:%M:%S")}
创建者: AgentNex Platform
'''
    
    return readme
