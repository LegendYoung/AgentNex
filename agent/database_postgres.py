"""
PostgreSQL 数据库配置和初始化
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# PostgreSQL 连接配置
POSTGRES_USER = os.getenv("POSTGRES_USER", "agentnex")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "agentnex123")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "agentnex")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 生产环境设置为 False
    pool_pre_ping=True,  # 检查连接有效性
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话
    用于 FastAPI 依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表
    """
    from models_db import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


if __name__ == "__main__":
    # 测试数据库连接
    try:
        connection = engine.connect()
        print("✅ PostgreSQL connection successful!")
        connection.close()
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
