from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SynergyRequest(BaseModel):
    filter_id: int = Field(example=1, description="필터링 ID")
    user_ids: List[str] = Field(
        example=["user1", "user2", "user3"],
        description="시너지 분석을 위한 사용자 ID 목록"
    )

class ApplicantData(BaseModel):
    role: str = Field(example="프론트엔드 개발자, UI/UX 디자이너", description="팀원 역할")
    skill: str = Field(example="python, HTML", description="팀원 스킬")
    experience: str = Field(example="1:0, 5:0, 1:1", description="공모전 경험")
    tendency_type: str = Field(example="LEADER", description="역할 유형 (LEADER, SUPPORTER)")
    goal: str = Field(example="QUALITY", description="목표 (QUALITY, SCHEDULE)")
    time: str = Field(example="MORNING", description="시간대 (MORNING, NIGHT)")
    problem: str = Field(example="ANALYTIC", description="문제 해결 방식 (ANALYTIC, ADHOC)")

class SynergyAnalysisRequest(BaseModel):
    filtering_id: int = Field(example=1, description="공모전 필터링 ID")
    applicants: List[ApplicantData] = Field(description="지원자 정보 목록")

class SynergyAnalysisResponse(BaseModel):
    result: str = Field(example="시너지 결과입니다", description="시너지 분석 결과")

class UserSkill(BaseModel):
    skill_name: str = Field(example="Java", description="스킬 이름")

class UserRole(BaseModel):
    role_name: str = Field(example="프론트엔드 개발자", description="역할 이름")

class UserTrait(BaseModel):
    profile_code: str = Field(example="STRATEGIC_LEADER", description="프로필 코드")
    display_name: str = Field(example="전략 리더", description="프로필 표시 이름")

class SynergyUser(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    skills: List[UserSkill] = Field(example=[], description="사용자 스킬 목록")
    roles: List[UserRole] = Field(example=[], description="사용자 역할 목록")
    traits: Optional[UserTrait] = Field(example=None, description="사용자 성향 정보")
    
    class Config:
        from_attributes = True

class SynergyResponse(BaseModel):
    users: List[SynergyUser] = Field(
        description="시너지 분석 대상 사용자 목록 (자신 포함)"
    )
    synergy_result: Optional[SynergyAnalysisResponse] = Field(
        default=None, description="시너지 분석 결과"
    )
