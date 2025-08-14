from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Contest(Base):
    __tablename__ = "contests"
    
    contest_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    contest_url = Column(String(500), nullable=False)
    poster_img_url = Column(String(500), nullable=False)
    start_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    prize = Column(Integer, nullable=False)
    
    # Relationships
    contest_tags = relationship("ContestTag", back_populates="contest")
    recruitment_posts = relationship("RecruitmentPost", back_populates="contest")

class Tag(Base):
    __tablename__ = "tags"
    
    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    contest_tags = relationship("ContestTag", back_populates="tag")

class ContestTag(Base):
    __tablename__ = "contest_tags"
    
    contest_tag_id = Column(Integer, primary_key=True, autoincrement=True)
    contest_id = Column(Integer, nullable=False)
    tag_id = Column(Integer, nullable=False)
    
    # Foreign Keys
    contest = relationship("Contest", back_populates="contest_tags")
    tag = relationship("Tag", back_populates="contest_tags") 