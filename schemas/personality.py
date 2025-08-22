from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

# 질문 스키마
class QuestionBase(BaseModel):
    order_no: int = Field(example=1, description="질문 순서")
    key_name: str = Field(example="role", description="질문 키")
    text: str = Field(example="팀에서 나는...", description="질문 내용")

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    
    class Config:
        from_attributes = True

# 보기 스키마
class OptionBase(BaseModel):
    code: str = Field(example="LEADER", description="보기 코드")
    text: str = Field(example="방향을 제시하고 결정을 주도하는 편이다", description="보기 내용")
    trait_tag: str = Field(example="LEADER", description="성향 태그")
    order_no: int = Field(example=1, description="보기 순서")

class OptionCreate(OptionBase):
    question_id: int = Field(description="질문 ID")

class Option(OptionBase):
    id: int
    question_id: int
    
    class Config:
        from_attributes = True

# 질문과 보기를 포함한 완전한 질문 스키마
class QuestionWithOptions(Question):
    options: List[Option] = Field(default=[], description="보기 목록")

# 답변 스키마
class AnswerBase(BaseModel):
    question_id: int = Field(description="질문 ID")
    option_id: int = Field(description="선택한 보기 ID")

# 성향 프로필 스키마
class TraitProfileBase(BaseModel):
    profile_code: str = Field(example="STRATEGIC_LEADER", description="프로필 코드")
    traits_json: Dict[str, str] = Field(example={"role": "LEADER", "time": "MORNING"}, description="성향 특성")

class TraitProfileCreate(TraitProfileBase):
    user_id: str = Field(description="사용자 ID")

class TraitProfile(TraitProfileBase):
    id: int
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 테스트 제출 요청 스키마
class SubmitTestRequest(BaseModel):
    user_id: str = Field(description="사용자 ID")
    answers: List[AnswerBase] = Field(description="답변 목록")

# 테스트 결과 응답 스키마
class TestResultResponse(BaseModel):
    profile_code: str
    display_name: str
    description: str
    traits: Dict[str, str]
    completed_at: Optional[datetime] = None

# 질문 목록 응답 스키마
class QuestionListResponse(BaseModel):
    questions: List[QuestionWithOptions]
    total_count: int

# 프로필 규칙 스키마
class ProfileRuleBase(BaseModel):
    profile_code: str = Field(example="STRATEGIC_LEADER", description="프로필 코드")
    display_name: str = Field(example="전략 리더", description="표시 이름")
    description: str = Field(example="아침형 + 분석 + 완성도 중시", description="설명")
    required_tags_json: List[str] = Field(example=["LEADER", "MORNING", "ANALYTIC", "QUALITY"], description="필요한 태그들")
    priority: int = Field(example=10, description="우선순위")

class ProfileRuleCreate(ProfileRuleBase):
    pass

class ProfileRule(ProfileRuleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
