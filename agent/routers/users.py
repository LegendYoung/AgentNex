"""
用户管理路由（管理员功能）
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from agent.database_postgres import get_db
from agent.models_db import User, PlatformRole, UserStatus
from agent.utils.auth import get_current_user, require_admin, require_super_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])


# ==================== Pydantic 模型 ====================

class UpdateRoleRequest(BaseModel):
    role: PlatformRole = Field(..., description="用户角色")


class UpdateStatusRequest(BaseModel):
    status: UserStatus = Field(..., description="用户状态")


# ==================== 获取用户列表 ====================

@router.get("")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: PlatformRole = Query(None, description="角色筛选"),
    search: str = Query(None, description="搜索关键词"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取用户列表
    
    权限：平台管理员以上
    """
    query = db.query(User)
    
    # 角色筛选
    if role:
        query = query.filter(User.role == role)
    
    # 搜索
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    result = []
    for user in users:
        result.append({
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "status": user.status.value,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        })
    
    return {
        "success": True,
        "data": {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


# ==================== 修改用户角色 ====================

@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    修改用户角色
    
    权限：仅超级管理员
    
    规则：
    - 不能修改自己的角色
    - 不能修改其他超级管理员的角色
    """
    # 不能修改自己的角色
    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不能修改其他超级管理员的角色
    if user.role == PlatformRole.SUPER_ADMIN and str(user.id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot modify another super admin's role")
    
    # 更新角色
    old_role = user.role
    user.role = request.role
    db.commit()
    
    logger.info(f"User role updated: {user.email} from {old_role.value} to {request.role.value}")
    
    return {
        "success": True,
        "message": f"User role updated to {request.role.value}"
    }


# ==================== 修改用户状态 ====================

@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: str,
    request: UpdateStatusRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    修改用户状态（启用/禁用）
    
    权限：平台管理员以上
    
    规则：
    - 不能修改自己的状态
    - 不能修改超级管理员的状态
    """
    # 不能修改自己的状态
    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot change your own status")
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不能修改超级管理员的状态
    if user.role == PlatformRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify super admin's status")
    
    # 更新状态
    old_status = user.status
    user.status = request.status
    db.commit()
    
    logger.info(f"User status updated: {user.email} from {old_status.value} to {request.status.value}")
    
    return {
        "success": True,
        "message": f"User status updated to {request.status.value}"
    }


# ==================== 删除用户 ====================

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    删除用户
    
    权限：仅超级管理员
    
    规则：
    - 不能删除自己
    - 不能删除其他超级管理员
    """
    # 不能删除自己
    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不能删除其他超级管理员
    if user.role == PlatformRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete super admin")
    
    # 删除用户
    db.delete(user)
    db.commit()
    
    logger.info(f"User deleted: {user.email}")
    
    return {
        "success": True,
        "message": "User deleted successfully"
    }
