from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date

class UserBase(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    name: str = Field(example="홍길동", description="사용자 이름")
    email: EmailStr = Field(example="user@example.com", description="이메일")

class UserCreate(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    name: str = Field(example="홍길동", description="사용자 이름")
    email: EmailStr = Field(example="user@example.com", description="이메일")
    password: str = Field(example="password123", description="비밀번호")

class User(UserBase):
    is_deleted: bool = Field(example=False, description="삭제 여부")
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    password: str = Field(example="Password12#", description="비밀번호")

class Token(BaseModel):
    access_token: str = Field(example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", description="액세스 토큰")
    token_type: str = Field(example="bearer", description="토큰 타입")

class LogoutResponse(BaseModel):
    message: str = Field(example="로그아웃이 완료되었습니다.", description="로그아웃 메시지")

class UserUpdateProfile(BaseModel):
    name: Optional[str] = Field(None, example="홍길동", description="변경할 사용자 이름")
    current_password: str = Field(example="current123", description="현재 비밀번호 (비밀번호 변경 시 필요)")
    new_password: Optional[str] = Field(None, example="new123", description="새로운 비밀번호 (변경하지 않을 경우 생략)")

# 스킬 수정 스키마
class SkillUpdate(BaseModel):
    skill_ids: List[int] = Field(example=[1, 2, 3], description="선택할 스킬 ID 목록")
    custom_skills: List[str] = Field(example=["Flutter", "Dart"], description="사용자가 직접 입력한 스킬들")

# 역할 수정 스키마
class RoleUpdate(BaseModel):
    role_ids: List[int] = Field(example=[1, 2], description="선택할 역할 ID 목록")
    custom_roles: List[str] = Field(example=["DevOps", "QA"], description="사용자가 직접 입력한 역할들")

# 경험 수정 스키마
class ExperienceUpdate(BaseModel):
    contest_name: str = Field(example="2024 대학생 소프트웨어 경진대회", description="공모전명")
    award_date: date = Field(example="2024-12-01", description="수상 날짜")
    host_organization: Optional[str] = Field(example="한국정보산업연합회", description="주최 기관")
    award_name: str = Field(example="대상", description="수상명 (예: 대상, 최우수상)")
    description: Optional[str] = Field(example="팀 프로젝트 매칭 플랫폼으로 수상", description="설명 (어떤 작품으로 수상했는지 등)")
    filter_id: int = Field(example=1, description="필터 ID (공모전 카테고리)")

class ExperienceCreate(BaseModel):
    experiences: List[ExperienceUpdate] = Field(example=[], description="공모전 수상 경험 목록")

class User(UserBase):
    is_deleted: bool = Field(example=False, description="삭제 여부")
    
    class Config:
        from_attributes = True

class TokenData(BaseModel):
    user_id: Optional[str] = None

# 이메일 인증 관련 스키마
class EmailVerificationRequest(BaseModel):
    email: EmailStr = Field(
        example="user@teamup.com",
        description="인증번호를 받을 이메일 주소"
    )

class EmailVerificationResponse(BaseModel):
    message: str = Field(
        description="인증번호 발송 결과 메시지"
    )

class EmailVerificationCode(BaseModel):
    email: EmailStr = Field(
        example="user@teamup.com",
        description="인증할 이메일 주소"
    )
    verification_code: str = Field(
        example="123456",
        description="이메일로 받은 6자리 인증번호"
    )

class UserCreateWithVerification(BaseModel):
    user_id: str = Field(
        example="teamup_user",
        description="사용자 ID"
    )
    name: str = Field(
        example="홍길동",
        description="사용자 실명"
    )
    email: EmailStr = Field(
        example="user@teamup.com",
        description="이메일 주소"
    )
    password: str = Field(
        example="password123",
        description="비밀번호"
    )
    verification_code: str = Field(
        example="123456",
        description="이메일 인증번호"
    )

# 사용자 ID 중복 검사 스키마
class UserIdCheckRequest(BaseModel):
    user_id: str = Field(
        example="teamup_user",
        description="중복 검사할 사용자 ID"
    )

class UserIdCheckResponse(BaseModel):
    available: bool = Field(
        description="사용 가능 여부 (true: 사용 가능, false: 이미 사용 중)"
    )
    message: str = Field(
        description="중복 검사 결과 메시지"
    ) 