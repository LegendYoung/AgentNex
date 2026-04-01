"""
PostgreSQL 数据库配置和初始化
"""

import os
import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# 加载根目录的 .env 文件，强制覆盖已存在的环境变量
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

logger = logging.getLogger(__name__)

# PostgreSQL 连接配置
POSTGRES_USER = os.getenv("POSTGRES_USER", "agentnex")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "agentnex123")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "agentnex")

# URL 编码密码以避免特殊字符问题，并添加编码参数
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{quote_plus(POSTGRES_PASSWORD)}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?client_encoding=utf8"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 生产环境设置为 False
    pool_pre_ping=True,  # 检查连接有效性
    pool_size=10,
    max_overflow=20,
    connect_args={'options': '-c client_encoding=UTF8'}
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
    from .models_db import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


if __name__ == "__main__":
    # 测试数据库连接
    try:
        connection = engine.connect()
        print("PostgreSQL connection successful!")
        connection.close()
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")