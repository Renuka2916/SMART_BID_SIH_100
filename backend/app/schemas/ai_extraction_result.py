from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ExtractedEntity(BaseModel):
    field_name: str
    raw_value: str
    normalized_value: Optional[Any] = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    source_snippet: Optional[str] = None

class SignatureSealResult(BaseModel):
    has_signature: bool = False
    has_stamp_seal: bool = False
    has_oem_logo: bool = False
    signature_confidence: float = 0.0
    seal_confidence: float = 0.0
    logo_confidence: float = 0.0
    detected_regions: List[Dict[str, Any]] = Field(default_factory=list)
    details: str = ""

class ValidationCheck(BaseModel):
    rule_name: str
    passed: bool
    severity: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    message: str

class AIExtractionResult(BaseModel):
    document_id: Optional[str] = None
    document_type: str
    file_name: str
    ocr_engine: str
    extracted_text_preview: str
    ocr_confidence: float = Field(ge=0.0, le=1.0, default=0.9)
    entities: Dict[str, Any] = Field(default_factory=dict)
    signature_verification: SignatureSealResult = Field(default_factory=SignatureSealResult)
    validation_checks: List[ValidationCheck] = Field(default_factory=list)
    recommended_status: str = "AI_VERIFIED"  # "AI_VERIFIED" or "FLAGGED"
    validation_integrity_score: float = Field(default=100.0, ge=0.0, le=100.0, description="Composite document verification integrity score")
    integrity_notes: Optional[str] = Field(default=None, description="Summary notes explaining integrity deduction")
    processing_time_ms: float = 0.0
    processed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
