from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    
    def __repr__(self):
        return f"<Role(role_id={self.role_id}, name='{self.name}')>"
