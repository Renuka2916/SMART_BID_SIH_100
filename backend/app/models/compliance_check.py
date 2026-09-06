from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class ComplianceCheckStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FLAGGED = "FLAGGED"
    FAILED = "FAILED"
    EXEMPTED = "EXEMPTED"

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False, index=True)

    requirement_key = Column(String(50), nullable=False, index=True)  # UDYAM, GST, PAN, MAKE_IN_INDIA, EPFO_ESIC, etc.
    portal_name = Column(String(50), nullable=False)  # GSTN, MSME_UDYAM, INCOME_TAX_CBDT, EPFO, DIGILOCKER, CPPP_DEBARMENT
    status = Column(String(50), default=ComplianceCheckStatus.PENDING.value, nullable=False)

    check_details = Column(JSON, default=dict, nullable=False)  # Portal responses, verification timestamps, parameters
    discrepancy_notes = Column(Text, nullable=True)
    score_contribution = Column(Float, default=0.0, nullable=False)

    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    bidder = relationship("Bidder", back_populates="compliance_checks")
