from pydantic import BaseModel, Field, HttpUrl
from typing import List
from datetime import date

# 태그 스키마
class Tag(BaseModel):
    tag_id: int = Field(example=1, description="태그 ID")
    name: str = Field(example="웹 개발", description="태그명")
    
    class Config:
        from_attributes = True

# 공모전 목록 스키마
class Contest(BaseModel):
    contest_id: int = Field(example=1, description="공모전 ID")
    name: str = Field(example="2024 대학생 소프트웨어 경진대회", description="공모전명")
    poster_img_url: HttpUrl = Field(example="https://example.com/poster.jpg", description="포스터 이미지 URL")
    due_date: date = Field(example="2024-12-31", description="마감일")
    tags: List[Tag] = Field(example=[], description="연결된 태그들")
    
    class Config:
        from_attributes = True

# 공모전 목록 조회 응답 스키마
class ContestListResponse(BaseModel):
    contests: List[Contest] = Field(example=[], description="공모전 목록")
    total_count: int = Field(example=10, description="전체 공모전 수")
