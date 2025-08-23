from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import settings
# Import all models to ensure they are registered with SQLAlchemy
from models import *
from routers import users, registration
from routers import profile, contests, recruitments, applications, comments, personality, synergy, notifications
import asyncio
import threading
import time
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 스케줄러 객체
scheduler = None

# 데이터베이스 테이블 생성 (MySQL 연결이 가능할 때만)
def init_database():
    try:
        if engine:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully")
            return True
        else:
            print("⚠️ Database engine not available")
            return False
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        print("📝 Please make sure MySQL server is running and database is configured")
        print("📝 You can still use the API without database functionality")
        return False

# 스케줄러 작업 함수
def run_deadline_reminders():
    """마감일 알림 스케줄러 실행"""
    try:
        from utils.scheduler import DeadlineReminderScheduler
        
        logger.info("⏰ 마감일 알림 스케줄러 실행 중...")
        scheduler_instance = DeadlineReminderScheduler()
        scheduler_instance.run_daily_reminders()
        logger.info("✅ 마감일 알림 스케줄러 완료")
        
    except Exception as e:
        logger.error(f"마감일 알림 스케줄러 실행 중 오류: {e}")

def init_scheduler():
    """스케줄러 초기화 및 설정"""
    global scheduler
    
    try:
        scheduler = BackgroundScheduler()
        
        # 매일 자정(12시)에 마감일 알림 실행
        scheduler.add_job(
            func=run_deadline_reminders,
            trigger=CronTrigger(hour=0, minute=0),
            id='deadline_reminders',
            name='공모전 마감일 알림',
            replace_existing=True
        )
        
        # 스케줄러 시작
        scheduler.start()
        logger.info("🚀 백그라운드 스케줄러가 시작되었습니다.")
        logger.info("📅 매일 자정(12시)에 마감일 알림을 확인합니다.")
        
        return True
        
    except Exception as e:
        logger.error(f"스케줄러 초기화 실패: {e}")
        return False

# 데이터베이스 초기화 시도 (실패해도 앱은 계속 실행)
database_initialized = init_database()

# FastAPI 앱 객체 생성
app = FastAPI(
    title="TeamUp API",
    description="TeamUp 프로젝트를 위한 FastAPI 백엔드",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS 미들웨어 설정 (Android Studio와의 통신을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    logger.info("🚀 TeamUp API 서버가 시작되었습니다.")
    
    # 백그라운드 스케줄러 시작
    init_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행되는 이벤트"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("🛑 스케줄러가 종료되었습니다.")

@app.get("/")
def read_root():
    return {"message": "TeamUp API에 오신 것을 환영합니다!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/scheduler/status")
def scheduler_status():
    """스케줄러 상태 확인 엔드포인트"""
    global scheduler
    
    if scheduler and scheduler.running:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            })
        
        return {
            "status": "running",
            "message": "백그라운드 스케줄러가 실행 중입니다.",
            "jobs": jobs
        }
    else:
        return {
            "status": "stopped",
            "message": "스케줄러가 실행되지 않고 있습니다."
        }

@app.post("/scheduler/run-now")
def run_scheduler_now():
    """즉시 스케줄러 실행 (테스트용)"""
    try:
        run_deadline_reminders()
        
        return {
            "status": "success",
            "message": "스케줄러가 즉시 실행되었습니다."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"스케줄러 실행 실패: {str(e)}"
        }

@app.post("/scheduler/restart")
def restart_scheduler():
    """스케줄러 재시작"""
    global scheduler
    
    try:
        if scheduler:
            scheduler.shutdown()
        
        success = init_scheduler()
        
        if success:
            return {
                "status": "success",
                "message": "스케줄러가 재시작되었습니다."
            }
        else:
            return {
                "status": "error",
                "message": "스케줄러 재시작에 실패했습니다."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"스케줄러 재시작 실패: {str(e)}"
        }

# 라우터들을 여기에 추가할 예정
app.include_router(users.router, prefix="/api/v1")
app.include_router(registration.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(contests.router, prefix="/api/v1")
app.include_router(recruitments.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(personality.router, prefix="/api/v1")
app.include_router(synergy.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


# app.include_router(teams.router, prefix="/api/v1")
# app.include_router(projects.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )