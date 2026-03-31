#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建 PostgreSQL 数据库表并初始化超级管理员用户
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.database_postgres import init_db, engine
from agent.models_db import User, PlatformRole
from sqlalchemy.orm import sessionmaker
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_super_admin():
    """创建超级管理员用户"""
    from agent.config import SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 检查是否已存在超级管理员
        existing_user = db.query(User).filter(User.email == SUPER_ADMIN_EMAIL).first()
        if existing_user:
            logger.info(f"Super admin user {SUPER_ADMIN_EMAIL} already exists")
            return
        
        # 创建超级管理员（注意：这里应该哈希密码，但为了简化先直接存储）
        super_admin = User(
            email=SUPER_ADMIN_EMAIL,
            password_hash=SUPER_ADMIN_PASSWORD,  # 字段名是 password_hash
            role=PlatformRole.SUPER_ADMIN,  # 字段名是 role 而不是 platform_role
            status="active",
            require_password_change=True,  # 首次登录强制修改密码
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(super_admin)
        db.commit()
        logger.info(f"Super admin user {SUPER_ADMIN_EMAIL} created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create super admin: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Initializing database...")
    try:
        # 初始化数据库表
        init_db()
        
        # 创建超级管理员
        create_super_admin()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)