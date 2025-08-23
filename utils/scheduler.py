"""
공모전 마감일 알림 스케줄러
매일 마감일이 임박한 공모전에 대해 알림을 전송합니다.
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 import 경로에 추가
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_CURRENT_DIR)
if _BACKEND_ROOT not in sys.path:
    sys.path.append(_BACKEND_ROOT)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeadlineReminderScheduler:
    """공모전 마감일 알림 스케줄러"""
    
    def __init__(self):
        pass
    
    def run_daily_reminders(self):
        """일일 마감일 알림 실행"""
        try:
            logger.info("공모전 마감일 알림 스케줄러 시작")
            
            from utils.notification_service import NotificationService
            from database import SessionLocal
            
            db = SessionLocal()
            try:
                # 마감일 알림 전송
                sent_results = NotificationService.check_and_send_deadline_reminders(db)
                
                if sent_results:
                    logger.info(f"마감일 알림 전송 완료: {len(sent_results)}건")
                    for key, count in sent_results.items():
                        contest_id, days = key.split('_')
                        logger.info(f"  - 공모전 {contest_id}: 마감 {days}일 전 알림 {count}명에게 전송")
                else:
                    logger.info("전송할 마감일 알림이 없습니다.")
                    
            finally:
                db.close()
            
            logger.info("공모전 마감일 알림 스케줄러 완료")
            
        except Exception as e:
            logger.error(f"마감일 알림 스케줄러 실행 중 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def run_test_reminders(self):
        """테스트용 알림 실행 (특정 공모전에 대해)"""
        try:
            logger.info("테스트 마감일 알림 실행")
            
            from models.contest import Contest
            from utils.notification_service import NotificationService
            from database import SessionLocal
            
            db = SessionLocal()
            try:
                # 테스트용: 마감일이 임박한 공모전 하나 선택
                test_contest = db.query(Contest).filter(
                    Contest.due_date >= datetime.now().date()
                ).first()
                
                if test_contest:
                    logger.info(f"테스트 공모전: {test_contest.name} (마감일: {test_contest.due_date})")
                    
                    # 30일 전 알림 테스트
                    sent_count = NotificationService.notify_contest_deadline_reminder(
                        db, test_contest, 30
                    )
                    logger.info(f"테스트 알림 전송 완료: {sent_count}명에게 전송")
                else:
                    logger.info("테스트할 공모전이 없습니다.")
                    
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"테스트 알림 실행 중 오류: {e}")
            import traceback
            traceback.print_exc()
