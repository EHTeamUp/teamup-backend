from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class NotificationType(enum.Enum):
    NEW_CONTEST = "new_contest"  # 새로운 공모전 알림
    APPLICATION_RESPONSE = "application_response"  # 지원 응답 알림
    NEW_COMMENT = "new_comment"  # 새 댓글 알림
    NEW_REPLY = "new_reply"  # 새 대댓글 알림
    CONTEST_DEADLINE = "contest_deadline"  # 공모전 마감일 알림

class Notification(Base):
    __tablename__ = "notifications"
    
    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # 관련 데이터 (JSON 형태로 저장)
    related_data = Column(Text, nullable=True)  # JSON string
    
    # Foreign Keys
    user = relationship("User", back_populates="notifications")
