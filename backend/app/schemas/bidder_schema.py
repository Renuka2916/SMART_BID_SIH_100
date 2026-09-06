from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class BidderBase(BaseModel):
    company_name: str = Field(..., description="Legal registered name of bidder enterprise")
    contact_email: EmailStr = Field(..., description="Primary authorized communication email")
    contact_phone: Optional[str] = Field(None, description="Contact telephone/mobile number")

class BidderCreate(BidderBase):
    pan: str = Field(..., description="10-digit Permanent Account Number (PAN)", min_length=10, max_length=10)
    gstin: str = Field(..., description="15-character Goods and Services Tax Identification Number (GSTIN)", min_length=15, max_length=15)
    udyam_no: Optional[str] = Field(None, description="Udyam Registration Number (e.g. UDYAM-XX-00-0000000)")

class BidderUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    composite_status: Optional[str] = None
    compliance_score: Optional[float] = None

class BidderResponse(BidderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    pan_masked: str
    gstin_masked: str
    udyam_no_masked: Optional[str] = None
    
    # Decrypted fields available for authorized Procurement Officers
    pan: Optional[str] = None
    gstin: Optional[str] = None
    udyam_no: Optional[str] = None

    composite_status: str
    compliance_score: float
    documents_count: int = 0
    checks_count: int = 0
    created_at: datetime
    updated_at: datetime

class BidderListResponse(BaseModel):
    total: int
    items: List[BidderResponse]
