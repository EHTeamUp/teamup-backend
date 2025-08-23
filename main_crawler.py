#!/usr/bin/env python3
"""
TeamUp 크롤링 파이프라인
2주에 한번씩 실행되어 공모전을 크롤링하고 분석합니다.
"""

import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 크롤링 및 분석 모듈 import
from jobs.crawler import CrawlingExecutor
from jobs.analyzer import TagGenerator
from utils.notification_service import NotificationService
from database import get_db
from sqlalchemy.orm import Session

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("크롤링 시작")
    
    try:
        # 1단계: 크롤링 실행
        logger.info("공모전 크롤링 시작")
        crawler = CrawlingExecutor()
        crawler.run_all_crawling()
        logger.info("크롤링 완료")
        
        # 2단계: 분석 실행
        logger.info("태그 분석 시작")
        
        # .env에서 OLLAMA_HOST 가져오기
        ollama_host = os.getenv('OLLAMA_HOST', '')
        logger.info(f"Ollama 호스트: {ollama_host}")
        
        analyzer = TagGenerator(ollama_host=ollama_host)
        analyzer.extract_tags_from_final_contest()
        logger.info("분석 완료")
        
        # 3단계: 마감일 알림 실행 (선택사항)
        logger.info("마감일 알림 실행")
        db: Session = next(get_db())
        try:
            NotificationService.check_and_send_deadline_reminders(db)
            logger.info("마감일 알림 완료")
        except Exception as e:
            logger.warning(f"마감일 알림 실패 (계속 진행): {e}")
        finally:
            db.close()
        
        logger.info("크롤링 완료")
        
    except Exception as e:
        logger.error(f"실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 로그 디렉토리 생성
    os.makedirs("/var/log/teamup", exist_ok=True)
    
    main()
