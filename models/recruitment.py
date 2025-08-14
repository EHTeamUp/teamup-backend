from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class ApplicationStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class RecruitmentPost(Base):
    __tablename__ = "recruitment_posts"
    
    recruitment_post_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)  # 작성자
    contest_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Foreign Keys
    user = relationship("User", back_populates="recruitment_posts")
    contest = relationship("Contest", back_populates="recruitment_posts")
    
    # Relationships
    applications = relationship("Application", back_populates="recruitment_post")
    recruitment_post_skills = relationship("RecruitmentPostSkill", back_populates="recruitment_post")
    recruitment_post_roles = relationship("RecruitmentPostRole", back_populates="recruitment_post")
    comments = relationship("Comment", back_populates="recruitment_post")

class Application(Base):
    __tablename__ = "applications"
    
    application_id = Column(Integer, primary_key=True, autoincrement=True)
    recruitment_post_id = Column(Integer, nullable=False)
    user_id = Column(String(50), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending)
    
    # Foreign Keys
    recruitment_post = relationship("RecruitmentPost", back_populates="applications")
    user = relationship("User", back_populates="applications")

class RecruitmentPostSkill(Base):
    __tablename__ = "recruitment_post_skills"
    
    recruitment_post_skill_id = Column(Integer, primary_key=True, autoincrement=True)
    recruitment_post_id = Column(Integer, nullable=False)
    skill_id = Column(Integer, nullable=False)
    
    # Foreign Keys
    recruitment_post = relationship("RecruitmentPost", back_populates="recruitment_post_skills")
    skill = relationship("Skill", back_populates="recruitment_post_skills")

class RecruitmentPostRole(Base):
    __tablename__ = "recruitment_post_roles"
    
    recruitment_post_role_id = Column(Integer, primary_key=True, autoincrement=True)
    recruitment_post_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)
    
    # Foreign Keys
    recruitment_post = relationship("RecruitmentPost", back_populates="recruitment_post_roles")
    role = relationship("Role", back_populates="recruitment_post_roles")

class Comment(Base):
    __tablename__ = "comments"
    
    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    recruitment_post_id = Column(Integer, nullable=False)
    user_id = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Foreign Keys
    recruitment_post = relationship("RecruitmentPost", back_populates="comments")
    user = relationship("User", back_populates="comments") 