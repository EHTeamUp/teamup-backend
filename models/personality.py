from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Question(Base):
    """질문"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(Integer, nullable=False)  # 질문 순서
    key_name = Column(String(50), nullable=False)  # 'role', 'time', 'communication' 등
    text = Column(String(255), nullable=False)  # 질문 내용
    
    # Relationships
    options = relationship("Option", back_populates="question", order_by="Option.order_no")
    
    def __repr__(self):
        return f"<Question(key='{self.key_name}', text='{self.text[:30]}...')>"

class Option(Base):
    """질문 보기"""
    __tablename__ = "options"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    code = Column(String(50), nullable=False)  # 'LEADER', 'SUPPORTER' 등
    text = Column(String(255), nullable=False)  # 보기 내용
    trait_tag = Column(String(50), nullable=False)  # 결과 계산용 태그
    order_no = Column(Integer, nullable=False)  # 보기 순서
    
    # Relationships
    question = relationship("Question", back_populates="options")
    
    def __repr__(self):
        return f"<Option(code='{self.code}', text='{self.text[:30]}...')>"

class UserTraitProfile(Base):
    """사용자 성향 프로필 (결과)"""
    __tablename__ = "user_trait_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    profile_code = Column(String(100), nullable=False)  # 'STRATEGIC_LEADER' 등
    traits_json = Column(JSON, nullable=False)  # {"role":"LEADER","time":"MORNING",...}
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trait_profiles")
    
    def __repr__(self):
        return f"<UserTraitProfile(user_id='{self.user_id}', profile_code='{self.profile_code}')>"

class ProfileRule(Base):
    """프로필 규칙"""
    __tablename__ = "profile_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_code = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    required_tags_json = Column(JSON, nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<ProfileRule(profile_code='{self.profile_code}', display_name='{self.display_name}')>"
