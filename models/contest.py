from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
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
    contest_filters = relationship("ContestFilter", back_populates="contest")
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
    contest_id = Column(Integer, ForeignKey("contests.contest_id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.tag_id"), nullable=False)
    
    # Foreign Keys
    contest = relationship("Contest", back_populates="contest_tags")
    tag = relationship("Tag", back_populates="contest_tags")

class Filter(Base):
    __tablename__ = "filters"
    
    filter_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    contest_filters = relationship("ContestFilter", back_populates="filter")

class ContestFilter(Base):
    __tablename__ = "contest_filters"
    
    contest_filter_id = Column(Integer, primary_key=True, autoincrement=True)
    contest_id = Column(Integer, ForeignKey("contests.contest_id"), nullable=False)
    filter_id = Column(Integer, ForeignKey("filters.filter_id"), nullable=False)
    
    # Foreign Keys
    contest = relationship("Contest", back_populates="contest_filters")
    filter = relationship("Filter", back_populates="contest_filters") 