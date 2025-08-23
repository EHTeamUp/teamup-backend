from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.contest import Contest
from schemas.notification import FCMTokenUpdate
from utils.notification_service import NotificationService
from utils.auth import get_current_user
from datetime import datetime, timedelta
from models.recruitment import RecruitmentPost

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.put("/fcm-token")
def update_fcm_token(
        token_update: FCMTokenUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """FCM 토큰 업데이트"""
    try:
        success = NotificationService.update_fcm_token(
            db=db,
            user_id=current_user.user_id,
            fcm_token=token_update.fcm_token
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update FCM token"
            )

        return {"message": "FCM 토큰이 업데이트되었습니다."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/check-deadlines")
def check_deadlines(db: Session = Depends(get_db)):
    """공모전 마감일 확인 및 알림 전송 (수동 실행)"""
    try:
        # 마감일 알림 전송 (모든 관련 사용자에게)
        sent_results = NotificationService.check_and_send_deadline_reminders(db)
        
        total_sent = sum(sent_results.values()) if sent_results else 0

        return {
            "message": f"마감일 확인 완료",
            "notifications_sent": total_sent,
            "details": sent_results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )