from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from datetime import date
from database import get_db
from models.recruitment import RecruitmentPost, Application, ApplicationStatus
from models.contest import Contest, ContestFilter
from models.user import User
from schemas.recruitment import RecruitmentPostCreate, RecruitmentPostResponse, RecruitmentPostUpdate, RecruitmentPostList
from utils.auth import get_current_user

router = APIRouter(prefix="/recruitments", tags=["recruitments"])

@router.post("/create", response_model=RecruitmentPostResponse, status_code=status.HTTP_201_CREATED)
def create_recruitment_post(
    recruitment_post: RecruitmentPostCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 모집 게시글 생성
    """
    db_recruitment_post = RecruitmentPost(
        title=recruitment_post.title,
        content=recruitment_post.content,
        recruitment_count=recruitment_post.recruitment_count,
        contest_id=recruitment_post.contest_id,
        user_id=recruitment_post.user_id
    )
    
    db.add(db_recruitment_post)
    db.commit()
    db.refresh(db_recruitment_post)
    
    return db_recruitment_post

@router.get("/latest", response_model=List[RecruitmentPostList])
def get_latest_recruitment_posts(
    db: Session = Depends(get_db)
):
    """
    최신 모집 게시글 3개 조회
    """
    today = date.today()
    
    recruitment_posts = db.query(RecruitmentPost, Contest.due_date, Contest.name).join(
        Contest, RecruitmentPost.contest_id == Contest.contest_id
    ).filter(Contest.due_date >= today).order_by(RecruitmentPost.created_at.desc()).limit(3).all()
    
    # 결과를 RecruitmentPostList 형태로 변환
    result = []
    for post, due_date, contest_name in recruitment_posts:
        # accepted된 지원자 수 계산
        accepted_count = db.query(Application).filter(
            Application.recruitment_post_id == post.recruitment_post_id,
            Application.status == ApplicationStatus.accepted
        ).count()
        
        post_dict = {
            "recruitment_post_id": post.recruitment_post_id,
            "title": post.title,
            "content": post.content,
            "recruitment_count": post.recruitment_count,
            "contest_id": post.contest_id,
            "contest_name": contest_name,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "due_date": due_date,
            "accepted_count": accepted_count
        }
        result.append(RecruitmentPostList(**post_dict))
    
    return result

@router.get("/read", response_model=List[RecruitmentPostList])
def get_recruitment_posts(
    db: Session = Depends(get_db)
):
    """
    모든 모집 게시글 목록 조회 (페이징 없음)
    """
    # RecruitmentPost와 Contest를 조인하여 due_date와 contest_name 정보를 가져옴
    recruitment_posts = db.query(RecruitmentPost, Contest.due_date, Contest.name).join(
        Contest, RecruitmentPost.contest_id == Contest.contest_id
    ).all()
    
    # 결과를 RecruitmentPostList 형태로 변환
    result = []
    for post, due_date, contest_name in recruitment_posts:
        # accepted된 지원자 수 계산
        accepted_count = db.query(Application).filter(
            Application.recruitment_post_id == post.recruitment_post_id,
            Application.status == ApplicationStatus.accepted
        ).count()
        
        # contest_id에 해당하는 filter_id 조회 (contest당 하나의 filter)
        filter_result = db.query(ContestFilter.filter_id).filter(
            ContestFilter.contest_id == post.contest_id
        ).first()
        filter_id = filter_result[0] if filter_result else None
        
        post_dict = {
            "recruitment_post_id": post.recruitment_post_id,
            "title": post.title,
            "content": post.content,
            "recruitment_count": post.recruitment_count,
            "contest_id": post.contest_id,
            "contest_name": contest_name,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "due_date": due_date,
            "accepted_count": accepted_count,
            "filter_id": filter_id
        }
        result.append(RecruitmentPostList(**post_dict))
    
    return result

@router.get("/{recruitment_post_id}", response_model=RecruitmentPostResponse)
def get_recruitment_post(
    recruitment_post_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 모집 게시글 조회
    """
    # RecruitmentPost와 Contest를 조인하여 due_date와 contest_name 정보를 가져옴
    result = db.query(RecruitmentPost, Contest.due_date, Contest.name).join(
        Contest, RecruitmentPost.contest_id == Contest.contest_id
    ).filter(RecruitmentPost.recruitment_post_id == recruitment_post_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    post, due_date, contest_name = result
    
    # contest_id에 해당하는 filter_id 조회 
    filter_result = db.query(ContestFilter.filter_id).filter(
        ContestFilter.contest_id == post.contest_id
    ).first()
    filter_id = filter_result[0] if filter_result else None
    
    # accepted된 지원자 수 계산
    accepted_count = db.query(Application).filter(
        Application.recruitment_post_id == post.recruitment_post_id,
        Application.status == ApplicationStatus.accepted
    ).count()
    
    # 결과를 RecruitmentPostResponse 형태로 변환
    post_dict = {
        "recruitment_post_id": post.recruitment_post_id,
        "title": post.title,
        "content": post.content,
        "recruitment_count": post.recruitment_count,
        "contest_id": post.contest_id,
        "contest_name": contest_name,
        "user_id": post.user_id,
        "created_at": post.created_at,
        "due_date": due_date,
        "accepted_count": accepted_count,
        "filter_id": filter_id
    }
    
    return RecruitmentPostResponse(**post_dict)

@router.put("/update/{recruitment_post_id}", response_model=RecruitmentPostResponse)
def update_recruitment_post(
    recruitment_post_id: int,
    recruitment_post_update: RecruitmentPostUpdate,
    db: Session = Depends(get_db)
):
    """
    모집 게시글 수정
    """
    db_recruitment_post = db.query(RecruitmentPost).filter(
        RecruitmentPost.recruitment_post_id == recruitment_post_id
    ).first()
    
    if not db_recruitment_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    if db_recruitment_post.user_id != recruitment_post_update.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="게시글을 수정할 권한이 없습니다."
        )
    
    update_data = recruitment_post_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_recruitment_post, field, value)
    
    db.commit()
    db.refresh(db_recruitment_post)
    
    return db_recruitment_post

