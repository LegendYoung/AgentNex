"""
Agent 导入导出路由
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agent.database_postgres import get_db
from agent.models_db import Agent, User
from agent.utils.auth import get_current_user
from agent.services.agent_export_service import export_agent_to_code, generate_agent_readme
from agent.services.agent_import_service import parse_agent_code, validate_agent_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# ==================== Pydantic 模型 ====================

class AgentImportRequest(BaseModel):
    code: str = Field(..., min_length=50, description="Agno Python 代码")


class AgentImportResponse(BaseModel):
    agent_config: dict


# ==================== 导出 Agent ====================

@router.post("/{agent_id}/export")
async def export_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出 Agent 为 Agno Runtime 兼容的 Python 代码
    
    返回可直接运行的 Python 代码文件
    """
    # 查找 Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 权限检查（创建者可导出）
    if str(agent.creator_id) != str(current_user.id):
        # 检查是否有编辑权限
        from routers.agents import check_agent_permission
        if not check_agent_permission(db, str(current_user.id), agent, "edit"):
            raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        # 导出代码
        code = export_agent_to_code(agent)
        
        # 生成 README
        readme = generate_agent_readme(agent)
        
        # 生成文件名
        filename = agent.name.replace(" ", "_").lower() + ".py"
        
        logger.info(f"Agent exported: {agent.name} by {current_user.email}")
        
        return {
            "success": True,
            "data": {
                "code": code,
                "readme": readme,
                "filename": filename,
                "agent_name": agent.name
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to export agent: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ==================== 导入 Agent ====================

@router.post("/import", response_model=dict)
async def import_agent(
    request: AgentImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导入 Agno Python 代码，解析配置
    
    流程：
    1. 解析 Python 代码
    2. 提取 Agent 配置
    3. 验证配置有效性
    4. 返回配置供前端回填表单
    """
    try:
        # 解析代码
        config = parse_agent_code(request.code)
        
        # 验证配置
        is_valid, error_msg = validate_agent_config(config)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid agent config: {error_msg}")
        
        # 添加描述字段（如果没有）
        if not config.get("description"):
            config["description"] = f"Imported from code: {config.get('name', 'Unknown Agent')}"
        
        logger.info(f"Agent code imported: {config.get('name')} by {current_user.email}")
        
        return {
            "success": True,
            "data": {
                "agent_config": config,
                "import_warnings": []  # 可以添加导入过程中的警告信息
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import agent code: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ==================== 下载 Agent 包 ====================

@router.get("/{agent_id}/download")
async def download_agent_package(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载 Agent 完整包（代码 + README + 配置文件）
    
    返回 ZIP 文件
    """
    from fastapi.responses import StreamingResponse
    import zipfile
    import io
    
    # 查找 Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 权限检查
    if str(agent.creator_id) != str(current_user.id):
        from routers.agents import check_agent_permission
        if not check_agent_permission(db, str(current_user.id), agent, "edit"):
            raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        # 生成代码和 README
        code = export_agent_to_code(agent)
        readme = generate_agent_readme(agent)
        
        # 创建 ZIP 文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加 Python 代码文件
            code_filename = agent.name.replace(" ", "_").lower() + ".py"
            zipf.writestr(code_filename, code)
            
            # 添加 README 文件
            zipf.writestr("README.md", readme)
            
            # 添加配置文件（JSON 格式）
            import json
            config_json = json.dumps({
                "name": agent.name,
                "description": agent.description,
                "system_prompt": agent.system_prompt,
                "model_id": agent.model_id,
                "temperature": agent.temperature / 100.0,
                "top_p": agent.top_p / 100.0,
                "enable_memory": agent.enable_memory,
                "enable_knowledge": agent.enable_knowledge,
                "enable_tools": agent.enable_tools
            }, indent=2, ensure_ascii=False)
            zipf.writestr("config.json", config_json)
            
            # 添加 requirements.txt
            requirements = """agno>=1.1.11
dashscope>=1.20.14
chromadb>=0.5.23
python-dotenv>=1.0.1
"""
            zipf.writestr("requirements.txt", requirements)
            
            # 添加 .env.example
            env_example = """# DashScope API Key
DASHSCOPE_API_KEY=your-api-key-here
"""
            zipf.writestr(".env.example", env_example)
        
        zip_buffer.seek(0)
        
        logger.info(f"Agent package downloaded: {agent.name} by {current_user.email}")
        
        # 返回 ZIP 文件
        zip_filename = agent.name.replace(" ", "_").lower() + ".zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"'
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create agent package: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
