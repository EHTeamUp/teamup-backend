from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import settings
# Import all models to ensure they are registered with SQLAlchemy
from models import *
from routers import users, registration
from routers import profile

# 데이터베이스 테이블 생성 (MySQL 연결이 가능할 때만)
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️ Database connection failed: {e}")
    print("📝 Please make sure MySQL server is running and database is configured")

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

@app.get("/")
def read_root():
    return {"message": "TeamUp API에 오신 것을 환영합니다!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 라우터들을 여기에 추가할 예정
app.include_router(users.router, prefix="/api/v1")
app.include_router(registration.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
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