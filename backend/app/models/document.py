import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    OCR_PROCESSING = "OCR_PROCESSING"
    AI_VERIFIED = "AI_VERIFIED"
    FLAGGED = "FLAGGED"

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bidder_id = Column(Integer, ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False, index=True)

    document_type = Column(String(50), nullable=False)  # PAN_CARD, GST_CERTIFICATE, UDYAM_CERTIFICATE, ITR_V, MAKE_IN_INDIA_DECLARATION, etc.
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), default="application/pdf", nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash for document integrity validation

    status = Column(String(50), default=DocumentStatus.UPLOADED.value, nullable=False)
    extracted_data = Column(JSON, default=dict, nullable=False)
    ocr_confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    bidder = relationship("Bidder", back_populates="documents")
