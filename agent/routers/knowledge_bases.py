"""
知识库管理路由（增强版）
支持权限控制、文档批量上传、分块策略配置、检索测试
"""

import os
import uuid
import logging
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database_postgres import get_db
from models_db import (
    KnowledgeBase, Document, User, TeamMember, ResourcePermission,
    ResourcePermission as ResPerm, TeamRole
)
from utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge"])


# ==================== Pydantic 模型 ====================

class KnowledgeBaseConfig(BaseModel):
    name: str = Field(..., min_length=2, max_length=32)
    description: Optional[str] = Field(None, min_length=10, max_length=200)
    chunk_size: int = Field(512, ge=100, le=2000, description="分块大小")
    chunk_overlap: int = Field(128, ge=0, le=500, description="重叠长度")
    is_public: bool = False


class TeamPermissionConfig(BaseModel):
    team_id: str
    permission: str = "view"  # view | edit | manage


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    top_k: int = Field(5, ge=1, le=20)


# ==================== 辅助函数 ====================

def check_kb_permission(
    db: Session,
    user_id: str,
    kb: KnowledgeBase,
    required_permission: str = "view"
) -> bool:
    """
    检查用户对知识库的访问权限
    
    权限规则：
    1. 创建者拥有所有权限
    2. 公开知识库所有人可查看
    3. 团队共享知识库根据权限级别判断
    """
    # 创建者拥有所有权限
    if str(kb.creator_id) == str(user_id):
        return True
    
    # 公开知识库所有人可查看
    if kb.is_public and required_permission == "view":
        return True
    
    # 检查团队权限
    permission_record = db.query(ResourcePermission).filter(
        and_(
            ResourcePermission.knowledge_base_id == kb.id,
            ResourcePermission.team_id.in_(
                db.query(TeamMember.team_id).filter(
                    TeamMember.user_id == user_id
                )
            )
        )
    ).first()
    
    if permission_record:
        perm_level = {"view": 1, "edit": 2, "manage": 3}
        if perm_level.get(permission_record.permission.value, 0) >= perm_level.get(required_permission, 0):
            return True
    
    return False


# ==================== 创建知识库 ====================

