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
    answers = relationship("UserAnswer", back_populates="question")
    
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
    answers = relationship("UserAnswer", back_populates="option")
    
    def __repr__(self):
        return f"<Option(code='{self.code}', text='{self.text[:30]}...')>"

class UserTestSession(Base):
    """사용자 테스트 세션"""
    __tablename__ = "user_test_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)  # 완료 시점
    
    # Relationships
    user = relationship("User", back_populates="test_sessions")
    answers = relationship("UserAnswer", back_populates="session")
    trait_profile = relationship("UserTraitProfile", back_populates="session", uselist=False)
    
    def __repr__(self):
        return f"<UserTestSession(user_id='{self.user_id}', started_at={self.started_at})>"

class UserAnswer(Base):
    """사용자 답변"""
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("user_test_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("options.id"), nullable=False)
    answered_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    session = relationship("UserTestSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    option = relationship("Option", back_populates="answers")
    
    def __repr__(self):
        return f"<UserAnswer(session_id={self.session_id}, question_id={self.question_id})>"

class UserTraitProfile(Base):
    """사용자 성향 프로필 (결과)"""
    __tablename__ = "user_trait_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("user_test_sessions.id"), nullable=False, unique=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    profile_code = Column(String(100), nullable=False)  # 'STRATEGIC_LEADER' 등
    traits_json = Column(JSON, nullable=False)  # {"role":"LEADER","time":"MORNING",...}
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    session = relationship("UserTestSession", back_populates="trait_profile")
    user = relationship("User", back_populates="trait_profiles")
    
    def __repr__(self):
        return f"<UserTraitProfile(user_id='{self.user_id}', profile_code='{self.profile_code}')>"