@router.delete("/delete/{recruitment_post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recruitment_post(
    recruitment_post_id: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    모집 게시글 삭제
    """
    db_recruitment_post = db.query(RecruitmentPost).filter(
        RecruitmentPost.recruitment_post_id == recruitment_post_id
    ).first()
    
    if not db_recruitment_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    if db_recruitment_post.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="게시글을 삭제할 권한이 없습니다."
        )
    
    db.delete(db_recruitment_post)
    db.commit()
    
    return None

@router.get("/contest/{contest_id}", response_model=List[RecruitmentPostList])
def get_recruitment_posts_by_contest(
    contest_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 콘테스트 모집 게시글 목록 조회
    """
    # RecruitmentPost와 Contest를 조인하여 due_date와 contest_name 정보를 가져옴
    recruitment_posts = db.query(RecruitmentPost, Contest.due_date, Contest.name).join(
        Contest, RecruitmentPost.contest_id == Contest.contest_id
    ).filter(RecruitmentPost.contest_id == contest_id).all()
    
    # 결과를 RecruitmentPostList 형태로 변환
    result = []
    for post, due_date, contest_name in recruitment_posts:
        post_dict = {
            "recruitment_post_id": post.recruitment_post_id,
            "title": post.title,
            "content": post.content,
            "recruitment_count": post.recruitment_count,
            "contest_id": post.contest_id,
            "contest_name": contest_name,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "due_date": due_date
        }
        result.append(RecruitmentPostList(**post_dict))
    
    return result

@router.get("/check-author/{recruitment_post_id}")
def check_post_author(
    recruitment_post_id: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    게시글 작성자 확인 (안드로이드에서 수정/삭제 버튼 표시 여부 결정)
    """
    recruitment_post = db.query(RecruitmentPost).filter(
        RecruitmentPost.recruitment_post_id == recruitment_post_id
    ).first()
    
    if not recruitment_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    
    is_author = recruitment_post.user_id == user_id
    
    return {
        "is_author": is_author,
        "post_user_id": recruitment_post.user_id,
        "request_user_id": user_id
    }

@router.get("/user/{user_id}/written", response_model=List[RecruitmentPostList])
def get_written_posts_by_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 사용자가 작성한 게시글 목록 조회
    """
    # RecruitmentPost와 Contest를 조인하여 due_date와 contest_name 정보를 가져옴
    recruitment_posts = db.query(RecruitmentPost, Contest.due_date, Contest.name).join(
        Contest, RecruitmentPost.contest_id == Contest.contest_id
    ).filter(RecruitmentPost.user_id == user_id).all()
    
    # 결과를 RecruitmentPostList 형태로 변환
    result = []
    for post, due_date, contest_name in recruitment_posts:
        post_dict = {
            "recruitment_post_id": post.recruitment_post_id,
            "title": post.title,
            "content": post.content,
            "recruitment_count": post.recruitment_count,
            "contest_id": post.contest_id,
            "contest_name": contest_name,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "due_date": due_date
        }
        result.append(RecruitmentPostList(**post_dict))
    
    return result