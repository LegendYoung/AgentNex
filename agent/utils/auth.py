"""
认证工具模块
JWT Token 生成、验证、密码加密
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from agent.database_postgres import get_db
from agent.models_db import User, PlatformRole, UserStatus

# JWT 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "agentnex-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


# ==================== 密码加密 ====================

def hash_password(password: str) -> str:
    """
    使用 bcrypt 加密密码
    
    Args:
        password: 明文密码
    
    Returns:
        加密后的密码哈希
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
    
    Returns:
        是否匹配
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ==================== JWT Token ====================

def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 Access Token
    
    Args:
        user_id: 用户ID
        role: 用户角色
        expires_delta: 过期时间增量
    
    Returns:
        JWT Token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    创建 Refresh Token
    
    Args:
        user_id: 用户ID
    
    Returns:
        JWT Token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码 Token
    
    Args:
        token: JWT Token
    
    Returns:
        Payload 字典
    
    Raises:
        HTTPException: Token 无效或过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==================== 权限验证 ====================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户
    
    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话
    
    Returns:
        当前用户对象
    
    Raises:
        HTTPException: 未授权
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="User account is disabled")
    
    return user


def require_role(required_roles: list):
    """
    角色权限装饰器
    
    Args:
        required_roles: 需要的角色列表
    
    Returns:
        依赖函数
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required roles: {required_roles}"
            )
        return current_user
    
    return role_checker


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求超级管理员权限
    """
    if current_user.role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Super admin permission required"
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限（超级管理员或平台管理员）
    """
    if current_user.role not in [PlatformRole.SUPER_ADMIN, PlatformRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )
    return current_user
