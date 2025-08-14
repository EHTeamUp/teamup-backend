from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_role_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id={self.role_id})>"
