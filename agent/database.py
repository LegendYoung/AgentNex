"""
数据库和向量库初始化模块
"""

import os
import logging
# 从 PostgreSQL 配置导入数据库相关对象
from agent.database_postgres import engine, SessionLocal, Base
# 使用 agno 的 PostgresDb 替代 SQLAlchemy Session
from agno.db import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.embedder.openai import OpenAIEmbedder

from agent.config import (
    CHROMA_DIR,
    EMBEDDER_ID,
    EMBEDDER_BASE_URL,
    CHROMA_COLLECTION_NAME,
)

logger = logging.getLogger(__name__)

# ==================== PostgreSQL 数据库 ====================
# 使用 agno 的 PostgresDb，它支持 get_user_memories 等方法
db = PostgresDb(
    db_engine=engine,
    create_schema=True,
)

# 保留 SessionLocal 用于 FastAPI 依赖注入（非 agno 相关操作）
session_factory = SessionLocal

# ==================== ChromaDB 向量数据库 ====================

# 确保 ChromaDB 目录存在
CHROMA_DIR.mkdir(exist_ok=True)
logger.info(f"ChromaDB directory: {CHROMA_DIR}, exists: {CHROMA_DIR.exists()}")

# 使用 DashScope Embedding API（兼容 OpenAI 格式）
embedder = OpenAIEmbedder(
    id=EMBEDDER_ID,
    api_key=os.environ.get("DASHSCOPE_API_KEY"),
    base_url=EMBEDDER_BASE_URL,
    dimensions=1024,  # text-embedding-v3 默认维度
)

chroma_db = ChromaDb(
    collection=CHROMA_COLLECTION_NAME,
    path=str(CHROMA_DIR),
    embedder=embedder,
)

# 确保集合存在
try:
    chroma_db.create()
    logger.info(f"ChromaDB collection created/verified: {CHROMA_COLLECTION_NAME}")
    
    # 移除 count 调用，因为 ChromaDb 可能没有这个方法
    # vector_count = chroma_db.count()
    # logger.info(f"ChromaDB vector count: {vector_count}")
    
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB: {e}")
    raise

# 创建知识库实例
knowledge = Knowledge(
    vector_db=chroma_db,
    # 移除 embedder 参数，因为 Knowledge 构造函数不接受它
)