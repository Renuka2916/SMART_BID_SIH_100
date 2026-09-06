import pytest
import sys, os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.document import Document, DocumentStatus
from app.models.compliance_check import ComplianceCheck
from app.models.audit_log import AuditLog
from app.utils.encryption import (
    encrypt_field,
    decrypt_field,
    mask_pan,
    mask_gstin,
    mask_udyam,
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

# ==============================================================================
# 1. AES-256 Cryptography & Masking Tests
# ==============================================================================

def test_aes_encryption_roundtrip():
    original_pan = "AAAPL1234K"
    original_gstin = "07AAAPL1234K1Z5"
    original_udyam = "UDYAM-DL-01-0012345"

    enc_pan = encrypt_field(original_pan)
    enc_gstin = encrypt_field(original_gstin)
    enc_udyam = encrypt_field(original_udyam)

    assert enc_pan != original_pan
    assert enc_gstin != original_gstin
    assert enc_udyam != original_udyam

    # Decrypt and verify exact match
    assert decrypt_field(enc_pan) == original_pan
    assert decrypt_field(enc_gstin) == original_gstin
    assert decrypt_field(enc_udyam) == original_udyam

def test_encryption_does_not_leak_plaintext():
    pan = "BRKPS9876Q"
    ciphertext = encrypt_field(pan)
    assert pan not in ciphertext
    assert "BRK" not in ciphertext
    assert "9876" not in ciphertext

def test_tampered_ciphertext_fails():
    pan = "ABCDE1234F"
    enc = encrypt_field(pan)
    # Corrupt middle byte of base64
    tampered = enc[:15] + ("X" if enc[15] != "X" else "Y") + enc[16:]
    with pytest.raises(ValueError, match="AES-256 decryption failed"):
        decrypt_field(tampered)

def test_masking_functions():
    assert mask_pan("ABCDE1234F") == "ABC****34F"
    assert mask_gstin("07ABCDE1234F1Z5") == "07A******1Z5"
    assert mask_udyam("UDYAM-DL-01-0029145") == "UDYAM-**-**-***9145"

# ==============================================================================
# 2. Data Integrity & Bidder Service Tests
# ==============================================================================

def test_create_bidder_and_verify_encrypted_pii(officer_token, db_session):
    # Find active tender
    tender = db_session.query(Tender).filter(Tender.tender_ref == "GEM/2026/B/1049281").first()
    assert tender is not None

    pan = "TSTNP9999R"
    gstin = "09TSTNP9999R1Z9"
    udyam = "UDYAM-UP-03-0099999"

    # Ensure clean state for test PAN
    existing = db_session.query(Bidder).filter(Bidder.pan_masked == "TST****99R").all()
    for b in existing:
        db_session.delete(b)
    db_session.commit()

    payload = {
        "company_name": "  Zenith   Compute   Systems Pvt Ltd  ",
        "pan": pan,
        "gstin": gstin,
        "udyam_no": udyam,
        "contact_email": "tenders@zenithsystems-test.in",
        "contact_phone": "+91 98765 43210"
    }

    # Submit application
    resp = client.post(
        f"/api/tenders/{tender.id}/bidders",
        json=payload,
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 201
    data = resp.json()
    bidder_id = data["id"]

    # Name normalized
    assert data["company_name"] == "Zenith Compute Systems Pvt Ltd"
    # Masked fields present
    assert data["pan_masked"] == "TST****99R"
    assert data["gstin_masked"] == "09T******1Z9"
    # Decrypted PII returned for Procurement Officer
    assert data["pan"] == pan
    assert data["gstin"] == gstin

    # Verify directly in Database that ciphertext is stored (not plaintext)
    raw_bidder = db_session.query(Bidder).filter(Bidder.id == bidder_id).first()
    assert raw_bidder.pan_encrypted != pan
    assert raw_bidder.gstin_encrypted != gstin
    assert decrypt_field(raw_bidder.pan_encrypted) == pan

    # Verify automatic generation of compliance checks matching tender requirements
    checks = db_session.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()
    assert len(checks) == len(tender.mandatory_requirements)
    check_keys = [c.requirement_key for c in checks]
    for req in tender.mandatory_requirements:
        assert req in check_keys

def test_duplicate_bidder_pan_rejection(officer_token, db_session):
    tender = db_session.query(Tender).filter(Tender.tender_ref == "GEM/2026/B/1049281").first()
    assert tender is not None

    duplicate_pan = "KLMNP5432R"
    payload = {
        "company_name": "Zenith Subsidiary Corp",
        "pan": duplicate_pan,
        "gstin": "09KLMNP5432R1Z2",
        "contact_email": "other@zenithsystems.in"
    }

    resp = client.post(
        f"/api/tenders/{tender.id}/bidders",
        json=payload,
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    # Should be rejected as duplicate submission
    assert resp.status_code == 400
    assert "has already submitted a bid" in resp.json()["detail"]

# ==============================================================================
# 3. Document Lifecycle & SHA-256 Hash Tests
# ==============================================================================

def test_document_lifecycle_and_audit(officer_token, db_session):
    # Retrieve existing bidder
    bidder = db_session.query(Bidder).filter(Bidder.company_name == "Alpha Data Systems Pvt Ltd").first()
    assert bidder is not None

    doc_payload = {
        "document_type": "OEM_MAF",
        "file_name": "enterprise_server_maf.pdf",
        "mime_type": "application/pdf",
        "storage_path": "/storage/tenders/maf_8912.pdf",
        "file_size_bytes": 1024000
    }

    # 1. Register Document
    upload_resp = client.post(
        f"/api/bidders/{bidder.id}/documents",
        json=doc_payload,
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "UPLOADED"
    assert len(doc_data["file_hash"]) == 64  # Valid SHA-256 length

    # 2. Update status to OCR_PROCESSING
    status_resp = client.put(
        f"/api/documents/{doc_id}/status",
        json={
            "status": "OCR_PROCESSING",
            "extracted_data": {"oem_name": "Dell Technologies", "validity": "2027-12-31"},
            "ocr_confidence": 0.94
        },
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "OCR_PROCESSING"
    assert status_resp.json()["ocr_confidence"] == 0.94

    # 3. Finalize status to AI_VERIFIED
    final_resp = client.put(
        f"/api/documents/{doc_id}/status",
        json={
            "status": "AI_VERIFIED",
            "extracted_data": {"oem_name": "Dell Technologies", "verified": True},
            "ocr_confidence": 0.97
        },
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert final_resp.status_code == 200
    assert final_resp.json()["status"] == "AI_VERIFIED"

# ==============================================================================
# 4. Audit Log Immutability & Traceability Tests
# ==============================================================================

def test_audit_logs_query_and_transparency(officer_token):
    resp = client.get(
        "/api/audit-logs?limit=10",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0

    first_log = data["items"][0]
    assert "action" in first_log
    assert "entity_type" in first_log
    assert "summary" in first_log

def test_audit_log_immutability_enforcement(db_session):
    # Fetch an existing audit log
    log = db_session.query(AuditLog).first()
    assert log is not None

    # Test that UPDATE is blocked by event listener
    log.summary = "Malicious unauthorized modification"
    with pytest.raises(RuntimeError, match="AuditLog records are strictly immutable and cannot be updated."):
        db_session.commit()

    db_session.rollback()

    # Test that DELETE is blocked by event listener
    db_session.delete(log)
    with pytest.raises(RuntimeError, match="AuditLog records are strictly immutable and cannot be deleted."):
        db_session.commit()

    db_session.rollback()

# ==============================================================================
# 5. Referential Integrity & Cascading Deletes
# ==============================================================================

def test_bidder_cascade_delete(db_session):
    # Create temporary bidder with a document and check
    tender = db_session.query(Tender).first()
    assert tender is not None

    temp_bidder = Bidder(
        tender_id=tender.id,
        company_name="Cascade Test Corp",
        pan_encrypted=encrypt_field("XYZWQ9988Z"),
        pan_masked=mask_pan("XYZWQ9988Z"),
        gstin_encrypted=encrypt_field("09XYZWQ9988Z1Z5"),
        gstin_masked=mask_gstin("09XYZWQ9988Z1Z5"),
        contact_email="cascade@test.com",
        composite_status="UNDER_REVIEW"
    )
    db_session.add(temp_bidder)
    db_session.commit()
    db_session.refresh(temp_bidder)

    temp_doc = Document(
        bidder_id=temp_bidder.id,
        document_type="PAN_CARD",
        file_name="test_pan.pdf",
        storage_path="/tmp/test.pdf",
        file_hash="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        status="UPLOADED"
    )
    temp_check = ComplianceCheck(
        bidder_id=temp_bidder.id,
        requirement_key="PAN",
        portal_name="INCOME_TAX_CBDT",
        status="PENDING"
    )
    db_session.add_all([temp_doc, temp_check])
    db_session.commit()

    bidder_id = temp_bidder.id
    doc_id = temp_doc.id
    check_id = temp_check.id

    # Now delete bidder and assert cascade delete to Document and ComplianceCheck
    db_session.delete(temp_bidder)
    db_session.commit()

    assert db_session.query(Bidder).filter(Bidder.id == bidder_id).first() is None
    assert db_session.query(Document).filter(Document.id == doc_id).first() is None
    assert db_session.query(ComplianceCheck).filter(ComplianceCheck.id == check_id).first() is None
