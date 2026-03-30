"""
超级管理员初始化脚本
部署后自动初始化唯一超级管理员账号
"""

import os
import sys
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database_postgres import SessionLocal, init_db
from models_db import User, PlatformRole, UserStatus
from utils.auth import hash_password


def init_super_admin():
    """
    初始化超级管理员账号
    
    默认账号：admin@agentnex.io
    默认密码：AgentNex@2026
    首次登录强制修改密码
    """
    db: Session = SessionLocal()
    
    try:
        # 检查是否已存在超级管理员
        existing_super_admin = db.query(User).filter(
            User.role == PlatformRole.SUPER_ADMIN
        ).first()
        
        if existing_super_admin:
            print(f"✅ Super admin already exists: {existing_super_admin.email}")
            return
        
        # 创建超级管理员
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "admin@agentnex.io")
        super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "AgentNex@2026")
        
        # 检查邮箱是否已被使用
        existing_user = db.query(User).filter(
            User.email == super_admin_email
        ).first()
        
        if existing_user:
            # 如果邮箱已存在，直接提升为超级管理员
            existing_user.role = PlatformRole.SUPER_ADMIN
            existing_user.require_password_change = True
            db.commit()
            print(f"✅ Existing user promoted to super admin: {super_admin_email}")
            return
        
        # 创建新的超级管理员
        hashed_password = hash_password(super_admin_password)
        
        super_admin = User(
            email=super_admin_email,
            password_hash=hashed_password,
            name="Super Admin",
            role=PlatformRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            require_password_change=True,  # 首次登录强制修改密码
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(super_admin)
        db.commit()
        
        print("=" * 60)
        print("✅ Super admin initialized successfully!")
        print("=" * 60)
        print(f"Email: {super_admin_email}")
        print(f"Password: {super_admin_password}")
        print("⚠️  IMPORTANT: Please change the password after first login!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Failed to initialize super admin: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("Initializing AgentNex Platform...")
    print("-" * 60)
    
    # 初始化数据库表
    print("Creating database tables...")
    init_db()
    print("✅ Database tables created")
    
    # 初始化超级管理员
    init_super_admin()
    
    print("-" * 60)
    print("✅ Initialization completed!")


if __name__ == "__main__":
    main()
