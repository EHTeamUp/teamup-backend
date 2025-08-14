from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # Java, Python, Spring boot, ...
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill")
    recruitment_post_skills = relationship("RecruitmentPostSkill", back_populates="skill")

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # 백엔드, 프론트엔드, 풀스택, ...
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    recruitment_post_roles = relationship("RecruitmentPostRole", back_populates="role")

class UserSkill(Base):
    __tablename__ = "user_skills"
    
    user_skill_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    skill_id = Column(Integer, nullable=False)
    
    # Foreign Keys
    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_role_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    role_id = Column(Integer, nullable=False)
    
    # Foreign Keys
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles") 