from pydantic import BaseModel, validator
from typing import Optional, List, TypedDict
from datetime import datetime
from models.recruitment import ApplicationStatus

# Recruitment Post Schemas
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

# Application Schemas
class ApplicationBase(BaseModel):
    recruitment_post_id: int
    user_id: str
    message: str

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    status: ApplicationStatus

class ApplicationResponse(ApplicationBase):
    application_id: int
    status: ApplicationStatus
    
    class Config:
        from_attributes = True

class ApplicationStatusUpdate(BaseModel):
    user_ids: List[str]
    recruitment_post_id: int

class ApplicationReject(BaseModel):
    user_id: str
    recruitment_post_id: int

# User Activity Response
class UserActivityPost(BaseModel):
    """사용자 활동의 게시글 정보"""
    recruitment_post_id: int
    title: str
    content: str
    recruitment_count: int
    contest_id: int
    user_id: str
    created_at: datetime

class UserActivityApplication(BaseModel):
    """사용자 활동의 지원 정보"""
    application_id: int
    recruitment_post_id: int
    user_id: str
    message: str
    status: ApplicationStatus

class UserActivityResponse(BaseModel):
    """사용자의 작성 게시글과 지원 목록을 함께 반환하는 스키마"""
    written_posts: List[UserActivityPost]
    accepted_applications: List[UserActivityApplication]

# Comment Schemas
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    recruitment_post_id: int
    user_id: str
    parent_comment_id: Optional[int] = None
    
    @validator('parent_comment_id', pre=True, always=True)
    def validate_parent_comment_id(cls, v):
        """parent_comment_id가 0이거나 None인 경우 None으로 변환"""
        if v is None or v == 0 or v == "0":
            return None
        return v

class ReplyCreate(CommentBase):
    """대댓글 작성용 스키마 - recruitment_post_id 없음"""
    user_id: str
    parent_comment_id: int

class CommentUpdate(CommentBase):
    pass

class CommentResponse(CommentBase):
    comment_id: int
    recruitment_post_id: int
    user_id: str
    parent_comment_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CommentWithReplies(CommentResponse):
    """대댓글이 포함된 댓글 스키마"""
    replies: List['CommentResponse'] = []
    
    class Config:
        from_attributes = True

# 순환 참조 해결을 위한 업데이트
CommentWithReplies.model_rebuild()