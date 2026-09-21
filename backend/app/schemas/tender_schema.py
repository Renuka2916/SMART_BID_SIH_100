from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class StatutoryRequirementTemplate(BaseModel):
    key: str
    name: str
    category: str  # e.g., "Statutory & Taxation", "MSME & Industrial", "Labor & Social", "Integrity & Compliance"
    description: str
    is_recommended: bool = True

class TenderBase(BaseModel):
    tender_ref: str = Field(..., description="SmartBid Tender Reference Number, e.g. SMARTBID/2026/B/89123")
    title: str
    description: Optional[str] = None
    category: str = "Goods"  # Goods, Services, Works
    estimated_value: float = Field(default=0.0, description="Estimated Tender Value in INR")
    department: str = "Central Public Procurement"
    opening_date: datetime
    closing_date: datetime
    status: str = "Published"  # Draft, Published, Under Evaluation, Closed
    mandatory_requirements: List[str] = Field(
        default_factory=list,
        description="Keys of selected mandatory compliance requirements (e.g., ['UDYAM', 'GST', 'PAN'])"
    )

class TenderCreate(TenderBase):
    pass

class TenderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    estimated_value: Optional[float] = None
    department: Optional[str] = None
    opening_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    status: Optional[str] = None
    mandatory_requirements: Optional[List[str]] = None

class TenderResponse(TenderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    created_by_name: Optional[str] = None

class TenderListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[TenderResponse]
