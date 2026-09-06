import re
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PortalStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FLAGGED = "FLAGGED"
    FAILED = "FAILED"
    OFFLINE = "OFFLINE"

class BidderIdentifiers(BaseModel):
    company_name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    udyam_no: Optional[str] = None
    cin: Optional[str] = None
    epfo_code: Optional[str] = None
    esic_code: Optional[str] = None
    startup_dipp_no: Optional[str] = None
    nsic_no: Optional[str] = None
    oem_name: Optional[str] = None
    oem_maf_ref: Optional[str] = None
    bis_reg_no: Optional[str] = None
    udin: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class DiscrepancyItem(BaseModel):
    field: str
    severity: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    message: str
    source_portal: str

class NormalizedPortalResponse(BaseModel):
    portal_id: str
    portal_name: str
    category: str
    status: PortalStatus
    is_valid: bool
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)
    discrepancies: List[str] = Field(default_factory=list)
    normalized_data: Dict[str, Any] = Field(default_factory=dict)
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency_ms: float = 0.0
    error_message: Optional[str] = None

def normalize_legal_name(name: str) -> str:
    """Standardizes company names for fuzzy comparison across government portals."""
    if not name:
        return ""
    cleaned = name.upper().strip()
    # Normalize common business entity designations
    replacements = {
        "PRIVATE LIMITED": "PVT LTD",
        "PRVT LTD": "PVT LTD",
        "P. LTD.": "PVT LTD",
        "P. LTD": "PVT LTD",
        "PVT. LTD.": "PVT LTD",
        "PVT. LTD": "PVT LTD",
        "LIMITED": "LTD",
        "LTD.": "LTD",
        "LLP.": "LLP",
        "CORPORATION": "CORP",
        "INCORPORATED": "INC",
        "ENTERPRISES": "ENT",
        "SYSTEMS": "SYS",
        "TECHNOLOGIES": "TECH",
        "SOLUTIONS": "SOL"
    }
    for old, new in replacements.items():
        cleaned = re.sub(rf"\b{re.escape(old)}\b", new, cleaned)
    # Strip non-alphanumeric except whitespace
    cleaned = re.sub(r"[^A-Z0-9\s]", "", cleaned)
    # Collapse multiple spaces
    return " ".join(cleaned.split())

def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculates Levenshtein-like token overlap similarity between two company names."""
    n1 = normalize_legal_name(name1)
    n2 = normalize_legal_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0

    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # Check substring containment
    if n1 in n2 or n2 in n1:
        return max(jaccard, 0.85)
        
    return round(jaccard, 2)
