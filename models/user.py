from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False)  # 0: 활성, 1: 탈퇴
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="user")
    user_roles = relationship("UserRole", back_populates="user")
    user_personality_scores = relationship("UserPersonalityScore", back_populates="user")
    recruitment_posts = relationship("RecruitmentPost", back_populates="user")
    applications = relationship("Application", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan") 