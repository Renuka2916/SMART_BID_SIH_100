from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Bidder(Base):
    __tablename__ = "bidders"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)

    # AES-256 encrypted sensitive fields
    pan_encrypted = Column(Text, nullable=False)
    pan_masked = Column(String(20), nullable=False, index=True)

    gstin_encrypted = Column(Text, nullable=False)
    gstin_masked = Column(String(20), nullable=False, index=True)

    udyam_no_encrypted = Column(Text, nullable=True)
    udyam_no_masked = Column(String(50), nullable=True)

    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)

    # Overall evaluation status
    composite_status = Column(String(50), default="UNDER_REVIEW", nullable=False)  # COMPLIANT, FLAGGED, NON_COMPLIANT, UNDER_REVIEW
    compliance_score = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    tender = relationship("Tender", back_populates="bidders")
    documents = relationship("Document", back_populates="bidder", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="bidder", cascade="all, delete-orphan")
