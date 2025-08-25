from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # Java, Python, Spring boot, ...
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill")
    
    def __repr__(self):
        return f"<Skill(skill_id={self.skill_id}, name='{self.name}')>" 