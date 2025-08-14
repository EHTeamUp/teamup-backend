from sqlalchemy import Column, Integer, String, Text, CHAR
from sqlalchemy.orm import relationship
from database import Base

class Personality(Base):
    __tablename__ = "personalities"
    
    personality_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    answers = relationship("Answer", back_populates="personality")
    user_personality_scores = relationship("UserPersonalityScore", back_populates="personality")

class Question(Base):
    __tablename__ = "questions"
    
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    
    # Relationships
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, nullable=False)
    label = Column(CHAR(1))  # A, B
    content = Column(Text, nullable=False)
    personality_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    
    # Foreign Keys
    question = relationship("Question", back_populates="answers")
    personality = relationship("Personality", back_populates="answers")

class UserPersonalityScore(Base):
    __tablename__ = "user_personality_scores"
    
    user_personality_score_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    personality_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    
    # Foreign Keys
    user = relationship("User", back_populates="user_personality_scores")
    personality = relationship("Personality", back_populates="user_personality_scores") 