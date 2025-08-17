from sqlalchemy import Column, Integer, String, Text, CHAR, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Personality(Base):
    __tablename__ = "personalities"
    
    personality_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    user_personality_scores = relationship("UserPersonalityScore", back_populates="personality")
    answers = relationship("Answer", back_populates="personality")
    
    def __repr__(self):
        return f"<Personality(personality_id={self.personality_id}, name='{self.name}')>"

class Question(Base):
    __tablename__ = "questions"
    
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    
    # Relationships
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.question_id"), nullable=False)
    label = Column(CHAR(1))  # A, B
    content = Column(Text, nullable=False)
    personality_id = Column(Integer, ForeignKey("personalities.personality_id"), nullable=False)
    score = Column(Integer, nullable=False)
    
    # Foreign Keys
    question = relationship("Question", back_populates="answers")
    personality = relationship("Personality", back_populates="answers")

class UserPersonalityScore(Base):
    __tablename__ = "user_personality_scores"
    
    user_personality_score_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    personality_id = Column(Integer, ForeignKey("personalities.personality_id"), nullable=False)
    score = Column(Integer, nullable=False)
    
    # Foreign Keys
    user = relationship("User", back_populates="user_personality_scores")
    personality = relationship("Personality", back_populates="user_personality_scores") 