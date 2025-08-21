from pydantic import BaseModel, Field, validator, model_validator
from typing import List, Optional
from datetime import datetime, date

# 1단계: 기본 정보 + 이메일 인증
class RegistrationStep1(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    name: str = Field(example="홍길동", description="사용자 실명")
    email: str = Field(example="user@teamup.com", description="이메일 주소")
    password: str = Field(example="password123", description="비밀번호")
    verification_code: str = Field(example="123456", description="이메일 인증번호")

# 2단계: 스킬 + 역할 선택
class RegistrationStep2(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    skill_ids: List[int] = Field(example=[1, 2, 3], description="선택한 스킬 ID 목록")
    role_ids: List[int] = Field(example=[1, 2], description="선택한 역할 ID 목록")
    custom_skills: List[str] = Field(example=["Flutter", "Dart"], description="사용자가 직접 입력한 스킬들")
    custom_roles: List[str] = Field(example=["DevOps", "QA"], description="사용자가 직접 입력한 역할들")
    
    @model_validator(mode='after')
    def check_interest_selection(self):
        """기술(skills) 또는 역할(roles) 중 최소 1개 이상 선택 필수"""
        skill_ids = self.skill_ids or []
        role_ids = self.role_ids or []
        custom_skills = self.custom_skills or []
        custom_roles = self.custom_roles or []
        
        # 빈 문자열 제거
        custom_skills = [skill.strip() for skill in custom_skills if skill.strip()]
        custom_roles = [role.strip() for role in custom_roles if role.strip()]
        
        # 기술 선택 여부 확인
        has_skills = bool(skill_ids or custom_skills)
        
        # 역할 선택 여부 확인
        has_roles = bool(role_ids or custom_roles)
        
        # 기술 또는 역할 중 최소 1개 이상 선택되어야 함
        if not has_skills and not has_roles:
            raise ValueError('기술 또는 역할 중 하나는 반드시 선택해야 합니다.')
        
        return self

# 3단계: 공모전 수상 경험 정보
class ExperienceInput(BaseModel):
    contest_name: str = Field(example="2024 대학생 소프트웨어 경진대회", description="공모전명")
    award_date: date = Field(example="2024-12-01", description="수상 날짜")
    host_organization: Optional[str] = Field(example="한국정보산업연합회", description="주최 기관")
    award_name: str = Field(example="대상", description="수상명 (예: 대상, 최우수상)")
    description: Optional[str] = Field(example="팀 프로젝트 매칭 플랫폼으로 수상", description="설명 (어떤 작품으로 수상했는지 등)")
    filter_id: int = Field(example=1, description="필터 ID (공모전 카테고리)")

class RegistrationStep3(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    experiences: List[ExperienceInput] = Field(example=[], description="공모전 수상 경험 목록")

# 4단계: 성향테스트 (필수)
class PersonalityAnswer(BaseModel):
    question_id: int = Field(example=1, description="질문 ID")
    option_id: int = Field(example=1, description="선택한 보기 ID")

class RegistrationStep4(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    answers: List[PersonalityAnswer] = Field(example=[], description="성향테스트 답변 목록")
    
    @validator('answers')
    def validate_answers(cls, v):
        """성향테스트는 4개 질문에 모두 답변해야 함"""
        if len(v) != 4:
            raise ValueError('성향테스트는 4개 질문에 모두 답변해야 합니다.')
        return v

# 전체 회원가입 정보
class CompleteRegistration(BaseModel):
    step1: RegistrationStep1
    step2: RegistrationStep2
    step3: RegistrationStep3
    step4: Optional[RegistrationStep4] = None

# 회원가입 진행 상태
class RegistrationStatus(BaseModel):
    user_id: str
    current_step: int = Field(example=1, description="현재 진행 단계 (1, 2, 3, 4)")
    is_completed: bool = Field(example=False, description="회원가입 완료 여부")
    completed_steps: List[int] = Field(example=[1], description="완료된 단계 목록")

# 단계별 응답
class StepResponse(BaseModel):
    success: bool
    message: str
    current_step: int
    next_step: Optional[int] = None
    is_completed: bool = False
    can_skip_personality: bool = False
