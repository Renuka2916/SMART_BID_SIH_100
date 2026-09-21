import io
import pytest
from fastapi.testclient import TestClient
import pypdf
import numpy as np
import cv2
from PIL import Image

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.ai.ocr_pipeline import ocr_pipeline
from app.ai.nlp_extractor import nlp_extractor
from app.ai.signature_verifier import signature_verifier
from app.ai.document_processor import document_processor
from app.schemas.ai_extraction_result import AIExtractionResult

client = TestClient(app)

@pytest.fixture
def officer_token():
    resp = client.post(
        "/api/auth/login",
        json={"email": "officer@smartbid.gov.in", "password": "SmartBid@2026!Officer"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

@pytest.fixture
def sample_pdf_bytes():
    """Generates a valid synthetic digital PDF in-memory using pypdf."""
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    
    # We can write text content or create a basic stream
    text = (
        "GOVERNMENT OF INDIA - FORM GST REG-06\n"
        "Registration Certificate\n"
        "Registration Number (GSTIN): 07ABCDE1234F1Z5\n"
        "Legal Name: Alpha Data Systems Private Limited\n"
        "Trade Name: Alpha Data Systems\n"
        "Permanent Account Number: ABCDE1234F\n"
        "Date of Liability: 01/07/2017\n"
        "Period of Validity: From 01/07/2017 to Perpetual\n"
        "Make in India Local Content: 68.5% (Class-I Local Supplier)\n"
        "Udyam Number: UDYAM-DL-01-0029145\n"
        "ICAI UDIN: 26084920AAAAAB9812\n"
        "Authorized Signatory & Seal: Attested with signature and stamp.\n"
    )
    
    # In pypdf, we can write an object with a text stream
    # A cleaner cross-platform way for unit testing extract_text_from_pdf:
    # Use pypdf with annotation or directly test processor on text/PDF
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue(), text

@pytest.fixture
def sample_image_bytes():
    """Generates a synthetic certificate image with blue signature and round stamp."""
    img = np.ones((600, 500, 3), dtype=np.uint8) * 255
    # Add title text
    cv2.putText(img, "GOVERNMENT OF INDIA", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "GSTIN: 07ABCDE1234F1Z5", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.putText(img, "PAN: ABCDE1234F", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    # Draw blue signature stroke in bottom 30%
    cv2.line(img, (100, 500), (220, 480), (200, 50, 20), 3)
    cv2.circle(img, (150, 490), 15, (180, 40, 10), 2)
    # Draw circular stamp in bottom half
    cv2.circle(img, (380, 480), 40, (150, 30, 20), 2)
    cv2.circle(img, (380, 480), 32, (150, 30, 20), 1)

    _, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()

def test_opencv_preprocessing(sample_image_bytes):
    thresh, angle = ocr_pipeline.preprocess_image_cv2(sample_image_bytes)
    assert thresh is not None
    assert isinstance(thresh, np.ndarray)
    assert thresh.shape[0] == 600
    assert thresh.shape[1] == 500

def test_signature_and_stamp_cv_detection(sample_image_bytes):
    sig_res = signature_verifier.verify_from_image_bytes(sample_image_bytes)
    assert sig_res.has_signature is True
    assert sig_res.signature_confidence >= 0.80
    assert sig_res.has_stamp_seal is True
    assert sig_res.seal_confidence >= 0.80

def test_nlp_entity_extractor():
    sample_text = """
    GOVERNMENT OF INDIA - MINISTRY OF MSME
    UDYAM REGISTRATION CERTIFICATE
    Udyam Registration Number : UDYAM-UP-03-0054321
    Name of Enterprise : Zenith Compute Systems Pvt Ltd
    Major Activity : Manufacturing
    PAN : KLMCP5432R
    GSTIN : 09KLMCP5432R1Z2
    Local Content : 65% Local Content verified
    ICAI UDIN : 25012345AAAAAB1234
    Authorized Signatory
    """
    entities = nlp_extractor.extract_all_entities(sample_text)
    
    # 1. GSTIN
    assert "gstin" in entities
    assert entities["gstin"]["gstin"] == "09KLMCP5432R1Z2"
    assert entities["gstin"]["state_name"] == "Uttar Pradesh"
    assert entities["gstin"]["embedded_pan"] == "KLMCP5432R"

    # 2. PAN
    assert "pan" in entities
    assert entities["pan"]["pan"] == "KLMCP5432R"
    assert entities["pan"]["entity_type"] == "Company"

    # 3. Udyam
    assert "udyam" in entities
    assert entities["udyam"]["udyam_no"] == "UDYAM-UP-03-0054321"

    # 4. Make in India
    assert "make_in_india" in entities
    assert entities["make_in_india"]["percentage"] == 65.0
    assert entities["make_in_india"]["meets_class_1"] is True

    # 5. UDIN
    assert "udin" in entities
    assert entities["udin"]["udin"] == "25012345AAAAAB1234"

def test_document_processor_consistent_pass():
    doc_text = """
    CERTIFICATE OF REGISTRATION UNDER GST
    Legal Name : Alpha Data Systems Private Limited
    GSTIN : 07ABCDE1234F1Z5
    PAN : ABCDE1234F
    UDYAM-DL-01-0029145
    Local Content: 60%
    Authorized Signatory attested with seal
    """
    res: AIExtractionResult = document_processor.process(
        file_bytes=doc_text.encode("utf-8"),
        filename="gst_cert.txt",
        doc_type="GST_CERTIFICATE",
        expected_bidder_name="Alpha Data Systems Pvt Ltd"
    )
    assert res.recommended_status == "AI_VERIFIED"
    assert res.entities["gstin"]["gstin"] == "07ABCDE1234F1Z5"
    assert any(c.rule_name == "PAN_GSTIN_CONSISTENCY" and c.passed for c in res.validation_checks)
    assert any(c.rule_name == "LEGAL_NAME_MATCH" and c.passed for c in res.validation_checks)

def test_document_processor_flagged_pan_mismatch():
    # PAN KLMNP5432R contradicts GSTIN embedded PAN ABCDE1234F
    mismatch_text = """
    GST CERTIFICATE
    Legal Name : Alpha Data Systems Private Limited
    GSTIN : 07ABCDE1234F1Z5
    PAN : KLMNP5432R
    Authorized Signatory
    """
    res: AIExtractionResult = document_processor.process(
        file_bytes=mismatch_text.encode("utf-8"),
        filename="tampered_cert.txt",
        doc_type="GST_CERTIFICATE"
    )
    assert res.recommended_status == "FLAGGED"
    pan_check = next(c for c in res.validation_checks if c.rule_name == "PAN_GSTIN_CONSISTENCY")
    assert pan_check.passed is False
    assert pan_check.severity == "HIGH"

def test_api_extract_uploaded_file(officer_token):
    content = b"""
    MINISTRY OF COMMERCE AND INDUSTRY
    MAKE IN INDIA SELF-DECLARATION
    Company: Alpha Data Systems Private Limited
    GSTIN: 07ABCDE1234F1Z5
    PAN: ABCDE1234F
    Local Content: 72.5% Local Content
    Class-I Local Supplier
    Authorized Signatory: Signed
    """
    resp = client.post(
        "/api/ai/extract-file",
        files={"file": ("mii_declaration.txt", content, "text/plain")},
        data={"doc_type": "MAKE_IN_INDIA_DECLARATION", "expected_bidder_name": "Alpha Data Systems Pvt Ltd"},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_status"] == "AI_VERIFIED"
    assert data["entities"]["make_in_india"]["percentage"] == 72.5
    assert data["entities"]["make_in_india"]["meets_class_1"] is True

def test_api_process_stored_document(officer_token):
    # Retrieve documents for bidder 1
    docs_resp = client.get(
        "/api/bidders/1/documents",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert docs_resp.status_code == 200
    docs = docs_resp.json()["items"]
    assert len(docs) > 0
    doc_id = docs[0]["id"]

    # Trigger AI processing on document
    proc_resp = client.post(
        f"/api/ai/documents/{doc_id}/process-ai",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert proc_resp.status_code == 200
    p_data = proc_resp.json()
    assert p_data["document_id"] == doc_id
    assert p_data["status"] in ("AI_VERIFIED", "FLAGGED")
    assert p_data["ocr_confidence"] is not None

    # Query extraction details
    res_resp = client.get(
        f"/api/ai/documents/{doc_id}/ai-results",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert res_resp.status_code == 200
    r_data = res_resp.json()
    assert r_data["document_id"] == doc_id
    assert "entities" in r_data["extracted_data"]
