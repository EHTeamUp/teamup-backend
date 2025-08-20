from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Experience(Base):
    __tablename__ = "experiences"
    
    experience_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 공모전 수상 정보
    contest_name = Column(String(255), nullable=False, comment="공모전명")
    award_date = Column(Date, nullable=False, comment="수상 날짜")
    host_organization = Column(String(255), nullable=True, comment="주최 기관")
    award_name = Column(String(255), nullable=False, comment="수상명 (예: 대상, 최우수상)")
    description = Column(Text, nullable=True, comment="설명 (어떤 작품으로 수상했는지 등)")
    
    # 필터링을 위한 필드
    filter_id = Column(Integer, ForeignKey("filters.filter_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 메타 정보
    created_at = Column(Date, default=func.current_date())
    updated_at = Column(Date, default=func.current_date(), onupdate=func.current_date())
    
    # Relationships
    user = relationship("User", back_populates="experiences")
    filter = relationship("Filter", back_populates="experiences")
    
    def __repr__(self):
        return f"<Experience(contest_name='{self.contest_name}', award_name='{self.award_name}')>"
