from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# 데이터베이스 엔진 생성 (연결 실패 시에도 앱 실행 가능)
try:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,  # SQL 쿼리 로깅 (개발 환경에서만)
        pool_pre_ping=True,   # 연결 상태 확인
        pool_recycle=3600     # 1시간마다 연결 재생성
    )
    print("✅ Database engine created successfully")
except Exception as e:
    print(f"⚠️ Failed to create database engine: {e}")
    engine = None

# 세션 팩토리 생성 (엔진이 없을 때는 None)
if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

# Base 클래스 생성 (모델들이 상속받을 클래스)
Base = declarative_base()

# 데이터베이스 세션 의존성
def get_db():
    if not SessionLocal:
        raise Exception("Database is not available. Please check your database connection.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 