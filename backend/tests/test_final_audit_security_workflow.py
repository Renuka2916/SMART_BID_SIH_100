import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.audit_log import AuditLog, AuditAction

from app.audit.audit_log import calculate_log_hash
from app.audit.audit_service import (
    record_audit_event,
    get_audit_trail,
    export_audit_docket
)
from app.security.encryption_util import (
    encrypt_field,
    decrypt_field,
    mask_pan,
    mask_gstin,
    mask_udyam,
    verify_ciphertext_integrity
)
from app.security.failure_handling import (
    CircuitBreaker,
    handle_portal_outage,
    PortalOutageException
)
from app.security.retry_manager import (
    fetch_with_retry,
    RetryPolicy
)
from app.workflow.decision_controller import (
    validate_ai_safety_gate,
    enforce_officer_qualification_decision,
    DecisionSubmissionPayload
)

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def procurement_officer(db: Session):
    officer_role = db.query(Role).filter(Role.name == "Procurement Officer").first()
    officer = db.query(User).filter(User.email == "officer@smartbid.gov.in").first()
    if not officer:
        officer = User(
            email="officer@smartbid.gov.in",
            full_name="Rajesh Sharma",
            hashed_password="mock_password_hash",
            role_id=officer_role.id if officer_role else 1,
            is_active=True
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)
    return officer

@pytest.fixture
def test_bidder(db: Session, procurement_officer: User):
    tender = db.query(Tender).first()
    if not tender:
        tender = Tender(
            tender_ref="SMARTBID/2026/TEST/999",
            title="Test Infrastructure Tender",
            description="Test Description",
            category="Goods",
            estimated_value=1000000.0,
            department="Test Department",
            status="Published",
            mandatory_requirements=["GST", "PAN"],
            created_by_id=procurement_officer.id
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)

    bidder = db.query(Bidder).filter(Bidder.company_name == "Workflow Test Systems Pvt Ltd").first()
    if not bidder:
        bidder = Bidder(
            tender_id=tender.id,
            company_name="Workflow Test Systems Pvt Ltd",
            pan_encrypted=encrypt_field("ABCDE9999F"),
            pan_masked="ABC****99F",
            gstin_encrypted=encrypt_field("07ABCDE9999F1Z5"),
            gstin_masked="07ABC******1Z5",
            contact_email="workflow@testsystems.in",
            composite_status="UNDER_REVIEW",
            compliance_score=85.0
        )
        db.add(bidder)
        db.commit()
        db.refresh(bidder)
    return bidder


# ==============================================================================
# 1. Audit Trail Module Tests
# ==============================================================================

def test_audit_log_append_only_immutability(db: Session, procurement_officer: User):
    """Verifies that AuditLog records are strictly append-only and reject updates/deletions."""
    log = record_audit_event(
        db=db,
        user=procurement_officer,
        action=AuditAction.VERIFY.value,
        entity_type="TEST_AUDIT",
        entity_id="101",
        summary="Security compliance audit verification event"
    )
    assert log.id is not None

    # Verify update rejection at ORM level
    log.summary = "Tampered summary modification"
    with pytest.raises(RuntimeError, match="AuditLog records are strictly immutable"):
        db.commit()
    db.rollback()

    # Verify delete rejection at ORM level
    with pytest.raises(RuntimeError, match="AuditLog records are strictly immutable"):
        db.delete(log)
        db.commit()
    db.rollback()

def test_audit_log_hash_and_docket_export(db: Session, procurement_officer: User):
    """Verifies cryptographic hash computation and audit docket generation."""
    log = record_audit_event(
        db=db,
        user=procurement_officer,
        action=AuditAction.CREATE.value,
        entity_type="DOCKET_TEST",
        entity_id="202",
        summary="Audit entry for docket generation"
    )
    sha_hash = calculate_log_hash(log)
    assert len(sha_hash) == 64  # Valid SHA-256 hex string

    docket = export_audit_docket(db, entity_type="DOCKET_TEST", entity_id="202")
    assert docket["entity_type"] == "DOCKET_TEST"
    assert docket["total_records"] >= 1
    assert "records" in docket
    assert docket["records"][0]["sha256_hash"] == sha_hash


# ==============================================================================
# 2. Security & AES-256 Encryption Tests
# ==============================================================================

def test_aes_256_gcm_roundtrip_and_tamper_detection():
    """Verifies AES-256-GCM encryption, decryption, and tamper resistance."""
    plaintext = "07AAACZ1234K1Z1"
    cipher = encrypt_field(plaintext)
    assert cipher is not None
    assert cipher != plaintext

    # Valid Decryption
    decrypted = decrypt_field(cipher)
    assert decrypted == plaintext
    assert verify_ciphertext_integrity(cipher) is True

    # Tampered Ciphertext must fail
    tampered = cipher[:-4] + "AAAA"
    assert verify_ciphertext_integrity(tampered) is False
    with pytest.raises(ValueError, match="AES-256 decryption failed"):
        decrypt_field(tampered)

