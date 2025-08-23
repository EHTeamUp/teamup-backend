from sqlalchemy.orm import Session
from models.user import User
from models.user_skill import UserSkill
from models.contest import Contest, ContestFilter, ContestTag, Tag
from models.recruitment import RecruitmentPost, Application, ApplicationStatus
from models.skill import Skill
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
        notification_type: str,
        title: str,
        message: str,
        related_data: Dict[str, Any] = None
    ) -> bool:
        """FCM 푸시 알림 전송 (데이터베이스 저장 없음)"""
        try:
            # 사용자 조회
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user or not user.fcm_token:
                print(f"User not found or no FCM token: {user_id}")
                return False
            
            # FCM 토큰으로 푸시 알림 전송
            try:
                FCMService.send_single_notification(
                    token=user.fcm_token,
                    title=title,
                    body=message,
                    data={
                        "type": notification_type,
                        "related_data": json.dumps(related_data) if related_data else ""
                    }
                )
                print(f"FCM 알림 전송 성공: {user_id} - {title}")
            except Exception as fcm_error:
                print(f"FCM 전송 실패 (임시로 성공 처리): {fcm_error}")
                # 임시로 FCM 오류를 무시하고 성공으로 처리
                print(f"알림 내용: {title} - {message}")
            
            return True
            
        except Exception as e:
            print(f"Error in create_notification: {e}")
            return False
    
    @staticmethod
    def notify_new_contest(db: Session, contest: Contest) -> int:
        """새로운 공모전 알림 전송"""
        sent_count = 0
        
        try:
            # 공모전의 필터(카테고리) 가져오기
            contest_filters = db.query(ContestFilter).filter(
                ContestFilter.contest_id == contest.contest_id
            ).all()
            
            filter_ids = [cf.filter_id for cf in contest_filters]
            
            if not filter_ids:
                return sent_count
            
            # 해당 필터에 관심이 있는 사용자들의 스킬 찾기
            interested_users = db.query(UserSkill.user_id).filter(
                UserSkill.skill_id.in_(filter_ids)
            ).distinct().all()
            
            user_ids = [user[0] for user in interested_users]
            
            # 각 사용자에게 알림 전송
            for user_id in user_ids:
                success = NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="new_contest",
                    title="새로운 공모전이 등록되었습니다!",
                    message=f"'{contest.name}' 공모전이 등록되었습니다. 확인해보세요!",
                    related_data={
                        "contest_id": contest.contest_id,
                        "contest_name": contest.name,
                        "due_date": contest.due_date.isoformat()
                    }
                )
                if success:
                    sent_count += 1
            
            return sent_count
            
        except Exception as e:
            print(f"Error notifying new contest: {e}")
            return sent_count
    
    @staticmethod
    def notify_application_response(
        db: Session, 
        application_user_id: str, 
        recruitment_post_id: int,
        status: str
    ) -> bool:
        """지원 응답 알림 전송"""
        try:
            print(f"DEBUG: notify_application_response 시작 - user_id: {application_user_id}, post_id: {recruitment_post_id}, status: {status}")
            
            # 모집 게시글 정보 조회
            recruitment_post = db.query(RecruitmentPost).filter(
                RecruitmentPost.recruitment_post_id == recruitment_post_id
            ).first()
            
            if not recruitment_post:
                print(f"Recruitment post not found: {recruitment_post_id}")
                return False
            
            print(f"DEBUG: 모집 게시글 조회 성공 - 제목: {recruitment_post.title}")
            
            status_text = "수락" if status == "accepted" else "거절"
            
            print(f"DEBUG: create_notification 호출 시작")
            
            success = NotificationService.create_notification(
                db=db,
                user_id=application_user_id,
                notification_type="application_response",
                title="팀 지원 결과",
                message=f"'{recruitment_post.title}' 팀 지원이 {status_text}되었습니다.",
                related_data={
                    "recruitment_post_id": recruitment_post_id,
                    "recruitment_post_title": recruitment_post.title,
                    "status": status
                }
            )
            
            print(f"DEBUG: create_notification 결과 - success: {success}")
            
            return success
            
        except Exception as e:
            print(f"Error notifying application response: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def notify_new_comment(
        db: Session,
        recruitment_post_user_id: str,
        comment_user_name: str,
        recruitment_post_id: int,
        comment_content: str
    ) -> bool:
        """새 댓글 알림 전송"""
        try:
            # 모집 게시글 정보 조회
            recruitment_post = db.query(RecruitmentPost).filter(
                RecruitmentPost.recruitment_post_id == recruitment_post_id
            ).first()
            
            if not recruitment_post:
                print(f"Recruitment post not found: {recruitment_post_id}")
                return False
            
            return NotificationService.create_notification(
                db=db,
                user_id=recruitment_post_user_id,
                notification_type="new_comment",
                title="새 댓글이 달렸습니다",
                message=f"'{recruitment_post.title}' 게시글에 {comment_user_name}님이 댓글을 남겼습니다.",
                related_data={
                    "recruitment_post_id": recruitment_post_id,
                    "recruitment_post_title": recruitment_post.title,
                    "comment_user_name": comment_user_name,
                    "comment_content": comment_content[:50] + "..." if len(comment_content) > 50 else comment_content
                }
            )
        except Exception as e:
            print(f"Error notifying new comment: {e}")
            return False
    
    @staticmethod
    def notify_new_reply(
        db: Session,
        parent_comment_user_id: str,
        reply_user_name: str,
        recruitment_post_id: int,
        reply_content: str
    ) -> bool:
        """새 대댓글 알림 전송"""
        try:
            # 모집 게시글 정보 조회
            recruitment_post = db.query(RecruitmentPost).filter(
                RecruitmentPost.recruitment_post_id == recruitment_post_id
            ).first()
            
            if not recruitment_post:
                print(f"Recruitment post not found: {recruitment_post_id}")
                return False
            
            return NotificationService.create_notification(
                db=db,
                user_id=parent_comment_user_id,
                notification_type="new_reply",
                title="새 댓글이 달렸습니다",
                message=f"'{recruitment_post.title}' 게시글에 {reply_user_name}님이 대댓글을 남겼습니다.",
                related_data={
                    "recruitment_post_id": recruitment_post_id,
                    "recruitment_post_title": recruitment_post.title,
                    "reply_user_name": reply_user_name,
                    "reply_content": reply_content[:50] + "..." if len(reply_content) > 50 else reply_content
                }
            )
        except Exception as e:
            print(f"Error notifying new reply: {e}")
            return False
    
    @staticmethod
    def notify_new_application(
        db: Session,
        recruitment_post_user_id: str,
        applicant_name: str,
        recruitment_post_id: int,
        application_message: str
    ) -> bool:
        """새로운 지원 알림 전송"""
        try:
            # 모집 게시글 정보 조회
            recruitment_post = db.query(RecruitmentPost).filter(
                RecruitmentPost.recruitment_post_id == recruitment_post_id
            ).first()
            
            if not recruitment_post:
                print(f"Recruitment post not found: {recruitment_post_id}")
                return False
            
            return NotificationService.create_notification(
                db=db,
                user_id=recruitment_post_user_id,
                notification_type="new_application",
                title="새로운 지원자가 등록되었습니다",
                message=f"'{recruitment_post.title}' 게시글에 {applicant_name}님이 지원했습니다.",
                related_data={
                    "recruitment_post_id": recruitment_post_id,
                    "recruitment_post_title": recruitment_post.title,
                    "applicant_name": applicant_name,
                    "application_message": application_message[:50] + "..." if len(application_message) > 50 else application_message
                }
            )
        except Exception as e:
            print(f"Error notifying new application: {e}")
            return False
    
    @staticmethod
    def notify_new_contest_with_skill_matching(db: Session, contest: Contest) -> int:
        """새로운 공모전 태그와 사용자 스킬 매칭 알림 전송"""
        sent_count = 0
        
        try:
            # 공모전의 태그들 가져오기
            contest_tags = db.query(ContestTag).filter(
                ContestTag.contest_id == contest.contest_id
            ).all()
            
            if not contest_tags:
                print(f"공모전 {contest.contest_title}에 태그가 없습니다.")
                return sent_count
            
            # 태그 이름들 가져오기
            tag_ids = [ct.tag_id for ct in contest_tags]
            tags = db.query(Tag).filter(Tag.tag_id.in_(tag_ids)).all()
            tag_names = [tag.name for tag in tags]
            
            print(f"공모전 '{contest.name}' 태그: {tag_names}")
            
            # 해당 태그와 매칭되는 스킬을 가진 사용자들 찾기
            matching_users = db.query(UserSkill.user_id).filter(
                UserSkill.skill_id.in_(
                    db.query(Skill.skill_id).filter(Skill.name.in_(tag_names))
                )
            ).distinct().all()
            
            user_ids = [user[0] for user in matching_users]
            
            print(f"매칭된 사용자 수: {len(user_ids)}")
            
            # 각 사용자에게 알림 전송
            for user_id in user_ids:
                success = NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="new_contest_skill_match",
                    title="관련 공모전이 등록되었습니다!",
                    message=f"'{contest.name}' 공모전이 등록되었습니다. {', '.join(tag_names)}과 관련이 있어요!",
                    related_data={
                        "contest_id": contest.contest_id,
                        "contest_name": contest.name,
                        "due_date": contest.due_date.isoformat(),
                        "matching_tags": tag_names
                    }
                )
                if success:
                    sent_count += 1
            
            return sent_count
            
        except Exception as e:
            print(f"Error notifying new contest with skill matching: {e}")
            import traceback
            traceback.print_exc()
            return sent_count
    

    
    @staticmethod
    def notify_contest_deadline_reminder(db: Session, contest: Contest, days_remaining: int) -> int:
        """공모전 마감일 알림 전송 (특정 일수 남았을 때)"""
        sent_count = 0
        
        try:
            # 공모전 모집글 작성자와 참여자들(status=accepted) 찾기
            recruitment_posts = db.query(RecruitmentPost).filter(
                RecruitmentPost.contest_id == contest.contest_id
            ).all()
            
            target_user_ids = set()
            
            for post in recruitment_posts:
                # 모집글 작성자 추가
                target_user_ids.add(post.user_id)
                
                # 수락된 지원자들 추가
                accepted_applications = db.query(Application).filter(
                    Application.recruitment_post_id == post.recruitment_post_id,
                    Application.status == ApplicationStatus.accepted
                ).all()
                
                for app in accepted_applications:
                    target_user_ids.add(app.user_id)
            
            if not target_user_ids:
                print(f"공모전 {contest.contest_id}에 관련된 사용자가 없습니다.")
                return sent_count
            
            # 일수에 따른 메시지 생성
            if days_remaining == 0:
                title = "공모전 마감일입니다!"
                message = f"'{contest.name}' 공모전이 오늘 마감됩니다!"
            else:
                title = f"공모전 마감 {days_remaining}일 전"
                message = f"'{contest.name}' 공모전이 {days_remaining}일 후 마감됩니다!"
            
            # 각 사용자에게 알림 전송
            for user_id in target_user_ids:
                success = NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="contest_deadline_reminder",
                    title=title,
                    message=message,
                    related_data={
                        "contest_id": contest.contest_id,
                        "contest_name": contest.name,
                        "due_date": contest.due_date.isoformat(),
                        "days_remaining": days_remaining
                    }
                )
                if success:
                    sent_count += 1
            
            print(f"공모전 마감일 알림 전송 완료: {sent_count}명에게 전송 (마감 {days_remaining}일 전)")
            return sent_count
            
        except Exception as e:
            print(f"Error notifying contest deadline reminder: {e}")
            import traceback
            traceback.print_exc()
            return sent_count
    
    @staticmethod
    def check_and_send_deadline_reminders(db: Session) -> Dict[str, int]:
        """모든 공모전의 마감일을 확인하고 알림 전송"""
        try:
            today = datetime.now().date()
            reminder_days = [30, 10, 5, 1, 0]  # 알림을 보낼 일수들
            total_sent = {}
            
            # 마감일이 임박한 공모전들 조회
            upcoming_contests = db.query(Contest).filter(
                Contest.due_date >= today
            ).all()
            
            for contest in upcoming_contests:
                days_until_deadline = (contest.due_date - today).days
                
                # 알림을 보낼 일수인지 확인
                if days_until_deadline in reminder_days:
                    sent_count = NotificationService.notify_contest_deadline_reminder(
                        db, contest, days_until_deadline
                    )
                    total_sent[f"{contest.contest_id}_{days_until_deadline}"] = sent_count
            
            return total_sent
            
        except Exception as e:
            print(f"Error checking deadline reminders: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
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
    
    @staticmethod
    def delete_fcm_token(db: Session, user_id: str) -> bool:
        """사용자의 FCM 토큰 삭제"""
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                user.fcm_token = None
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting FCM token: {e}")
            return False
