from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RecruitmentPostBase(BaseModel):
    title: str
    content: str
    recruitment_count: int
    contest_id: int

class RecruitmentPostCreate(RecruitmentPostBase):
    user_id: str

class RecruitmentPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    recruitment_count: Optional[int] = None
    contest_id: Optional[int] = None
    user_id: str

class RecruitmentPostResponse(RecruitmentPostBase):
    recruitment_post_id: int
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class RecruitmentPostList(BaseModel):
    recruitment_post_id: int
    title: str
    content: str
    recruitment_count: int
    contest_id: int
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
