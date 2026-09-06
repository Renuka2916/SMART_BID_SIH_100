import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class NLPExtractor:
    """
    Layout-Aware NLP & Regex Named Entity Recognition for Indian Statutory Documents.
    Extracts GSTIN, PAN, Udyam No, Entity Names, Local Content %, UDIN, and Dates.
    """

    GSTIN_PATTERN = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", re.IGNORECASE)
    PAN_PATTERN = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b", re.IGNORECASE)
    UDYAM_PATTERN = re.compile(r"\b(UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7})\b", re.IGNORECASE)
    UDIN_PATTERN = re.compile(r"\b(2[0-9]{7}[A-Z]{6}[0-9]{4}|[0-9]{18})\b", re.IGNORECASE)
    MAF_CODE_PATTERN = re.compile(r"\b(MAF-[A-Z0-9\-]{6,30})\b", re.IGNORECASE)
    
    # State code lookup for GSTIN
    GST_STATE_CODES = {
        "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
        "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
        "09": "Uttar Pradesh", "10": "Bihar", "19": "West Bengal", "24": "Gujarat",
        "27": "Maharashtra", "29": "Karnataka", "32": "Kerala", "33": "Tamil Nadu",
        "36": "Telangana", "37": "Andhra Pradesh"
    }

    PAN_ENTITY_TYPES = {
        "C": "Company",
        "P": "Individual / Proprietor",
        "F": "Partnership Firm / LLP",
        "H": "Hindu Undivided Family (HUF)",
        "A": "Association of Persons (AOP)",
        "T": "Trust",
        "B": "Body of Individuals (BOI)",
        "L": "Local Authority",
        "J": "Artificial Juridical Person",
        "G": "Government Entity"
    }

    def extract_gstin(self, text: str) -> Optional[Dict[str, Any]]:
        match = self.GSTIN_PATTERN.search(text)
        if match:
            raw_gstin = match.group(1).upper()
            state_code = raw_gstin[:2]
            embedded_pan = raw_gstin[2:12]
            state_name = self.GST_STATE_CODES.get(state_code, "Other/Unknown State")
            return {
                "gstin": raw_gstin,
                "state_code": state_code,
                "state_name": state_name,
                "embedded_pan": embedded_pan,
                "confidence": 0.99
            }
        return None

    def extract_pan(self, text: str) -> Optional[Dict[str, Any]]:
        # Find matches not immediately preceded/followed by alphanumeric (to avoid false matches inside GSTIN)
        matches = self.PAN_PATTERN.findall(text)
        if matches:
            # Prefer standalone PAN or first match
            pan_val = matches[0].upper()
            entity_code = pan_val[3] if len(pan_val) >= 4 else ""
            entity_type = self.PAN_ENTITY_TYPES.get(entity_code, "Unclassified")
            return {
                "pan": pan_val,
                "entity_type_code": entity_code,
                "entity_type": entity_type,
                "confidence": 0.98
            }
        return None

    def extract_udyam(self, text: str) -> Optional[Dict[str, Any]]:
        match = self.UDYAM_PATTERN.search(text)
        if match:
            u_num = match.group(1).upper()
            parts = u_num.split("-")
            state = parts[1] if len(parts) > 1 else ""
            return {
                "udyam_no": u_num,
                "state_prefix": state,
                "confidence": 0.99
            }
        return None

    def extract_udin(self, text: str) -> Optional[Dict[str, Any]]:
        match = self.UDIN_PATTERN.search(text)
        if match:
            return {
                "udin": match.group(1).upper(),
                "confidence": 0.97
            }
        return None

    def extract_local_content(self, text: str) -> Optional[Dict[str, Any]]:
        # Search for patterns like "Local Content: 68%" or "65% local content"
        p1 = re.search(r"(?:Local Content|Local Value Addition|MII Percentage)\s*[:\-]?\s*([0-9]{1,3}(?:\.[0-9]+)?)\s*%", text, re.IGNORECASE)
        if p1:
            val = float(p1.group(1))
            classification = "Class-I Local Supplier" if val >= 50.0 else ("Class-II Local Supplier" if val >= 20.0 else "Non-Local Supplier")
            return {
                "percentage": val,
                "percentage_str": f"{val}%",
                "classification": classification,
                "meets_class_1": val >= 50.0,
                "confidence": 0.95
            }
        
        p2 = re.search(r"([0-9]{1,3}(?:\.[0-9]+)?)\s*%\s*(?:Local Content|Local Value Addition)", text, re.IGNORECASE)
        if p2:
            val = float(p2.group(1))
            classification = "Class-I Local Supplier" if val >= 50.0 else ("Class-II Local Supplier" if val >= 20.0 else "Non-Local Supplier")
            return {
                "percentage": val,
                "percentage_str": f"{val}%",
                "classification": classification,
                "meets_class_1": val >= 50.0,
                "confidence": 0.94
            }

        return None

    def extract_company_name(self, text: str) -> Optional[Dict[str, Any]]:
        # Common anchor patterns in certificates
        anchors = [
            r"(?:Legal Name|Trade Name)\s*[:\-]?\s*([A-Za-z0-9\s\.,&]+?)(?:\n|$)",
            r"(?:Name of (?:the )?(?:Enterprise|Supplier|Bidder|Company))\s*[:\-]?\s*([A-Za-z0-9\s\.,&]+?)(?:\n|$)",
            r"(?:M/s\.?|Messrs\.?)\s*([A-Za-z0-9\s\.,&]+?(?:Private Limited|Pvt\.? Ltd\.?|Limited|Ltd\.?|LLP))",
            r"\b([A-Z][A-Za-z0-9\s&]+?(?:Private Limited|Pvt\.? Ltd\.?|Limited|Ltd\.?|LLP))\b"
        ]
        for pat in anchors:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean trailing noise
                name = re.sub(r"\s+", " ", name)
                if len(name) > 3 and not name.upper().startswith("INSTRUCTIONS"):
                    return {
                        "company_name": name,
                        "confidence": 0.90
                    }
        return None

    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        date_patterns = [
            r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b",
            r"\b(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b"
        ]
        results = []
        for pat in date_patterns:
            for match in re.finditer(pat, text):
                raw = match.group(1)
                results.append({"raw_date": raw})
        return results[:4]

    def extract_all_entities(self, text: str) -> Dict[str, Any]:
        """Runs full entity extraction across text payload."""
        entities = {}
        gstin_info = self.extract_gstin(text)
        if gstin_info:
            entities["gstin"] = gstin_info

        pan_info = self.extract_pan(text)
        if pan_info:
            entities["pan"] = pan_info

        udyam_info = self.extract_udyam(text)
        if udyam_info:
            entities["udyam"] = udyam_info

        udin_info = self.extract_udin(text)
        if udin_info:
            entities["udin"] = udin_info

        mii_info = self.extract_local_content(text)
        if mii_info:
            entities["make_in_india"] = mii_info

        name_info = self.extract_company_name(text)
        if name_info:
            entities["company_name"] = name_info

        dates = self.extract_dates(text)
        if dates:
            entities["detected_dates"] = dates

        return entities

# Singleton NLP Extractor
nlp_extractor = NLPExtractor()
