from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    tender_ref = Column(String(100), unique=True, index=True, nullable=False) # e.g. "GEM/2026/B/892011"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="Goods", nullable=False) # Goods, Services, Works
    estimated_value = Column(Float, default=0.0, nullable=False) # In INR
    department = Column(String(255), default="Central Public Procurement", nullable=False)
    opening_date = Column(DateTime, nullable=False)
    closing_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="Published", nullable=False) # Draft, Published, Under Evaluation, Closed
    mandatory_requirements = Column(JSON, default=list, nullable=False) # List of required compliance code strings
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    created_by = relationship("User", back_populates="tenders")
    bidders = relationship("Bidder", back_populates="tender", cascade="all, delete-orphan")
