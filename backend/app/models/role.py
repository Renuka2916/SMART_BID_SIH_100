from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # "Procurement Officer", "Bidder", "Admin", "Auditor"
    description = Column(Text, nullable=True)

    users = relationship("User", back_populates="role")
