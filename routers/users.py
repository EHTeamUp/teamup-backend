from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import (
    UserCreate, User as UserSchema, UserLogin, Token,
    EmailVerificationRequest, EmailVerificationResponse,
    EmailVerificationCode, UserCreateWithVerification,
    UserIdCheckRequest, UserIdCheckResponse
)
from utils.auth import get_password_hash, verify_password, create_access_token
from utils.email_auth import (
    generate_verification_code, send_verification_email,
    store_verification_code, verify_email_code,
    mark_email_as_verified
)
from datetime import timedelta
from config import settings
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/check-userid", response_model=UserIdCheckResponse)
def check_user_id_availability(request: UserIdCheckRequest, db: Session = Depends(get_db)):
    """사용자 ID 중복 검사"""
    try:
        # 사용자 ID 중복 확인
        db_user = db.query(User).filter(User.user_id == request.user_id).first()
        
        if db_user:
            return UserIdCheckResponse(
                available=False,
                message=f"사용자 ID '{request.user_id}'는 이미 사용 중입니다."
            )
        else:
            return UserIdCheckResponse(
                available=True,
                message=f"사용자 ID '{request.user_id}'는 사용 가능합니다."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/send-verification", response_model=EmailVerificationResponse)
def send_email_verification(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """이메일 인증번호 전송"""
    try:
        # 이미 가입된 이메일인지 확인
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 6자리 인증번호 생성
        verification_code = generate_verification_code(6)
        
        # 이메일로 인증번호 전송
        if send_verification_email(request.email, verification_code):
            # Redis에 인증번호 저장 (10분 만료)
            store_verification_code(request.email, verification_code)
            return EmailVerificationResponse(
                message="인증번호가 이메일로 전송되었습니다.",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/verify-email", response_model=EmailVerificationResponse)
def verify_email_code_endpoint(request: EmailVerificationCode):
    """이메일 인증번호 검증"""
    try:
        if verify_email_code(request.email, request.verification_code):
            # 인증 성공 시 이메일을 인증 완료 상태로 표시
            mark_email_as_verified(request.email)
            return EmailVerificationResponse(
                message="이메일 인증이 완료되었습니다.",
                success=True
            )
        else:
            return EmailVerificationResponse(
                message="인증번호가 올바르지 않거나 만료되었습니다.",
                success=False
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/register", response_model=UserSchema)
def register(user: UserCreateWithVerification, db: Session = Depends(get_db)):
    """이메일 인증이 완료된 사용자 등록"""
    try:
        # 중복 사용자 확인
        db_user = db.query(User).filter(User.user_id == user.user_id).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID already registered"
            )
        
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 이메일 인증번호 검증
        if not verify_email_code(user.email, user.verification_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        
        # 새 사용자 생성
        hashed_password = get_password_hash(user.password)
        db_user = User(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            password_hash=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 이메일을 인증 완료 상태로 표시
        mark_email_as_verified(user.email)
        
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인"""
    user = db.query(User).filter(User.user_id == user_credentials.user_id).first()
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deleted user"
        )
    
    # 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 현재 사용자 가져오기 함수
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return current_user 