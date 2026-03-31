"""
P0 阶段完整初始化脚本
一键初始化超级管理员和示例 Agent
"""

import sys
import os

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database_postgres import SessionLocal, init_db
from models_db import User, Agent, PlatformRole
from utils.auth import hash_password
from examples.agents import create_example_agents
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_p0_environment():
    """
    P0 阶段完整初始化
    
    流程：
    1. 初始化数据库表
    2. 创建超级管理员
    3. 创建示例 Agent
    """
    db: Session = SessionLocal()
    
    try:
        # ==================== Step 1: 初始化数据库表 ====================
        logger.info("=" * 60)
        logger.info("Step 1: Initializing database tables...")
        logger.info("=" * 60)
        
        init_db()
        logger.info("[OK] Database tables created successfully\n")
        
        # ==================== Step 2: 创建超级管理员 ====================
        logger.info("=" * 60)
        logger.info("Step 2: Creating super admin...")
        logger.info("=" * 60)
        
        # 检查是否已存在超级管理员
        existing_super_admin = db.query(User).filter(
            User.role == PlatformRole.SUPER_ADMIN
        ).first()
        
        if existing_super_admin:
            logger.info(f"[OK] Super admin already exists: {existing_super_admin.email}")
            super_admin = existing_super_admin
        else:
            # 创建超级管理员
            super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "admin@agentnex.io")
            super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "AgentNex@2026")
            
            # 检查邮箱是否已被使用
            existing_user = db.query(User).filter(
                User.email == super_admin_email
            ).first()
            
            if existing_user:
                existing_user.role = PlatformRole.SUPER_ADMIN
                existing_user.require_password_change = True
                db.commit()
                super_admin = existing_user
                logger.info(f"[OK] Existing user promoted to super admin: {super_admin_email}")
            else:
                # 创建新的超级管理员
                hashed_password = hash_password(super_admin_password)
                
                super_admin = User(
                    email=super_admin_email,
                    password_hash=hashed_password,
                    name="Super Admin",
                    role=PlatformRole.SUPER_ADMIN,
                    require_password_change=True
                )
                
                db.add(super_admin)
                db.commit()
                
                logger.info("=" * 60)
                logger.info("[OK] Super admin created successfully!")
                logger.info("=" * 60)
                logger.info(f"Email: {super_admin_email}")
                logger.info(f"Password: {super_admin_password}")
                logger.info("[WARNING] IMPORTANT: Please change the password after first login!")
                logger.info("=" * 60 + "\n")
        
        # ==================== Step 3: 创建示例 Agent ====================
        logger.info("=" * 60)
        logger.info("Step 3: Creating example agents...")
        logger.info("=" * 60)
        
        # 检查是否已有示例 Agent
        existing_examples = db.query(Agent).filter(
            Agent.name.in_(["智能客服助手", "代码审查专家", "知识问答助手"])
        ).count()
        
        if existing_examples > 0:
            logger.info(f"[OK] Example agents already exist ({existing_examples} found)\n")
        else:
            created_agents = create_example_agents(db, str(super_admin.id))
            
            logger.info("=" * 60)
            logger.info("[OK] Example agents created successfully!")
            logger.info("=" * 60)
            for agent in created_agents:
                logger.info(f"  - {agent.name} (ID: {agent.id})")
            logger.info("=" * 60 + "\n")
        
        # ==================== 完成 ====================
        logger.info("=" * 60)
        logger.info("[SUCCESS] P0 Environment Initialization Completed!")
        logger.info("=" * 60)
        logger.info("\nAccess Information:")
        logger.info("  - API: http://localhost:8000")
        logger.info("  - Docs: http://localhost:8000/docs")
        logger.info("  - Admin: " + super_admin.email)
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_p0_environment()