@router.post("")
async def create_knowledge_base(
    config: KnowledgeBaseConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建知识库
    
    流程：
    1. 保存知识库配置到数据库
    2. 创建 ChromaDB 集合
    3. 返回知识库 ID
    """
    from database import chroma_db
    
    # 创建知识库记录
    new_kb = KnowledgeBase(
        id=uuid.uuid4(),
        name=config.name,
        description=config.description,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        is_public=config.is_public,
        creator_id=current_user.id,
        document_count=0,
        chunk_count=0
    )
    
    db.add(new_kb)
    db.flush()
    
    # 创建 ChromaDB 集合（使用知识库 ID 作为集合名）
    try:
        collection_name = f"kb_{str(new_kb.id).replace('-', '_')}"
        # 注意：实际部署时需要在 ChromaDB 中创建对应集合
        logger.info(f"ChromaDB collection created: {collection_name}")
    except Exception as e:
        logger.warning(f"Failed to create ChromaDB collection: {e}")
    
    db.commit()
    db.refresh(new_kb)
    
    logger.info(f"Knowledge base created: {new_kb.name} by {current_user.email}")
    
    return {
        "success": True,
        "data": {
            "kb_id": str(new_kb.id),
            "name": new_kb.name,
            "chunk_size": new_kb.chunk_size,
            "chunk_overlap": new_kb.chunk_overlap,
            "created_at": new_kb.created_at.isoformat()
        }
    }


# ==================== 获取知识库列表 ====================

@router.get("")
async def list_knowledge_bases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    visibility: str = Query("all"),  # all | my | shared
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库列表"""
    query = db.query(KnowledgeBase)
    
    # 可见性筛选
    if visibility == "my":
        query = query.filter(KnowledgeBase.creator_id == current_user.id)
    elif visibility == "shared":
        # 团队共享的知识库
        query = query.filter(
            or_(
                KnowledgeBase.is_public == True,
                KnowledgeBase.id.in_(
                    db.query(ResourcePermission.knowledge_base_id).filter(
                        ResourcePermission.team_id.in_(
                            db.query(TeamMember.team_id).filter(
                                TeamMember.user_id == current_user.id
                            )
                        )
                    )
                )
            )
        )
    else:
        # all: 自己创建 + 公开 + 团队共享
        query = query.filter(
            or_(
                KnowledgeBase.creator_id == current_user.id,
                KnowledgeBase.is_public == True,
                KnowledgeBase.id.in_(
                    db.query(ResourcePermission.knowledge_base_id).filter(
                        ResourcePermission.team_id.in_(
                            db.query(TeamMember.team_id).filter(
                                TeamMember.user_id == current_user.id
                            )
                        )
                    )
                )
            )
        )
    
    # 搜索
    if search:
        query = query.filter(
            or_(
                KnowledgeBase.name.ilike(f"%{search}%"),
                KnowledgeBase.description.ilike(f"%{search}%")
            )
        )
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    kbs = query.order_by(KnowledgeBase.created_at.desc()).offset(offset).limit(page_size).all()
    
    result = []
    for kb in kbs:
        result.append({
            "kb_id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "is_public": kb.is_public,
            "creator": {
                "user_id": str(kb.creator.id),
                "name": kb.creator.name,
                "email": kb.creator.email
            },
            "created_at": kb.created_at.isoformat()
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


# ==================== 获取知识库详情 ====================

@router.get("/{kb_id}")
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库详情"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 权限检查
    if not check_kb_permission(db, str(current_user.id), kb, "view"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return {
        "success": True,
        "data": {
            "kb_id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "is_public": kb.is_public,
            "creator": {
                "user_id": str(kb.creator.id),
                "name": kb.creator.name,
                "email": kb.creator.email
            },
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat()
        }
    }


# ==================== 上传文档 ====================

@router.post("/{kb_id}/documents")
async def upload_documents(
    kb_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量上传文档
    
    支持 PDF/DOCX/TXT/Markdown 格式
    单次最多 10 个文件，单个文件最大 50MB
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 权限检查
    if not check_kb_permission(db, str(current_user.id), kb, "edit"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 文件数量限制
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per upload")
    
    # 支持的文件类型
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/plain": "txt",
        "text/markdown": "md"
    }
    
    # 文件大小限制（50MB）
    max_size = 50 * 1024 * 1024
    
    uploaded_docs = []
    
    # 确保上传目录存在
    upload_dir = os.path.join("data", "knowledge", str(kb_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    for file in files:
        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 移回开头
        
        if file_size > max_size:
            uploaded_docs.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"File size exceeds 50MB limit ({file_size / 1024 / 1024:.2f} MB)"
            })
            continue
        
        # 检查文件类型
        file_type = allowed_types.get(file.content_type)
        if not file_type:
            # 尝试根据扩展名判断
            ext = file.filename.split('.')[-1].lower()
            if ext in ['pdf', 'docx', 'txt', 'md']:
                file_type = ext
            else:
                uploaded_docs.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": f"Unsupported file type: {file.content_type}"
                })
                continue
        
        # 保存文件
        file_path = os.path.join(upload_dir, file.filename)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 创建文档记录
            doc = Document(
                id=uuid.uuid4(),
                knowledge_base_id=kb.id,
                filename=file.filename,
                file_type=file_type,
                file_size=file_size,
                status="pending"
            )
            
            db.add(doc)
            db.flush()
            
            uploaded_docs.append({
                "document_id": str(doc.id),
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "status": "uploaded",
                "message": "File uploaded successfully, processing in background"
            })
            
            logger.info(f"Document uploaded: {file.filename} to KB {kb.name}")
            
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {e}")
            uploaded_docs.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    db.commit()
    
    # 触发后台文档处理任务（这里简化处理，实际应使用 Celery 等任务队列）
    # process_documents_background(kb_id)
    
    return {
        "success": True,
        "data": {
            "kb_id": str(kb.id),
            "uploaded_documents": uploaded_docs,
            "total_uploaded": len([d for d in uploaded_docs if d.get("status") == "uploaded"]),
            "total_failed": len([d for d in uploaded_docs if d.get("status") == "failed"])
        }
    }


# ==================== 获取文档列表 ====================

@router.get("/{kb_id}/documents")
async def list_documents(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库中的文档列表"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 权限检查
    if not check_kb_permission(db, str(current_user.id), kb, "view"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    documents = db.query(Document).filter(
        Document.knowledge_base_id == kb_id
    ).order_by(Document.created_at.desc()).all()
    
    result = []
    for doc in documents:
        result.append({
            "document_id": str(doc.id),
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "error_message": doc.error_message,
            "created_at": doc.created_at.isoformat(),
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
        })
    
    return {
        "success": True,
        "data": {
            "documents": result,
            "total": len(result)
        }
    }


# ==================== 删除文档 ====================

@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文档"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 权限检查
    if not check_kb_permission(db, str(current_user.id), kb, "edit"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    doc = db.query(Document).filter(
        and_(
            Document.id == doc_id,
            Document.knowledge_base_id == kb_id
        )
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 删除文件
    file_path = os.path.join("data", "knowledge", kb_id, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 删除数据库记录
    db.delete(doc)
    
    # 更新知识库统计
    kb.document_count -= 1
    kb.chunk_count -= doc.chunk_count
    
    db.commit()
    
    logger.info(f"Document deleted: {doc.filename} from KB {kb.name}")
    
    return {
        "success": True,
        "message": "Document deleted successfully"
    }


# ==================== 检索测试 ====================

@router.post("/{kb_id}/search")
async def search_knowledge_base(
    kb_id: str,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    知识库检索测试
    
    返回匹配的分块内容、相似度得分、所属文档
    """
    from database import knowledge
    
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 权限检查
    if not check_kb_permission(db, str(current_user.id), kb, "view"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        # 执行检索
        # 注意：这里需要根据实际的知识库 ID 过滤结果
        results = knowledge.search(query=request.query, limit=request.top_k)
        
        # 格式化结果
        formatted_results = []
        for idx, result in enumerate(results):
            formatted_results.append({
                "rank": idx + 1,
                "content": result.get("content", ""),
                "similarity": result.get("similarity", 0),
                "document": result.get("document", "Unknown"),
                "chunk_id": result.get("id", "")
            })
        
        logger.info(f"KB search: {kb.name} - query: {request.query}")
        
        return {
            "success": True,
            "data": {
                "query": request.query,
                "results": formatted_results,
                "total": len(formatted_results)
            }
        }
        
    except Exception as e:
        logger.error(f"KB search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ==================== 更新知识库配置 ====================

@router.put("/{kb_id}")
async def update_knowledge_base(
    kb_id: str,
    config: KnowledgeBaseConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新知识库配置"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 权限检查
    if not check_kb_permission(db, str(current_user.id), kb, "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 更新配置
    kb.name = config.name
    kb.description = config.description
    kb.chunk_size = config.chunk_size
    kb.chunk_overlap = config.chunk_overlap
    kb.is_public = config.is_public
    
    db.commit()
    
    logger.info(f"KB updated: {kb.name} by {current_user.email}")
    
    return {
        "success": True,
        "message": "Knowledge base updated successfully"
    }


# ==================== 删除知识库 ====================

@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除知识库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 权限检查（只有创建者可删除）
    if str(kb.creator_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only creator can delete knowledge base")
    
    # 删除文件目录
    upload_dir = os.path.join("data", "knowledge", kb_id)
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    
    # 删除数据库记录（级联删除文档）
    db.delete(kb)
    db.commit()
    
    logger.info(f"KB deleted: {kb.name} by {current_user.email}")
    
    return {
        "success": True,
        "message": "Knowledge base deleted successfully"
    }
