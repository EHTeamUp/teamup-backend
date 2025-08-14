from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import (
    UserLogin, Token, User as UserSchema, 
    UserUpdateProfile, LogoutResponse
)
from utils.auth import get_password_hash, verify_password, create_access_token, get_current_user
from datetime import timedelta

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인"""
    try:
        # 사용자 ID로 사용자 조회
        user = db.query(User).filter(User.user_id == user_credentials.user_id).first()
        
        # 사용자가 존재하지 않거나 삭제된 경우
        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect user ID or password"
            )
        
        # 비밀번호 검증
        if not verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect user ID or password"
            )
        
        # JWT 토큰 생성 (24시간 유효)
        access_token_expires = timedelta(hours=24)
        access_token = create_access_token(
            data={"sub": user.user_id}, expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: User = Depends(get_current_user)):
    """사용자 로그아웃"""
    try:
        # JWT 토큰은 클라이언트에서 삭제하도록 안내
        # 서버에서는 현재 사용자 정보만 반환하여 로그아웃 확인
        return LogoutResponse(
            message=f"{current_user.name}님, 로그아웃이 완료되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return current_user

@router.put("/mypage", response_model=dict)
def update_user_profile(
    profile_update: UserUpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """마이페이지 - 회원정보 수정 (이름, 비밀번호만 변경 가능)"""
    try:
        # 현재 비밀번호 확인
        if not verify_password(profile_update.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 일치하지 않습니다."
            )
        
        # 이름 변경
        if profile_update.name is not None:
            if profile_update.name.strip() == "":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이름은 빈 값일 수 없습니다."
                )
            current_user.name = profile_update.name.strip()
        
        # 비밀번호 변경
        if profile_update.new_password is not None:
            if profile_update.new_password.strip() == "":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="새 비밀번호는 빈 값일 수 없습니다."
                )
            if len(profile_update.new_password) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="새 비밀번호는 최소 6자 이상이어야 합니다."
                )
            current_user.password_hash = get_password_hash(profile_update.new_password)
        
        # 변경사항이 있는지 확인
        if profile_update.name is None and profile_update.new_password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="변경할 내용이 없습니다."
            )
        
        # 데이터베이스에 저장
        db.commit()
        
        # 변경된 필드 목록 생성
        updated_fields = []
        if profile_update.name is not None:
            updated_fields.append("이름")
        if profile_update.new_password is not None:
            updated_fields.append("비밀번호")
        
        return {
            "message": f"회원정보가 성공적으로 수정되었습니다. (변경된 항목: {', '.join(updated_fields)})",
            "updated_fields": updated_fields
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )