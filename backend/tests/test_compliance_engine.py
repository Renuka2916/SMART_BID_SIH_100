import pytest
import sys, os
from datetime import datetime, timezone
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from database import SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.models.compliance_check import ComplianceCheck
from app.compliance import (
    rule_engine,
    cross_verifier,
    scoring_module,
    risk_classifier,
    recommendation_generator,
    compliance_engine
)
from app.utils.response_normalizer import (
    NormalizedPortalResponse,
    PortalStatus
)
from app.schemas.compliance_schema import (
    CrossVerificationDiscrepancy,
    RuleEvaluationResult,
    ScoreBreakdown,
    RiskAssessment
)

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def officer_token():
    resp = client.post(
        "/api/auth/login",
        json={"email": "officer@gem.gov.in", "password": "GeM@2026!Officer"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

@pytest.fixture
def bidder_token():
    resp = client.post(
        "/api/auth/login",
        json={"email": "bidder@techcorp.in", "password": "Bidder@2026!Pass"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

# ==============================================================================
# 1. Rule Engine Unit Tests
# ==============================================================================

def test_rule_catalog():
    catalog = rule_engine.get_rule_catalog()
    assert len(catalog) >= 10
    keys = [r["rule_key"] for r in catalog]
    assert "GST" in keys
    assert "PAN" in keys
    assert "NON_BLACKLIST" in keys
    assert "MAKE_IN_INDIA" in keys
    assert "OEM_AUTH" in keys
    assert "TURNOVER" in keys

def test_rule_engine_statutory_evaluation_pass():
    bidder_dict = {
        "company_name": "Alpha Data Systems Pvt Ltd",
        "pan": "AAAPA1234K",
        "gstin": "07AAAPA1234K1Z5",
        "udyam_no": "UDYAM-DL-01-0029145"
    }
    portal_results = {
        "GSTN": NormalizedPortalResponse(
            portal_id="GSTN",
            portal_name="GSTN API",
            category="Taxation",
            status=PortalStatus.VERIFIED,
            is_valid=True,
            normalized_data={"gstin_status": "ACTIVE", "filing_regularity": "Regular"}
        ),
        "INCOME_TAX_CBDT": NormalizedPortalResponse(
            portal_id="INCOME_TAX_CBDT",
            portal_name="Income Tax CBDT",
            category="Identity",
            status=PortalStatus.VERIFIED,
            is_valid=True,
            normalized_data={"pan_status": "ACTIVE", "aadhaar_seeding": "YES"}
        ),
        "CPPP_DEBARMENT": NormalizedPortalResponse(
            portal_id="CPPP_DEBARMENT",
            portal_name="CPPP Debarment",
            category="Integrity",
            status=PortalStatus.VERIFIED,
            is_valid=True,
            normalized_data={"matches_found": 0, "is_blacklisted": False}
        )
    }

    results = rule_engine.evaluate_rules(
        bidder_data=bidder_dict,
        portal_results=portal_results,
        tender_requirements=["GST", "PAN", "NON_BLACKLIST"]
    )
    assert len(results) == 3
    assert all(r.status == "VERIFIED" for r in results)
    total_score = sum(r.score_awarded for r in results)
    assert total_score >= 99.0  # Dynamic normalized weights sum to 100

def test_rule_engine_failed_gstin():
    bidder_dict = {
        "company_name": "Defunct Enterprise",
        "pan": "BBBPB9999K",
        "gstin": "07BBBPB9999K1Z5"
    }
    portal_results = {
        "GSTN": NormalizedPortalResponse(
            portal_id="GSTN",
            portal_name="GSTN API",
            category="Taxation",
            status=PortalStatus.FAILED,
            is_valid=False,
            normalized_data={"gstin_status": "CANCELLED"}
        )
    }
    results = rule_engine.evaluate_rules(
        bidder_data=bidder_dict,
        portal_results=portal_results,
        tender_requirements=["GST"]
    )
    assert len(results) == 1
    assert results[0].status == "FAILED"
    assert results[0].score_awarded == 0.0

# ==============================================================================
# 2. Cross-Verification Module Unit Tests
# ==============================================================================

def test_cross_verifier_pan_gstin_mismatch():
    bidder_dict = {
        "company_name": "Test Firm",
        "pan": "ABCDE1234F",
        "gstin": "07ZZZZZ9999K1Z5"  # Embedded PAN does not match
    }
    discrepancies = cross_verifier.cross_verify(
        bidder_data=bidder_dict,
        portal_results={},
        documents=[]
    )
    conflict = [d for d in discrepancies if d.field_name == "PAN_GSTIN_CONSISTENCY"]
    assert len(conflict) == 1
    assert conflict[0].severity == "CRITICAL"
    assert conflict[0].disqualification_ground is True

def test_cross_verifier_cppp_blacklisting_detection():
    bidder_dict = {
        "company_name": "Debarred Supplies Pvt Ltd",
        "pan": "AAACD1111E",
        "gstin": "07AAACD1111E1Z5"
    }
    portal_results = {
        "CPPP_DEBARMENT": NormalizedPortalResponse(
            portal_id="CPPP_DEBARMENT",
            portal_name="CPPP Registry",
            category="Integrity",
            status=PortalStatus.FAILED,
            is_valid=False,
            normalized_data={"is_blacklisted": True, "matches_found": 1, "debarment_reason": "Vigilance Case"}
        )
    }
    discrepancies = cross_verifier.cross_verify(
        bidder_data=bidder_dict,
        portal_results=portal_results,
        documents=[]
    )
    bl_disc = [d for d in discrepancies if d.field_name == "BLACKLISTING_STATUS"]
    assert len(bl_disc) == 1
    assert bl_disc[0].severity == "CRITICAL"
    assert bl_disc[0].disqualification_ground is True

def test_cross_verifier_document_pan_mismatch():
    bidder_dict = {
        "company_name": "Alpha Corp",
        "pan": "AAAPA1234K",
        "gstin": "07AAAPA1234K1Z5"
    }
    # Mock document with forged/differing PAN
    class MockDoc:
        file_name = "forged_pan.pdf"
        document_type = "PAN_CARD"
        extracted_data = {"entities": {"pan": {"pan": "ZZZPZ9999L"}}}

    discrepancies = cross_verifier.cross_verify(
        bidder_data=bidder_dict,
        portal_results={},
        documents=[MockDoc()]
    )
    doc_pan_disc = [d for d in discrepancies if d.field_name == "DOCUMENT_PAN_MISMATCH"]
    assert len(doc_pan_disc) == 1
    assert doc_pan_disc[0].severity == "CRITICAL"

# ==============================================================================
# 3. Scoring Module & Penalty Tests
# ==============================================================================

def test_scoring_module_penalties():
    rules = [
        RuleEvaluationResult(
            rule_key="GST",
            rule_name="GSTIN Verification",
            portal_name="GSTN",
            category="Taxation",
            status="VERIFIED",
            weight=50.0,
            score_awarded=50.0,
            is_mandatory=True,
            details={}
        ),
        RuleEvaluationResult(
            rule_key="PAN",
            rule_name="PAN Verification",
            portal_name="INCOME_TAX_CBDT",
            category="Identity",
            status="VERIFIED",
            weight=50.0,
            score_awarded=50.0,
            is_mandatory=True,
            details={}
        )
    ]
    # No discrepancies -> 100%
    clean_score = scoring_module.calculate_score(rules, [])
    assert clean_score.raw_score == 100.0
    assert clean_score.penalties == 0.0
    assert clean_score.final_score == 100.0
    assert clean_score.category_scores["Taxation"] == 100.0

    # With HIGH discrepancy (-15 points)
    disc = [
        CrossVerificationDiscrepancy(
            field_name="LEGAL_NAME",
            severity="HIGH",
            source_a="Bidder",
            source_b="Portal",
            description="Name divergence detected."
        )
    ]
    penalized_score = scoring_module.calculate_score(rules, disc)
    assert penalized_score.raw_score == 100.0
    assert penalized_score.penalties == 15.0
    assert penalized_score.final_score == 85.0

# ==============================================================================
# 4. Risk Classifier & Recommendation Generator Tests
# ==============================================================================

def test_risk_classification_and_recommendations():
    # 1. Clean Low Risk Case
    score_clean = ScoreBreakdown(raw_score=95.0, penalties=0.0, final_score=95.0, category_scores={})
    rules_clean = [
        RuleEvaluationResult(
            rule_key="GST", rule_name="GST", portal_name="GSTN", category="Taxation",
            status="VERIFIED", weight=50.0, score_awarded=50.0, is_mandatory=True, details={}
        )
    ]
    risk_low = risk_classifier.classify_risk(score_clean, rules_clean, [])
    assert risk_low.risk_level == "LOW"
    assert risk_low.risk_score <= 20.0

    rec_qualify = recommendation_generator.generate_recommendation(
        "Compliant Ltd", score_clean, risk_low, rules_clean, [], {}
    )
    assert rec_qualify.verdict == "QUALIFY"
    assert "QUALIFY" in rec_qualify.headline

    # 2. Critical Disqualification Case
    crit_disc = [
        CrossVerificationDiscrepancy(
            field_name="BLACKLISTING_STATUS",
            severity="CRITICAL",
            source_a="Bidder",
            source_b="CPPP",
            description="Active Debarment",
            disqualification_ground=True
        )
    ]
    score_bad = ScoreBreakdown(raw_score=70.0, penalties=30.0, final_score=40.0, category_scores={})
    risk_high = risk_classifier.classify_risk(score_bad, rules_clean, crit_disc)
    assert risk_high.risk_level == "HIGH"
    assert risk_high.risk_score >= 75.0

    rec_dq = recommendation_generator.generate_recommendation(
        "Debarred Ltd", score_bad, risk_high, rules_clean, crit_disc, {}
    )
    assert rec_dq.verdict == "DISQUALIFY"
    assert len(rec_dq.disqualification_grounds) >= 1

# ==============================================================================
# 5. Full API Endpoints & Audit Log Integration Tests
# ==============================================================================

def test_api_compliance_rules(officer_token):
    resp = client.get(
        "/api/compliance/rules",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    catalog = resp.json()
    assert len(catalog) >= 10

def test_api_compliance_evaluate_and_audit_trail(officer_token, db_session):
    # Fetch Alpha Data Systems bidder
    bidder = db_session.query(Bidder).filter(Bidder.company_name == "Alpha Data Systems Pvt Ltd").first()
    assert bidder is not None

    # Count audit logs before
    logs_before = db_session.query(AuditLog).filter(
        AuditLog.entity_id == str(bidder.id),
        AuditLog.action == "VERIFY"
    ).count()

    resp = client.post(
        f"/api/compliance/evaluate/{bidder.id}",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    report = resp.json()

    assert report["bidder_id"] == bidder.id
    assert report["compliance_score"] >= 80.0
    assert report["risk_assessment"]["risk_level"] == "LOW"
    assert report["recommendation"]["verdict"] == "QUALIFY"
    assert len(report["rules_evaluated"]) >= 3
    assert "Taxation" in report["score_breakdown"]["category_scores"]

    # Verify audit log was registered
    logs_after = db_session.query(AuditLog).filter(
        AuditLog.entity_id == str(bidder.id),
        AuditLog.action == "VERIFY"
    ).count()
    assert logs_after > logs_before

def test_api_compliance_report_get(officer_token, db_session):
    bidder = db_session.query(Bidder).first()
    assert bidder is not None

    resp = client.get(
        f"/api/compliance/report/{bidder.id}",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    report = resp.json()
    assert report["bidder_id"] == bidder.id
    assert "score_breakdown" in report
    assert "recommendation" in report

def test_existing_bidder_evaluate_endpoint_compatibility(officer_token, db_session):
    bidder = db_session.query(Bidder).filter(Bidder.company_name == "Alpha Data Systems Pvt Ltd").first()
    assert bidder is not None

    resp = client.post(
        f"/api/bidders/{bidder.id}/evaluate",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == bidder.id
    assert data["compliance_score"] >= 80.0
    assert data["composite_status"] in ["COMPLIANT", "FLAGGED"]
