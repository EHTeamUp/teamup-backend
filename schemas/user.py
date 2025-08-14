from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    user_id: str
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    is_deleted: bool
    
    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class UserLogin(BaseModel):
    user_id: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

# ID Duplication Check schemas
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

# Email Verification schemas
class EmailVerificationRequest(BaseModel):
    email: EmailStr = Field(
        example="user@teamup.com",
        description="인증번호를 받을 이메일 주소"
    )

class EmailVerificationResponse(BaseModel):
    message: str
    success: bool

class EmailVerificationCode(BaseModel):
    email: EmailStr = Field(
        example="user@teamup.com",
        description="인증할 이메일 주소"
    )
    verification_code: str = Field(
        example="123456",
        description="6자리 인증번호"
    )

class UserCreateWithVerification(BaseModel):
    user_id: str = Field(
        example="teamup_user",
        description="사용자 ID (고유값)"
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
        description="비밀번호 (최소 8자)"
    )
    verification_code: str = Field(
        example="123456",
        description="이메일로 받은 6자리 인증번호"
    )

# Skill and Role schemas
class SkillBase(BaseModel):
    name: str

class SkillCreate(SkillBase):
    pass

class Skill(SkillBase):
    skill_id: int
    
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    role_id: int
    
    class Config:
        from_attributes = True

class UserSkillCreate(BaseModel):
    skill_id: int

class UserRoleCreate(BaseModel):
    role_id: int

# User with skills and roles
class UserWithDetails(User):
    skills: List[Skill] = []
    roles: List[Role] = [] 