"""
AI Agent API Server - Version 2.0
基于 FastAPI 提供 REST API 接口

新增功能（P0 MVP）:
- 用户认证系统（注册/登录/JWT）
- RBAC 权限系统
- 团队管理
- Agent 创建向导（4步分步表单）
- Agent CRUD 管理
- Agent 配置导入/导出
- 草稿系统
- PostgreSQL 数据库

架构:
- config.py: 配置管理
- database_postgres.py: PostgreSQL 数据库
- models_db.py: 数据模型
- utils/auth.py: 认证工具
- routers/: API 路由层
  - auth.py: 认证路由
  - users.py: 用户管理路由
  - teams.py: 团队管理路由
  - chat.py: 聊天路由
  - sessions.py: 会话管理
  - memory.py: 记忆管理
  - knowledge.py: 知识库管理
  - tools.py: 工具管理
"""

import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.config import API_TITLE, API_VERSION, API_DESCRIPTION, PROMPTS_DIR
from agent.database import knowledge
from agent.tools import set_knowledge_instance

# 导入所有路由
from agent.routers import (
    chat_router,
    sessions_router,
    memory_router,
    knowledge_router,
    tools_router,
)
from agent.routers.auth import router as auth_router
from agent.routers.users import router as users_router
from agent.routers.teams import router as teams_router
from agent.routers.agents import router as agents_router
from agent.routers.agent_import_export import router as agent_import_export_router
from agent.routers.knowledge_bases import router as knowledge_bases_router
from agent.routers.agent_teams import router as agent_teams_router
from agent.routers.workflows import router as workflows_router

from agent.services.session_service import session_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 初始化知识库实例 ====================

set_knowledge_instance(knowledge)


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("AgentNex Platform starting up...")
    
    # 初始化数据库和超级管理员
    try:
        from agent.database_postgres import init_db
        init_db()
        logger.info("Database tables created successfully")
        
        # 初始化超级管理员和示例数据
        from agent.init_examples import init_p0_environment
        init_p0_environment()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization error: {e}")
    
    yield
    
    # 关闭时
    from agent.routers.knowledge import close_selenium_driver
    close_selenium_driver()
    logger.info("AgentNex Platform shutdown, resources cleaned")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器 - 捕获所有未处理的异常"""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n")
        }
    )


# ==================== 注册路由 ====================

# 认证路由
app.include_router(auth_router, tags=["auth"])

# 用户管理路由
app.include_router(users_router, tags=["users"])

# 团队管理路由
app.include_router(teams_router, tags=["teams"])

# Agent 管理路由
app.include_router(agents_router, tags=["agents"])
app.include_router(agent_import_export_router, tags=["agents"])

# Agent Teams 路由（P1阶段）
app.include_router(agent_teams_router, tags=["agent-teams"])

# Workflows 路由（P2阶段）
app.include_router(workflows_router, tags=["workflows"])

# 知识库管理路由（增强版）
app.include_router(knowledge_bases_router, tags=["knowledge"])

# 聊天路由
app.include_router(chat_router)

# 会话管理路由
app.include_router(sessions_router)

# 记忆管理路由
app.include_router(memory_router)

# 知识库路由
app.include_router(knowledge_router)

# 工具路由
app.include_router(tools_router)


# ==================== 根端点 ====================

@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "status": "ok",
        "message": "AgentNex Platform API is running",
        "version": API_VERSION,
        "features": [
            "user_authentication",
            "rbac_permissions",
            "team_management",
            "agent_management",
            "agent_import_export",
            "draft_system",
            "agent_test_panel",
            "knowledge_base_management",
            "document_upload",
            "knowledge_search",
            "agent_chat",
            "memory_management",
            "tool_calling",
            "session_management"
        ],
        "sessions_count": session_service.count(),
        "prompt_templates_dir": str(PROMPTS_DIR)
    }


# ==================== API 文档端点 ====================

@app.get("/api/v1")
async def api_info():
    """API 信息"""
    return {
        "version": "v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "teams": "/api/v1/teams",
            "agents": "/api/v1/agents",
            "chat": "/chat",
            "sessions": "/sessions",
            "memory": "/memory",
            "knowledge": "/knowledge",
            "tools": "/tools"
        }
    }


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
