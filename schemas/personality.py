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

# 테스트 세션 스키마
class TestSession(BaseModel):
    id: int
    user_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 답변 스키마
class AnswerBase(BaseModel):
    question_id: int = Field(description="질문 ID")
    option_id: int = Field(description="선택한 보기 ID")

class AnswerCreate(AnswerBase):
    session_id: int = Field(description="테스트 세션 ID")

class Answer(AnswerBase):
    id: int
    session_id: int
    answered_at: datetime
    
    class Config:
        from_attributes = True

# 성향 프로필 스키마
class TraitProfileBase(BaseModel):
    profile_code: str = Field(example="STRATEGIC_LEADER", description="프로필 코드")
    traits_json: Dict[str, str] = Field(example={"role": "LEADER", "time": "MORNING"}, description="성향 특성")

class TraitProfileCreate(TraitProfileBase):
    session_id: int = Field(description="테스트 세션 ID")
    user_id: str = Field(description="사용자 ID")

class TraitProfile(TraitProfileBase):
    id: int
    session_id: int
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 테스트 시작 요청 스키마
class StartTestRequest(BaseModel):
    pass  # 더 이상 설문지 코드가 필요 없음

# 테스트 제출 요청 스키마
class SubmitTestRequest(BaseModel):
    session_id: int = Field(description="테스트 세션 ID")
    answers: List[AnswerBase] = Field(description="답변 목록")

# 테스트 결과 응답 스키마
class TestResultResponse(BaseModel):
    session_id: int
    profile_code: str
    traits: Dict[str, str]
    completed_at: datetime
    total_questions: int
    answered_questions: int

# 질문 목록 응답 스키마
class QuestionListResponse(BaseModel):
    questions: List[QuestionWithOptions]
    total_count: int