def test_identifier_masking_utilities():
    """Verifies consistent PII data masking."""
    assert mask_pan("ABCDE1234F") == "ABC****34F"
    assert mask_gstin("07ABCDE1234F1Z5") == "07ABC******1Z5"
    assert mask_udyam("UDYAM-DL-01-0029145") == "UDYAM-DL-**-***9145"


# ==============================================================================
# 3. Failure Handling & Circuit Breaker Tests
# ==============================================================================

def test_circuit_breaker_transitions():
    """Verifies CircuitBreaker state transitions: CLOSED -> OPEN -> HALF_OPEN."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=0.1)
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    # First failure
    cb.record_failure()
    assert cb.state == "CLOSED"

    # Second failure trips breaker
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False

    # Wait for recovery timeout
    time.sleep(0.12)
    assert cb.can_execute() is True
    assert cb.state == "HALF_OPEN"

    # Successful probe restores CLOSED
    cb.record_success()
    assert cb.state == "CLOSED"

def test_portal_outage_transition_to_pending_manual_review(db: Session, test_bidder: Bidder, procurement_officer: User):
    """Verifies that an external portal outage marks the bidder as PENDING_MANUAL_REVIEW."""
    res = handle_portal_outage(
        db=db,
        bidder_id=test_bidder.id,
        portal_id="GSTN_PORTAL",
        error_message="Gateway Timeout 504 from GSTN API",
        current_user=procurement_officer
    )
    assert res["new_status"] == "PENDING_MANUAL_REVIEW"
    assert res["outage_portal"] == "GSTN_PORTAL"

    db.refresh(test_bidder)
    assert test_bidder.composite_status == "PENDING_MANUAL_REVIEW"


# ==============================================================================
# 4. Retry Manager Tests
# ==============================================================================

def test_retry_manager_success_after_transient_failure():
    """Verifies fetch_with_retry successfully recovers from transient errors."""
    attempts = 0

    async def flaky_fetch():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionResetError("Transient network glitch")
        return {"status": "SUCCESS", "portal": "EPFO"}

    policy = RetryPolicy(max_retries=3, base_delay_sec=0.01, max_delay_sec=0.05, jitter=False)
    result = asyncio.run(fetch_with_retry("TEST_PORTAL_EPFO", flaky_fetch, policy=policy))
    assert result["status"] == "SUCCESS"
    assert attempts == 2

def test_retry_manager_exhaustion_raises_portal_outage():
    """Verifies fetch_with_retry raises PortalOutageException when retries are exhausted."""
    async def always_failing_fetch():
        raise TimeoutError("Portal server dead")

    policy = RetryPolicy(max_retries=2, base_delay_sec=0.01, max_delay_sec=0.02, jitter=False)
    with pytest.raises(PortalOutageException, match="unreachable after 2 attempts"):
        asyncio.run(fetch_with_retry("DEAD_PORTAL", always_failing_fetch, policy=policy))


# ==============================================================================
# 5. AI Safety Gate & Workflow Decision Control Tests
# ==============================================================================

def test_ai_safety_gate_rejects_unauthenticated():
    """AI Safety Gate must strictly reject automated/unauthenticated qualification."""
    with pytest.raises(Exception):
        validate_ai_safety_gate(None)

def test_officer_decision_validation_and_enforcement(db: Session, test_bidder: Bidder, procurement_officer: User):
    """Verifies mandatory 15-char remarks validation and formal determination commitment."""
    # Remarks shorter than 15 characters must be rejected
    with pytest.raises(ValueError, match="at least 15 characters"):
        DecisionSubmissionPayload(
            decision="QUALIFIED",
            remarks="Short"
        )

    # Valid decision submission
    valid_payload = DecisionSubmissionPayload(
        decision="QUALIFIED",
        remarks="All mandatory statutory credentials, GST, PAN, and local content criteria verified compliant.",
        pinned_evidence=[{"key": "GST", "status": "VERIFIED"}]
    )

    updated_bidder = enforce_officer_qualification_decision(
        db=db,
        bidder_id=test_bidder.id,
        payload=valid_payload,
        current_user=procurement_officer
    )
    assert updated_bidder.composite_status == "QUALIFIED"

    # Verify audit log was committed
    total, logs = get_audit_trail(db, entity_type="BIDDER", entity_id=str(test_bidder.id))
    assert total >= 1
    assert logs[0].action == AuditAction.DECISION_OVERRIDE.value


# ==============================================================================
# 6. Security Headers & Concurrency Load Tests
# ==============================================================================

def test_security_headers_enforced():
    """Verifies that all Government-grade security headers are present in HTTP responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_concurrent_api_load():
    """Verifies system responsiveness under 30 concurrent health & catalog queries."""
    start_time = time.time()

    def make_request():
        r = client.get("/health")
        return r.status_code

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(30)]
        results = [f.result() for f in futures]

    total_time = time.time() - start_time
    assert all(code == 200 for code in results)
    assert total_time < 3.0, f"Concurrent load took {total_time:.2f}s, expected < 3.0s"
