from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # Java, Python, Spring boot, ...
    is_custom = Column(Boolean, default=True)  # 사용자가 직접 추가한 스킬인지 여부
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill")
    recruitment_post_skills = relationship("RecruitmentPostSkill", back_populates="skill")
    
    def __repr__(self):
        return f"<Skill(skill_id={self.skill_id}, name='{self.name}', is_custom={self.is_custom})>" 