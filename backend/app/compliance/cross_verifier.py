import logging
from typing import Dict, Any, List, Optional
from app.utils.response_normalizer import (
    NormalizedPortalResponse,
    calculate_name_similarity,
    normalize_legal_name,
    PortalStatus
)
from app.schemas.compliance_schema import CrossVerificationDiscrepancy

logger = logging.getLogger("compliance_cross_verifier")

class CrossVerificationEngine:
    """
    Field-by-Field Multi-Source Cross-Verification Engine:
    Triangulates evidence across:
    1. Bidder Core Registration Vault (DB record)
    2. Uploaded Document OCR / NLP Semantic Entities
    3. External Government Portals (Live / Normalized Rest Responses)
    """

    def cross_verify(
        self,
        bidder_data: Dict[str, Any],
        portal_results: Dict[str, NormalizedPortalResponse],
        documents: List[Any],
        tender_metadata: Optional[Dict[str, Any]] = None
    ) -> List[CrossVerificationDiscrepancy]:
        discrepancies: List[CrossVerificationDiscrepancy] = []

        bidder_name = bidder_data.get("company_name", "").strip()
        bidder_pan = (bidder_data.get("pan") or "").strip().upper()
        bidder_gstin = (bidder_data.get("gstin") or "").strip().upper()
        bidder_udyam = (bidder_data.get("udyam_no") or "").strip().upper()

        tender_meta = tender_metadata or {}
        estimated_value = tender_meta.get("estimated_value", 0.0)

        # ----------------------------------------------------------------------
        # 1. PAN-GSTIN Internal Structural Consistency
        # ----------------------------------------------------------------------
        if bidder_pan and bidder_gstin and len(bidder_gstin) == 15:
            embedded_pan = bidder_gstin[2:12]
            if bidder_pan != embedded_pan:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field_name="PAN_GSTIN_CONSISTENCY",
                    severity="CRITICAL",
                    source_a=f"Bidder PAN Record: {bidder_pan}",
                    source_b=f"Embedded GSTIN PAN: {embedded_pan} (from {bidder_gstin})",
                    description="Critical statutory identity conflict: The PAN registered does not match characters 3-12 of the GSTIN.",
                    disqualification_ground=True
                ))

        # ----------------------------------------------------------------------
        # 2. Portal Data Cross-Checks (GSTN, CBDT, MCA21, CPPP, EPFO, etc.)
        # ----------------------------------------------------------------------
        # A. CPPP Debarment & Blacklisting Check
        cppp_res = portal_results.get("NON_BLACKLIST") or portal_results.get("CPPP_DEBARMENT")
        if cppp_res:
            norm = cppp_res.normalized_data
            is_blacklisted = norm.get("is_blacklisted") or norm.get("debarred") or False
            matches = norm.get("matches_found", 0) or len(norm.get("database_matches", []))
            vigilance = str(norm.get("vigilance_status") or norm.get("vigilance_clearance_status") or "").upper()
            if is_blacklisted:
                if vigilance == "REVIEW_REQUIRED":
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name="HISTORICAL_WATCHLIST_FLAG",
                        severity="HIGH",
                        source_a=f"Bidder: {bidder_name} (PAN: {bidder_pan})",
                        source_b="State Public Procurement Watchlist (CPPP Historical)",
                        description="Historical debarment entry detected (2024 notice period delay). Officer scrutiny required before final award.",
                        disqualification_ground=False
                    ))
                else:
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name="BLACKLISTING_STATUS",
                        severity="CRITICAL",
                        source_a=f"Bidder: {bidder_name} (PAN: {bidder_pan})",
                        source_b="CPPP National Debarment / GeM Watchlist Registry",
                        description=f"Active statutory debarment order detected: {norm.get('debarment_reason', 'Listed on debarred suppliers list')}. Under GFR Rule 151, entity is prohibited from participating.",
                        disqualification_ground=True
                    ))

        # B. GSTN Portal Cross-Check
        gstn_res = portal_results.get("GSTN")
        if gstn_res:
            norm = gstn_res.normalized_data
            status = str(norm.get("gstin_status", "")).upper()
            if status and status != "ACTIVE":
                discrepancies.append(CrossVerificationDiscrepancy(
                    field_name="GSTIN_STATUS",
                    severity="CRITICAL",
                    source_a=f"Bidder GSTIN: {bidder_gstin}",
                    source_b=f"GSTN Portal Status: {status}",
                    description=f"Statutory taxation failure: GSTIN status is '{status}'. Active GST registration is mandatory under GeM General Terms.",
                    disqualification_ground=True
                ))
            
            portal_trade_name = norm.get("trade_name") or norm.get("legal_name") or ""
            if portal_trade_name:
                sim = calculate_name_similarity(bidder_name, portal_trade_name)
                if sim < 0.70:
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name="LEGAL_NAME_GSTN",
                        severity="HIGH",
                        source_a=f"Bidder Registered Name: {bidder_name}",
                        source_b=f"GSTN Portal Legal/Trade Name: {portal_trade_name}",
                        description=f"Entity name divergence: {int(sim*100)}% match with GSTN registry. Possible unauthorized bid submission under unassociated GSTIN.",
                        disqualification_ground=False
                    ))

        # C. Income Tax CBDT Cross-Check
        pan_res = portal_results.get("INCOME_TAX_CBDT")
        if pan_res:
            norm = pan_res.normalized_data
            pan_status = str(norm.get("pan_status", "")).upper()
            if pan_status and pan_status not in ["VALID", "ACTIVE", "OPERATIVE"]:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field_name="PAN_CBDT_STATUS",
                    severity="CRITICAL",
                    source_a=f"Bidder PAN: {bidder_pan}",
                    source_b=f"Income Tax CBDT Status: {pan_status}",
                    description=f"Income Tax PAN is not operative or valid (Status: {pan_status}).",
                    disqualification_ground=True
                ))

        # D. MCA21 & ICAI Turnover / UDIN Cross-Check
        mca_res = portal_results.get("MCA21") or portal_results.get("TURNOVER_CA")
        if mca_res:
            norm = mca_res.normalized_data
            net_worth = norm.get("net_worth_positive", True)
            if net_worth is False:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field_name="FINANCIAL_SOLVENCY",
                    severity="HIGH",
                    source_a=f"Bidder Financial Review: {bidder_name}",
                    source_b="MCA21 / Balance Sheet Filing",
                    description="Financial insolvency risk: Negative net worth reported in latest audited balance sheet filing.",
                    disqualification_ground=False
                ))

        # E. EPFO / ESIC Social Security Compliance
        epfo_res = portal_results.get("EPFO")
        if epfo_res:
            norm = epfo_res.normalized_data
            challan_status = str(norm.get("challan_status", "")).upper()
            if "DELAY" in challan_status or "DEFAULT" in challan_status or norm.get("payment_delayed"):
                discrepancies.append(CrossVerificationDiscrepancy(
                    field_name="EPFO_REGULARITY",
                    severity="MEDIUM",
                    source_a=f"Bidder EPFO Filing: {bidder_name}",
                    source_b="EPFO Shram Suvidha Portal",
                    description="Statutory social security observation: Irregular or delayed EPFO contribution deposits identified in recent quarters.",
                    disqualification_ground=False
                ))

        # ----------------------------------------------------------------------
        # 3. Document OCR Extraction vs Core Data & Portal Triangulation
        # ----------------------------------------------------------------------
        for doc in documents:
            extracted = getattr(doc, "extracted_data", {}) or {}
            doc_type = getattr(doc, "document_type", "")
            entities = extracted.get("entities", {})

            # Check OCR PAN against Bidder PAN
            ocr_pan = entities.get("pan", {}).get("pan") or extracted.get("pan")
            if ocr_pan and bidder_pan:
                ocr_pan_clean = str(ocr_pan).strip().upper()
                if ocr_pan_clean != bidder_pan:
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name="DOCUMENT_PAN_MISMATCH",
                        severity="CRITICAL",
                        source_a=f"Bidder Vault PAN: {bidder_pan}",
                        source_b=f"Document OCR ({getattr(doc, 'file_name', 'File')}): {ocr_pan_clean}",
                        description=f"Identity document forgery/mismatch: Uploaded {doc_type} contains PAN '{ocr_pan_clean}' which contradicts registered bidder PAN '{bidder_pan}'.",
                        disqualification_ground=True
                    ))

            # Check OCR GSTIN against Bidder GSTIN
            ocr_gstin = entities.get("gstin", {}).get("gstin") or extracted.get("gstin")
            if ocr_gstin and bidder_gstin:
                ocr_gstin_clean = str(ocr_gstin).strip().upper()
                if ocr_gstin_clean != bidder_gstin:
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name="DOCUMENT_GSTIN_MISMATCH",
                        severity="HIGH",
                        source_a=f"Bidder Vault GSTIN: {bidder_gstin}",
                        source_b=f"Document OCR ({getattr(doc, 'file_name', 'File')}): {ocr_gstin_clean}",
                        description=f"Tax certificate mismatch: Extracted GSTIN '{ocr_gstin_clean}' differs from tender submission GSTIN '{bidder_gstin}'.",
                        disqualification_ground=False
                    ))

            # Check OCR Company Name against Bidder Name
            ocr_company = entities.get("company_name", {}).get("company_name") or extracted.get("company_name")
            if ocr_company and bidder_name:
                sim = calculate_name_similarity(bidder_name, str(ocr_company))
                if sim < 0.70:
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name="DOCUMENT_NAME_MISMATCH",
                        severity="HIGH",
                        source_a=f"Bidder Registered Name: {bidder_name}",
                        source_b=f"Document Recipient Name: {ocr_company} (Sim: {int(sim*100)}%)",
                        description=f"Certificate issued to a different legal entity '{ocr_company}' rather than the participating bidder '{bidder_name}'.",
                        disqualification_ground=False
                    ))

            # Check Make in India Local Content %
            mii_entity = entities.get("make_in_india", {})
            claimed_pct = mii_entity.get("percentage")
            if claimed_pct is not None:
                try:
                    pct_val = float(claimed_pct)
                    # Class-II threshold is 20%, Class-I is 50%
                    if pct_val < 20.0:
                        discrepancies.append(CrossVerificationDiscrepancy(
                            field_name="LOCAL_CONTENT_DEFICIT",
                            severity="HIGH",
                            source_a=f"Uploaded MII Declaration: {pct_val}%",
                            source_b="DPIIT Public Procurement Order (Min 20% / 50%)",
                            description=f"Declared local content ({pct_val}%) fails the statutory Class-II minimum threshold of 20.0%.",
                            disqualification_ground=False
                        ))
                except (ValueError, TypeError):
                    pass

            # Check CA UDIN Format
            if "TURNOVER" in doc_type or "BALANCE_SHEET" in doc_type or "CA_CERT" in doc_type:
                udin = entities.get("udin", {}).get("udin") or extracted.get("udin")
                if not udin:
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name="MISSING_CA_UDIN",
                        severity="MEDIUM",
                        source_a=f"CA Turnover Certificate ({getattr(doc, 'file_name', 'Doc')})",
                        source_b="ICAI Mandatory UDIN Directive",
                        description="CA certificate lacks verifiable 18-digit Unique Document Identification Number (UDIN).",
                        disqualification_ground=False
                    ))

            # Check Signature Attestation
            sig_ver = extracted.get("signature_verification", {})
            has_sig = sig_ver.get("has_signature", True) if isinstance(sig_ver, dict) else True
            if not has_sig:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field_name="MISSING_SIGNATURE",
                    severity="MEDIUM",
                    source_a=f"Document: {getattr(doc, 'file_name', 'File')}",
                    source_b="GeM Tender Terms (Signed & Stamped Mandatory)",
                    description="Uploaded statutory document lacks visible authorized signatory signature or company seal.",
                    disqualification_ground=False
                ))

        # Check Portal Discrepancies forwarded from fetchers
        for pid, pres in portal_results.items():
            for d_text in pres.discrepancies:
                # Avoid duplicate addition if already handled
                if not any(d.source_b == pres.portal_name for d in discrepancies):
                    discrepancies.append(CrossVerificationDiscrepancy(
                        field_name=f"{pid}_PORTAL_DISCREPANCY",
                        severity="MEDIUM" if pres.status == PortalStatus.FLAGGED else "LOW",
                        source_a=f"Bidder Submission: {bidder_name}",
                        source_b=pres.portal_name,
                        description=f"External portal flagged an observation: {d_text}",
                        disqualification_ground=False
                    ))

        return discrepancies

cross_verifier = CrossVerificationEngine()
