from sqlalchemy.orm import Session
from models.notification import Notification, NotificationType
from models.user import User
from models.user_skill import UserSkill
from models.contest import Contest, ContestFilter
from utils.fcm_service import FCMService
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta

class NotificationService:
    """알림 서비스"""
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_data: Dict[str, Any] = None
    ) -> Notification:
        """알림 생성 및 FCM 전송"""
        try:
            # 알림 생성
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                related_data=json.dumps(related_data) if related_data else None
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # FCM 토큰으로 푸시 알림 전송
            user = db.query(User).filter(User.user_id == user_id).first()
            if user and user.fcm_token:
                FCMService.send_single_notification(
                    token=user.fcm_token,
                    title=title,
                    body=message,
                    data={
                        "notification_id": str(notification.notification_id),
                        "type": notification_type.value,
                        "related_data": json.dumps(related_data) if related_data else ""
                    }
                )
            
            return notification
            
        except Exception as e:
            db.rollback()
            print(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    def notify_new_contest(db: Session, contest: Contest) -> List[Notification]:
        """새로운 공모전 알림 전송"""
        notifications = []
        
        try:
            # 공모전의 필터(카테고리) 가져오기
            contest_filters = db.query(ContestFilter).filter(
                ContestFilter.contest_id == contest.contest_id
            ).all()
            
            filter_ids = [cf.filter_id for cf in contest_filters]
            
            if not filter_ids:
                return notifications
            
            # 해당 필터에 관심이 있는 사용자들의 스킬 찾기
            interested_users = db.query(UserSkill.user_id).filter(
                UserSkill.skill_id.in_(filter_ids)
            ).distinct().all()
            
            user_ids = [user[0] for user in interested_users]
            
            # 각 사용자에게 알림 전송
            for user_id in user_ids:
                notification = NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type=NotificationType.NEW_CONTEST,
                    title="새로운 공모전이 등록되었습니다!",
                    message=f"'{contest.name}' 공모전이 등록되었습니다. 확인해보세요!",
                    related_data={
                        "contest_id": contest.contest_id,
                        "contest_name": contest.name,
                        "due_date": contest.due_date.isoformat()
                    }
                )
                if notification:
                    notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            print(f"Error notifying new contest: {e}")
            return notifications
    
    @staticmethod
    def notify_application_response(
        db: Session, 
        application_user_id: str, 
        recruitment_post_title: str,
        status: str
    ) -> Notification:
        """지원 응답 알림 전송"""
        status_text = "수락" if status == "accepted" else "거절"
        
        return NotificationService.create_notification(
            db=db,
            user_id=application_user_id,
            notification_type=NotificationType.APPLICATION_RESPONSE,
            title="팀 지원 결과",
            message=f"'{recruitment_post_title}' 팀 지원이 {status_text}되었습니다.",
            related_data={
                "recruitment_post_title": recruitment_post_title,
                "status": status
            }
        )
    
    @staticmethod
    def notify_new_comment(
        db: Session,
        recruitment_post_user_id: str,
        comment_user_name: str,
        recruitment_post_title: str,
        comment_content: str
    ) -> Notification:
        """새 댓글 알림 전송"""
        return NotificationService.create_notification(
            db=db,
            user_id=recruitment_post_user_id,
            notification_type=NotificationType.NEW_COMMENT,
            title="새 댓글이 달렸습니다",
            message=f"'{recruitment_post_title}' 게시글에 {comment_user_name}님이 댓글을 남겼습니다.",
            related_data={
                "recruitment_post_title": recruitment_post_title,
                "comment_user_name": comment_user_name,
                "comment_content": comment_content[:50] + "..." if len(comment_content) > 50 else comment_content
            }
        )
    
    @staticmethod
    def notify_new_reply(
        db: Session,
        parent_comment_user_id: str,
        reply_user_name: str,
        recruitment_post_title: str,
        reply_content: str
    ) -> Notification:
        """새 대댓글 알림 전송"""
        return NotificationService.create_notification(
            db=db,
            user_id=parent_comment_user_id,
            notification_type=NotificationType.NEW_REPLY,
            title="새 대댓글이 달렸습니다",
            message=f"'{recruitment_post_title}' 게시글에 {reply_user_name}님이 대댓글을 남겼습니다.",
            related_data={
                "recruitment_post_title": recruitment_post_title,
                "reply_user_name": reply_user_name,
                "reply_content": reply_content[:50] + "..." if len(reply_content) > 50 else reply_content
            }
        )
    
    @staticmethod
    def notify_contest_deadline(db: Session, contest: Contest) -> List[Notification]:
        """공모전 마감일 알림 전송"""
        notifications = []
        
        try:
            # 공모전에 지원한 사용자들 찾기 (지원 모델이 있다면)
            # 여기서는 간단히 모든 활성 사용자에게 전송
            active_users = db.query(User).filter(User.is_deleted == False).all()
            
            for user in active_users:
                notification = NotificationService.create_notification(
                    db=db,
                    user_id=user.user_id,
                    notification_type=NotificationType.CONTEST_DEADLINE,
                    title="공모전 마감일 알림",
                    message=f"'{contest.name}' 공모전이 {contest.due_date.strftime('%Y년 %m월 %d일')}에 마감됩니다!",
                    related_data={
                        "contest_id": contest.contest_id,
                        "contest_name": contest.name,
                        "due_date": contest.due_date.isoformat()
                    }
                )
                if notification:
                    notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            print(f"Error notifying contest deadline: {e}")
            return notifications
    
    @staticmethod
    def update_fcm_token(db: Session, user_id: str, fcm_token: str) -> bool:
        """사용자의 FCM 토큰 업데이트"""
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                user.fcm_token = fcm_token
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            print(f"Error updating FCM token: {e}")
            return False
