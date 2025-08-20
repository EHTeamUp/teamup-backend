from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SynergyRequest(BaseModel):
    user_ids: List[str] = Field(
        example=["user1", "user2", "user3"],
        description="시너지 분석을 위한 사용자 ID 목록"
    )

class UserSkill(BaseModel):
    skill_name: str = Field(example="Java", description="스킬 이름")
    is_custom: bool = Field(example=False, description="사용자 정의 스킬 여부")

class UserRole(BaseModel):
    role_name: str = Field(example="프론트엔드 개발자", description="역할 이름")
    is_custom: bool = Field(example=False, description="사용자 정의 역할 여부")

class UserExperience(BaseModel):
    contest_name: str = Field(example="2024 대학생 소프트웨어 경진대회", description="공모전명")
    award_status: int = Field(example=1, description="수상 여부 (0: 참가, 1: 수상)")
    award_name: Optional[str] = Field(example="대상", description="수상명 (수상한 경우만)")

class UserTrait(BaseModel):
    goal: str = Field(example="SCHEDULE", description="목표 지향성")
    role: str = Field(example="LEADER", description="역할 선호도")
    time: str = Field(example="MORNING", description="시간대 선호도")
    problem: str = Field(example="ADHOC", description="문제 해결 방식")

class SynergyUser(BaseModel):
    user_id: str = Field(example="user123", description="사용자 ID")
    skills: List[UserSkill] = Field(example=[], description="사용자 스킬 목록")
    roles: List[UserRole] = Field(example=[], description="사용자 역할 목록")
    experiences: List[UserExperience] = Field(example=[], description="사용자 경험 목록")
    traits: Optional[UserTrait] = Field(example=None, description="사용자 성향 정보")
    
    class Config:
        from_attributes = True

class SynergyResponse(BaseModel):
    users: List[SynergyUser] = Field(
        description="시너지 분석 대상 사용자 목록 (자신 포함)"
    )
    message: str = Field(
        example="시너지 분석을 위한 사용자 목록이 준비되었습니다.",
        description="응답 메시지"
    )
