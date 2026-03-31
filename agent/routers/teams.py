"""
团队管理路由
团队创建、成员邀请、成员管理
"""

import secrets
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_

from agent.database_postgres import get_db
from agent.models_db import User, Team, TeamMember, TeamInvitation, TeamRole, PlatformRole
from agent.utils.auth import get_current_user, require_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


# ==================== Pydantic 模型 ====================

class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=32, description="团队名称")
    description: str = Field(None, min_length=10, max_length=200, description="团队描述")


class InviteMemberRequest(BaseModel):
    email: str = Field(..., description="被邀请人邮箱")
    role: TeamRole = Field(TeamRole.VIEWER, description="团队角色")


class JoinTeamRequest(BaseModel):
    invite_code: str = Field(..., description="邀请码")


# ==================== 辅助函数 ====================

def check_team_permission(
    db: Session,
    user_id: str,
    team_id: str,
    required_roles: list = [TeamRole.ADMIN]
) -> TeamMember:
    """
    检查用户在团队中的权限
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        team_id: 团队ID
        required_roles: 需要的角色列表
    
    Returns:
        TeamMember 对象
    
    Raises:
        HTTPException: 无权限
    """
    member = db.query(TeamMember).filter(
        and_(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="You are not a member of this team")
    
    if member.role not in required_roles:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return member


# ==================== 创建团队 ====================

@router.post("")
async def create_team(
    request: CreateTeamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建团队
    
    创建者自动成为团队管理员
    """
    # 创建团队
    new_team = Team(
        name=request.name,
        description=request.description,
        creator_id=current_user.id
    )
    
    db.add(new_team)
    db.flush()  # 获取团队ID
    
    # 创建者自动成为团队管理员
    creator_member = TeamMember(
        team_id=new_team.id,
        user_id=current_user.id,
        role=TeamRole.ADMIN
    )
    
    db.add(creator_member)
    db.commit()
    db.refresh(new_team)
    
    logger.info(f"Team created: {new_team.name} by {current_user.email}")
    
    return {
        "success": True,
        "data": {
            "team_id": str(new_team.id),
            "name": new_team.name,
            "description": new_team.description,
            "creator_id": str(new_team.creator_id),
            "created_at": new_team.created_at.isoformat()
        }
    }


# ==================== 获取团队列表 ====================

@router.get("")
async def list_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户所在的团队列表"""
    # 查询用户所在的团队
    memberships = db.query(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()
    
    teams = []
    for membership in memberships:
        team = membership.team
        teams.append({
            "team_id": str(team.id),
            "name": team.name,
            "description": team.description,
            "role": membership.role.value,
            "member_count": len(team.members),
            "created_at": team.created_at.isoformat()
        })
    
    return {
        "success": True,
        "data": {
            "teams": teams,
            "total": len(teams)
        }
    }


# ==================== 邀请成员 ====================

@router.post("/{team_id}/invitations")
async def invite_member(
    team_id: str,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    邀请成员加入团队
    
    生成唯一邀请链接，24小时有效
    """
    # 检查权限（只有团队管理员可以邀请）
    check_team_permission(db, str(current_user.id), team_id, [TeamRole.ADMIN])
    
    # 生成唯一邀请码
    invite_code = secrets.token_urlsafe(32)
    
    # 计算过期时间（24小时）
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # 创建邀请记录
    invitation = TeamInvitation(
        team_id=team_id,
        email=request.email.lower(),
        role=request.role,
        invite_code=invite_code,
        expires_at=expires_at
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    # 生成邀请链接
    invite_url = f"https://your-domain.com/register?invite={invite_code}&email={request.email}"
    
    logger.info(f"Team invitation created: team={team_id}, email={request.email}, role={request.role}")
    
    return {
        "success": True,
        "data": {
            "invitation_id": str(invitation.id),
            "invite_code": invite_code,
            "invite_url": invite_url,
            "expires_at": expires_at.isoformat(),
            "email": request.email,
            "role": request.role.value
        }
    }


# ==================== 获取团队邀请列表 ====================

@router.get("/{team_id}/invitations")
async def list_invitations(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取团队的邀请列表"""
    # 检查权限
    check_team_permission(db, str(current_user.id), team_id, [TeamRole.ADMIN])
    
    # 查询邀请记录
    invitations = db.query(TeamInvitation).filter(
        TeamInvitation.team_id == team_id
    ).all()
    
    result = []
    for inv in invitations:
        status = "pending"
        if inv.is_used:
            status = "joined"
        elif inv.expires_at < datetime.utcnow():
            status = "expired"
        
        result.append({
            "invitation_id": str(inv.id),
            "email": inv.email,
            "role": inv.role.value,
            "status": status,
            "created_at": inv.created_at.isoformat(),
            "expires_at": inv.expires_at.isoformat()
        })
    
    return {
        "success": True,
        "data": {
            "invitations": result,
            "total": len(result)
        }
    }


# ==================== 加入团队 ====================

@router.post("/join")
async def join_team(
    request: JoinTeamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    通过邀请码加入团队
    
    验证邀请码有效性和邮箱匹配性
    """
    # 查找邀请记录
    invitation = db.query(TeamInvitation).filter(
        TeamInvitation.invite_code == request.invite_code
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    # 检查是否已使用
    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invite code has already been used")
    
    # 检查是否过期
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite code has expired")
    
    # 检查邮箱是否匹配（如果邀请指定了邮箱）
    if invitation.email and current_user.email != invitation.email:
        raise HTTPException(status_code=403, detail="This invite is for a different email address")
    
    # 检查是否已是团队成员
    existing_member = db.query(TeamMember).filter(
        and_(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="You are already a member of this team")
    
    # 创建团队成员
    new_member = TeamMember(
        team_id=invitation.team_id,
        user_id=current_user.id,
        role=invitation.role
    )
    
    db.add(new_member)
    
    # 标记邀请为已使用
    invitation.is_used = True
    db.commit()
    
    # 获取团队信息
    team = db.query(Team).filter(Team.id == invitation.team_id).first()
    
    logger.info(f"User joined team: {current_user.email} -> {team.name}")
    
    return {
        "success": True,
        "data": {
            "team_id": str(team.id),
            "team_name": team.name,
            "role": invitation.role.value
        }
    }


# ==================== 获取团队成员列表 ====================

@router.get("/{team_id}/members")
async def list_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取团队成员列表"""
    # 检查权限（团队成员可查看）
    check_team_permission(db, str(current_user.id), team_id, [TeamRole.ADMIN, TeamRole.EDITOR, TeamRole.VIEWER])
    
    # 查询团队成员
    members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id
    ).all()
    
    result = []
    for member in members:
        user = member.user
        result.append({
            "user_id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": member.role.value,
            "joined_at": member.joined_at.isoformat()
        })
    
    return {
        "success": True,
        "data": {
            "members": result,
            "total": len(result)
        }
    }


# ==================== 修改成员角色 ====================

@router.patch("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: str,
    user_id: str,
    role: TeamRole,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改团队成员角色
    
    仅团队管理员可操作
    """
    # 检查权限
    check_team_permission(db, str(current_user.id), team_id, [TeamRole.ADMIN])
    
    # 查找成员
    member = db.query(TeamMember).filter(
        and_(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # 更新角色
    member.role = role
    db.commit()
    
    logger.info(f"Member role updated: team={team_id}, user={user_id}, role={role}")
    
    return {
        "success": True,
        "message": "Member role updated successfully"
    }


# ==================== 移除成员 ====================

@router.delete("/{team_id}/members/{user_id}")
async def remove_member(
    team_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    移除团队成员
    
    仅团队管理员可操作
    """
    # 检查权限
    check_team_permission(db, str(current_user.id), team_id, [TeamRole.ADMIN])
    
    # 查找成员
    member = db.query(TeamMember).filter(
        and_(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # 删除成员
    db.delete(member)
    db.commit()
    
    logger.info(f"Member removed: team={team_id}, user={user_id}")
    
    return {
        "success": True,
        "message": "Member removed successfully"
    }


# ==================== 删除团队 ====================

@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除团队
    
    仅团队创建者可操作
    """
    # 查找团队
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # 检查权限（仅创建者可删除）
    if str(team.creator_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only team creator can delete the team")
    
    # 删除团队（级联删除成员和邀请）
    db.delete(team)
    db.commit()
    
    logger.info(f"Team deleted: {team.name}")
    
    return {
        "success": True,
        "message": "Team deleted successfully"
    }
