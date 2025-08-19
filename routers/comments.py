from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.recruitment import Comment
from schemas.recruitment import (
    CommentCreate, 
    CommentResponse, 
    CommentUpdate,
    CommentWithReplies,
    ReplyCreate
)

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db)
):
    """
    댓글 작성 (일반 댓글 또는 대댓글)
    """
    # parent_comment_id는 스키마 validator에서 이미 처리됨 (0 -> None)
    parent_comment_id = comment.parent_comment_id
    
    # 부모 댓글이 있는 경우, 해당 댓글이 존재하는지 확인
    if parent_comment_id:
        parent_comment = db.query(Comment).filter(
            Comment.comment_id == parent_comment_id,
            Comment.recruitment_post_id == comment.recruitment_post_id
        ).first()
        
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="부모 댓글을 찾을 수 없습니다."
            )
    
    # 새로운 댓글 생성
    db_comment = Comment(
        recruitment_post_id=comment.recruitment_post_id,
        user_id=comment.user_id,
        content=comment.content,
        parent_comment_id=parent_comment_id
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return db_comment

@router.get("/post/{recruitment_post_id}", response_model=List[CommentWithReplies])
def get_comments_by_post(
    recruitment_post_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 게시글의 모든 댓글 조회 (대댓글 포함)
    """
    # 최상위 댓글만 조회 (parent_comment_id가 null인 것들)
    top_level_comments = db.query(Comment).filter(
        Comment.recruitment_post_id == recruitment_post_id,
        Comment.parent_comment_id.is_(None)
    ).order_by(Comment.created_at.desc()).all()
    
    # 각 최상위 댓글에 대댓글 정보 추가
    comments_with_replies = []
    for comment in top_level_comments:
        # 해당 댓글의 대댓글들 조회
        replies = db.query(Comment).filter(
            Comment.parent_comment_id == comment.comment_id
        ).order_by(Comment.created_at.asc()).all()
        
        comment_with_replies = CommentWithReplies(
            comment_id=comment.comment_id,
            recruitment_post_id=comment.recruitment_post_id,
            user_id=comment.user_id,
            parent_comment_id=comment.parent_comment_id,
            content=comment.content,
            created_at=comment.created_at,
            replies=replies
        )
        comments_with_replies.append(comment_with_replies)
    
    return comments_with_replies

@router.get("/{comment_id}/replies", response_model=List[CommentResponse])
def get_comment_replies(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 댓글의 대댓글 목록 조회
    """
    # 먼저 해당 댓글이 존재하는지 확인
    parent_comment = db.query(Comment).filter(Comment.comment_id == comment_id).first()
    
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없습니다."
        )
    
    # 대댓글들 조회
    replies = db.query(Comment).filter(
        Comment.parent_comment_id == comment_id
    ).order_by(Comment.created_at.asc()).all()
    
    return replies

@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db)
):
    """
    댓글 수정
    """
    comment = db.query(Comment).filter(Comment.comment_id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없습니다."
        )
    
    # 댓글 내용 업데이트
    comment.content = comment_update.content
    
    db.commit()
    db.refresh(comment)
    
    return comment

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    댓글 삭제 (대댓글이 있는 경우 함께 삭제)
    """
    comment = db.query(Comment).filter(Comment.comment_id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없습니다."
        )
    
    # 대댓글들도 함께 삭제
    replies = db.query(Comment).filter(Comment.parent_comment_id == comment_id).all()
    for reply in replies:
        db.delete(reply)
    
    # 원본 댓글 삭제
    db.delete(comment)
    db.commit()
    
    return None

@router.post("/{comment_id}/reply", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_reply(
    comment_id: int,
    reply_data: ReplyCreate,
    db: Session = Depends(get_db)
):
    """
    특정 댓글에 대댓글 작성
    """
    # 부모 댓글이 존재하는지 확인
    parent_comment = db.query(Comment).filter(Comment.comment_id == comment_id).first()
    
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="부모 댓글을 찾을 수 없습니다."
        )
    
    # 대댓글 생성 (recruitment_post_id는 부모 댓글에서 자동으로 가져옴)
    db_reply = Comment(
        recruitment_post_id=parent_comment.recruitment_post_id,
        user_id=reply_data.user_id,
        parent_comment_id=comment_id,
        content=reply_data.content
    )
    
    db.add(db_reply)
    db.commit()
    db.refresh(db_reply)
    
    return db_reply