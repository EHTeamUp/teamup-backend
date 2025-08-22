from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.recruitment import Application, ApplicationStatus, RecruitmentPost
from models.user import User
from schemas.recruitment import (
    ApplicationCreate, 
    ApplicationResponse, 
    ApplicationStatusUpdate, 
    ApplicationReject,
    UserActivityResponse,
    UserActivityPost,
    UserActivityApplication
)
from utils.notification_service import NotificationService

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    모집 게시글 지원
    """
    # 이미 지원했는지 확인
    existing_application = db.query(Application).filter(
        Application.recruitment_post_id == application.recruitment_post_id,
        Application.user_id == application.user_id
    ).first()
    
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 지원한 게시글입니다."
        )
    
    # 새로운 지원 생성
    db_application = Application(
        recruitment_post_id=application.recruitment_post_id,
        user_id=application.user_id,
        message=application.message,
        status=ApplicationStatus.pending
    )
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    return db_application

@router.put("/accept", status_code=status.HTTP_200_OK)
def accept_applications(
    status_update: ApplicationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    지원자 수락
    """
    # 해당 게시글의 지원들을 찾아서 status를 accepted로 변경
    applications = db.query(Application).filter(
        Application.recruitment_post_id == status_update.recruitment_post_id,
        Application.user_id.in_(status_update.user_ids)
    ).all()
    
    if not applications:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당하는 지원을 찾을 수 없습니다."
        )
    
    # 게시글 정보 가져오기
    recruitment_post = db.query(RecruitmentPost).filter(
        RecruitmentPost.recruitment_post_id == status_update.recruitment_post_id
    ).first()
    
    for application in applications:
        application.status = ApplicationStatus.accepted
        
        # 지원자에게 수락 알림 전송
        if recruitment_post:
            NotificationService.notify_application_response(
                db=db,
                application_user_id=application.user_id,
                recruitment_post_id=status_update.recruitment_post_id,
                status="accepted"
            )
    
    db.commit()
    
    return {"message": f"{len(applications)}명의 지원자가 수락되었습니다."}

@router.put("/reject", status_code=status.HTTP_200_OK)
def reject_application(
    reject_data: ApplicationReject,
    db: Session = Depends(get_db)
):
    """
    특정 지원자 거절
    """
    application = db.query(Application).filter(
        Application.recruitment_post_id == reject_data.recruitment_post_id,
        Application.user_id == reject_data.user_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당하는 지원을 찾을 수 없습니다."
        )
    
    # 게시글 정보 가져오기
    recruitment_post = db.query(RecruitmentPost).filter(
        RecruitmentPost.recruitment_post_id == reject_data.recruitment_post_id
    ).first()
    
    application.status = ApplicationStatus.rejected
    
    # 지원자에게 거절 알림 전송
    if recruitment_post:
        NotificationService.notify_application_response(
            db=db,
            application_user_id=application.user_id,
            recruitment_post_id=reject_data.recruitment_post_id,
            status="rejected"
        )
    
    db.commit()
    
    return {"message": "지원이 거절되었습니다."}

@router.get("/post/{recruitment_post_id}", response_model=List[ApplicationResponse])
def get_applications_by_post(
    recruitment_post_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 게시글의 모든 지원 목록 조회 - 지원자 목록 (accepted, pending만)
    """
    applications = db.query(Application).filter(
        Application.recruitment_post_id == recruitment_post_id,
        Application.status.in_([ApplicationStatus.accepted, ApplicationStatus.pending])
    ).all()
    
    return applications

@router.get("/post/{recruitment_post_id}/accepted", response_model=List[ApplicationResponse])
def get_accepted_applications_by_post(
    recruitment_post_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 게시글의 수락된 지원자 목록 조회 - 수락된 지원자만
    """
    accepted_applications = db.query(Application).filter(
        Application.recruitment_post_id == recruitment_post_id,
        Application.status == ApplicationStatus.accepted
    ).all()
    
    return accepted_applications

@router.get("/user/{user_id}/activity", response_model=UserActivityResponse)
def get_user_activity(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 작성 게시글과 수락된 지원 목록을 함께 조회 - 내 참여 공모전 목록
    """
    from models.recruitment import RecruitmentPost

    # 사용자가 작성한 게시글 목록
    written_posts = db.query(RecruitmentPost).filter(
        RecruitmentPost.user_id == user_id
    ).all()
    
    # 사용자가 지원하고 수락된 지원 목록
    accepted_applications = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status == ApplicationStatus.accepted
    ).all()
    
    return UserActivityResponse(
        written_posts=[
            UserActivityPost(
                recruitment_post_id=post.recruitment_post_id,
                title=post.title,
                content=post.content,
                recruitment_count=post.recruitment_count,
                contest_id=post.contest_id,
                user_id=post.user_id,
                created_at=post.created_at
            ) for post in written_posts
        ],
        accepted_applications=[
            UserActivityApplication(
                application_id=app.application_id,
                recruitment_post_id=app.recruitment_post_id,
                user_id=app.user_id,
                message=app.message,
                status=app.status
            ) for app in accepted_applications
        ]
    )

@router.get("/user/{user_id}/accepted", response_model=List[ApplicationResponse])
def get_user_accepted_applications(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 수락된 지원 목록만 조회 - 내가 수락받은 지원들
    """
    accepted_applications = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status == ApplicationStatus.accepted
    ).all()
    
    return accepted_applications
