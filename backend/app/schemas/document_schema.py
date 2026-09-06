from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.document import DocumentStatus

class DocumentBase(BaseModel):
    document_type: str = Field(..., description="Document classification (e.g. PAN_CARD, GST_CERTIFICATE, UDYAM_CERTIFICATE)")
    file_name: str = Field(..., description="Original filename uploaded")
    mime_type: str = Field(default="application/pdf", description="MIME content type")

class DocumentCreate(DocumentBase):
    storage_path: str = Field(..., description="Path or storage URI where file is saved")
    file_size_bytes: Optional[int] = Field(None, description="Size in bytes")
    file_hash: Optional[str] = Field(None, description="Pre-computed SHA-256 hash if provided")

class DocumentUpdateStatus(BaseModel):
    status: DocumentStatus = Field(..., description="New document status: UPLOADED, OCR_PROCESSING, AI_VERIFIED, FLAGGED")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Extracted key-value pairs from OCR/verification")
    ocr_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")

class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bidder_id: int
    storage_path: str
    file_hash: str
    file_size_bytes: Optional[int] = None
    status: str
    extracted_data: Dict[str, Any] = {}
    ocr_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentResponse]
