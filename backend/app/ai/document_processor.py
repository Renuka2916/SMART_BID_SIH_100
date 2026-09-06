import time
from typing import Optional, Dict, Any, List

from app.schemas.ai_extraction_result import (
    AIExtractionResult,
    ValidationCheck,
    SignatureSealResult
)
from app.ai.ocr_pipeline import ocr_pipeline
from app.ai.nlp_extractor import nlp_extractor
from app.ai.signature_verifier import signature_verifier
from app.utils.response_normalizer import calculate_name_similarity

class DocumentProcessor:
    """
    AI Document Intelligence Orchestrator:
    - Coordinates OCR extraction, NLP Named Entity Recognition, and Signature Verification.
    - Evaluates cross-validation consistency rules.
    - Emits structured AIExtractionResult with recommended lifecycle state.
    """

    def process(
        self,
        file_bytes: bytes,
        filename: str,
        doc_type: str = "GENERAL_STATUTORY",
        expected_bidder_name: Optional[str] = None,
        expected_pan: Optional[str] = None,
        expected_gstin: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> AIExtractionResult:
        start_t = time.time()
        
        # 1. OCR Extraction
        raw_text, ocr_conf, ocr_engine = ocr_pipeline.process_document(file_bytes, filename)

        # 2. NLP Entity Extraction
        entities = nlp_extractor.extract_all_entities(raw_text)

        # 3. Signature & Stamp Verification
        is_image = any(filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"])
        if is_image:
            sig_result = signature_verifier.verify_from_image_bytes(file_bytes)
        else:
            sig_result = signature_verifier.verify_from_text_and_fallback(raw_text)

        # 4. Cross-Validation Consistency Rules
        validation_checks: List[ValidationCheck] = []

        # Rule A: PAN & GSTIN Internal Consistency
        extracted_pan = entities.get("pan", {}).get("pan")
        extracted_gstin = entities.get("gstin", {}).get("gstin")

        if extracted_pan and extracted_gstin:
            embedded_pan_in_gstin = extracted_gstin[2:12]
            if extracted_pan == embedded_pan_in_gstin:
                validation_checks.append(ValidationCheck(
                    rule_name="PAN_GSTIN_CONSISTENCY",
                    passed=True,
                    severity="HIGH",
                    message=f"Consistent: Extracted PAN ({extracted_pan}) matches embedded characters in GSTIN ({extracted_gstin})."
                ))
            else:
                validation_checks.append(ValidationCheck(
                    rule_name="PAN_GSTIN_CONSISTENCY",
                    passed=False,
                    severity="HIGH",
                    message=f"Discrepancy: Extracted PAN ({extracted_pan}) contradicts embedded PAN in GSTIN ({embedded_pan_in_gstin})."
                ))

        # Rule B: Name Consistency against Registered Tender Bidder
        extracted_company = entities.get("company_name", {}).get("company_name")
        if expected_bidder_name and extracted_company:
            sim = calculate_name_similarity(expected_bidder_name, extracted_company)
            if sim >= 0.70:
                validation_checks.append(ValidationCheck(
                    rule_name="LEGAL_NAME_MATCH",
                    passed=True,
                    severity="MEDIUM",
                    message=f"Name match verified ({int(sim*100)}% similarity with '{expected_bidder_name}')."
                ))
            else:
                validation_checks.append(ValidationCheck(
                    rule_name="LEGAL_NAME_MATCH",
                    passed=False,
                    severity="HIGH",
                    message=f"Name mismatch: Document issued to '{extracted_company}', tender bidder is '{expected_bidder_name}'."
                ))

        # Rule C: Document Type Specific Mandatory Checks
        dt_upper = doc_type.upper()
        if "GST" in dt_upper:
            if extracted_gstin:
                validation_checks.append(ValidationCheck(
                    rule_name="GSTIN_MANDATORY_FIELD",
                    passed=True,
                    severity="HIGH",
                    message=f"Valid GSTIN identified: {extracted_gstin}."
                ))
            else:
                validation_checks.append(ValidationCheck(
                    rule_name="GSTIN_MANDATORY_FIELD",
                    passed=False,
                    severity="HIGH",
                    message="GST certificate missing readable statutory GSTIN pattern."
                ))

        elif "PAN" in dt_upper:
            if extracted_pan:
                validation_checks.append(ValidationCheck(
                    rule_name="PAN_MANDATORY_FIELD",
                    passed=True,
                    severity="HIGH",
                    message=f"Valid statutory PAN identified: {extracted_pan}."
                ))
            else:
                validation_checks.append(ValidationCheck(
                    rule_name="PAN_MANDATORY_FIELD",
                    passed=False,
                    severity="HIGH",
                    message="PAN card document missing valid 10-digit PAN pattern."
                ))

        elif "UDYAM" in dt_upper:
            u_num = entities.get("udyam", {}).get("udyam_no")
            if u_num:
                validation_checks.append(ValidationCheck(
                    rule_name="UDYAM_MANDATORY_FIELD",
                    passed=True,
                    severity="HIGH",
                    message=f"Valid MSME Udyam Registration identified: {u_num}."
                ))
            else:
                validation_checks.append(ValidationCheck(
                    rule_name="UDYAM_MANDATORY_FIELD",
                    passed=False,
                    severity="HIGH",
                    message="Udyam certificate does not contain standard UDYAM-XX-XX-XXXXXXX identifier."
                ))

        elif "MAKE_IN_INDIA" in dt_upper or "LOCAL_CONTENT" in dt_upper:
            mii_data = entities.get("make_in_india")
            if mii_data:
                pct = mii_data.get("percentage", 0.0)
                if pct >= 20.0:
                    validation_checks.append(ValidationCheck(
                        rule_name="MII_THRESHOLD_COMPLIANCE",
                        passed=True,
                        severity="HIGH",
                        message=f"Local content ({pct}%) meets statutory threshold ({mii_data.get('classification')})."
                    ))
                else:
                    validation_checks.append(ValidationCheck(
                        rule_name="MII_THRESHOLD_COMPLIANCE",
                        passed=False,
                        severity="HIGH",
                        message=f"Local content ({pct}%) below mandatory 20% minimum threshold."
                    ))
            else:
                validation_checks.append(ValidationCheck(
                    rule_name="MII_THRESHOLD_COMPLIANCE",
                    passed=False,
                    severity="MEDIUM",
                    message="Could not extract explicit local content percentage from declaration."
                ))

        elif "OEM" in dt_upper:
            if sig_result.has_oem_logo or "maf" in raw_text.lower():
                validation_checks.append(ValidationCheck(
                    rule_name="OEM_AUTHORIZATION_AUTHENTICITY",
                    passed=True,
                    severity="HIGH",
                    message="OEM Authorization Form exhibits authenticated principal branding and MAF markers."
                ))
            else:
                validation_checks.append(ValidationCheck(
                    rule_name="OEM_AUTHORIZATION_AUTHENTICITY",
                    passed=False,
                    severity="HIGH",
                    message="Missing OEM principal branding or verifiable MAF reference on document."
                ))

        # Rule D: Attestation & Signature Verification
        if sig_result.has_signature:
            validation_checks.append(ValidationCheck(
                rule_name="SIGNATORY_ATTESTATION",
                passed=True,
                severity="MEDIUM",
                message="Authorized signatory / Director signature attested on document."
            ))
        else:
            validation_checks.append(ValidationCheck(
                rule_name="SIGNATORY_ATTESTATION",
                passed=False,
                severity="MEDIUM",
                message="Document appears unsigned or missing standard signatory block."
            ))

        # 5. Determine Recommended Status & Calculate Validation Integrity Score
        has_high_failure = any(not v.passed and v.severity == "HIGH" for v in validation_checks)
        recommended_status = "FLAGGED" if has_high_failure else "AI_VERIFIED"

        # Calculate composite document integrity score penalizing mismatches:
        # OCR confidence reflects optical glyph clarity (text scanner accuracy).
        # Integrity score reflects legal validity, bidder alignment, and absence of tampering.
        base_integrity = (ocr_conf if ocr_conf is not None else 0.95) * 100.0
        deductions = 0.0
        deduction_reasons = []

        for chk in validation_checks:
            if not chk.passed:
                if chk.severity == "HIGH":
                    deductions += 45.0
                    deduction_reasons.append(chk.message)
                elif chk.severity == "MEDIUM":
                    deductions += 15.0
                    deduction_reasons.append(chk.message)

        integrity_score = max(10.0, min(100.0, round(base_integrity - deductions, 1)))
        integrity_notes = "; ".join(deduction_reasons) if deduction_reasons else "All statutory cross-checks verified."

        latency = round((time.time() - start_t) * 1000, 2)

        return AIExtractionResult(
            document_id=document_id,
            document_type=doc_type,
            file_name=filename,
            ocr_engine=ocr_engine,
            extracted_text_preview=raw_text[:300] + ("..." if len(raw_text) > 300 else ""),
            ocr_confidence=ocr_conf,
            validation_integrity_score=integrity_score,
            integrity_notes=integrity_notes,
            entities=entities,
            signature_verification=sig_result,
            validation_checks=validation_checks,
            recommended_status=recommended_status,
            processing_time_ms=latency
        )

# Singleton Processor
document_processor = DocumentProcessor()
