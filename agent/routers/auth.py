"""
认证路由
用户注册、登录、Token刷新、密码修改
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database_postgres import get_db
from models_db import User, PlatformRole, UserStatus
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ==================== Pydantic 模型 ====================

class RegisterRequest(BaseModel):
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=32, description="密码")
    name: str = Field(None, min_length=2, max_length=32, description="用户名")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """密码必须包含大小写字母、数字、特殊字符"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """简单邮箱格式验证"""
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class LoginRequest(BaseModel):
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=32, description="新密码")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """密码格式验证"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str = None
    role: str
    require_password_change: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== 注册 ====================

@router.post("/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    流程：
    1. 验证邮箱是否已存在
    2. 加密密码
    3. 创建用户
    """
    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # 创建用户
    hashed_password = hash_password(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password,
        name=request.name,
        role=PlatformRole.USER,
        status=UserStatus.ACTIVE,
        require_password_change=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {request.email}")
    
    return {
        "success": True,
        "data": {
            "user_id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role.value,
            "created_at": new_user.created_at.isoformat()
        }
    }


# ==================== 登录 ====================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    流程：
    1. 验证邮箱和密码
    2. 检查账号状态
    3. 生成 Token
    4. 更新最后登录时间
    """
    # 查找用户
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # 检查账号状态
    if user.status == UserStatus.DISABLED:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # 生成 Token
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "require_password_change": user.require_password_change
        }
    }


# ==================== Token 刷新 ====================

@router.post("/refresh")
async def refresh_token(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """
    刷新 Access Token
    
    使用 Refresh Token 获取新的 Access Token
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    refresh_token = authorization.replace("Bearer ", "")
    
    # 解码 Token
    payload = decode_token(refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.status == UserStatus.DISABLED:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # 生成新的 Access Token
    new_access_token = create_access_token(str(user.id), user.role.value)
    
    return {
        "success": True,
        "data": {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    }


# ==================== 修改密码 ====================

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    
    流程：
    1. 验证旧密码
    2. 更新新密码
    3. 取消强制修改密码标记
    """
    # 验证旧密码
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    
    # 更新密码
    current_user.password_hash = hash_password(request.new_password)
    current_user.require_password_change = False
    db.commit()
    
    logger.info(f"User changed password: {current_user.email}")
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


# ==================== 获取当前用户信息 ====================

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "success": True,
        "data": {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role.value,
            "status": current_user.status.value,
            "created_at": current_user.created_at.isoformat(),
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
        }
    }
