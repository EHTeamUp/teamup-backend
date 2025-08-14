from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class UserSkill(Base):
    __tablename__ = "user_skills"
    
    user_skill_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.skill_id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")
    
    def __repr__(self):
        return f"<UserSkill(user_id='{self.user_id}', skill_id={self.skill_id})>"
