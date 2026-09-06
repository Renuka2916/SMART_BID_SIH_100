import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)

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

def test_get_statutory_requirements_catalog():
    resp = client.get("/api/tenders/requirements/templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) >= 8
    keys = [t["key"] for t in templates]
    assert "UDYAM" in keys
    assert "GST" in keys
    assert "PAN" in keys
    assert "MAKE_IN_INDIA" in keys
    assert "NON_BLACKLIST" in keys

def test_list_tenders_authorized(officer_token):
    resp = client.get(
        "/api/tenders",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1

def test_tender_search_and_filter(officer_token):
    # Search for Server
    resp = client.get(
        "/api/tenders?search=Server",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any("Server" in t["title"] for t in data["items"])

def test_tender_crud_lifecycle_as_procurement_officer(officer_token):
    now = datetime.now(timezone.utc)
    tender_payload = {
        "tender_ref": f"GEM/2026/TEST/{int(now.timestamp())}",
        "title": "Automated Testing Tender For Verification System",
        "description": "Integration test tender creation for compliance engine validation.",
        "category": "Goods",
        "estimated_value": 1500000.0,
        "department": "National Informatics Centre",
        "opening_date": (now - timedelta(days=1)).isoformat(),
        "closing_date": (now + timedelta(days=15)).isoformat(),
        "status": "Draft",
        "mandatory_requirements": ["UDYAM", "GST", "PAN", "MAKE_IN_INDIA"]
    }

    # 1. CREATE
    create_resp = client.post(
        "/api/tenders",
        json=tender_payload,
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    tender_id = created["id"]
    assert created["tender_ref"] == tender_payload["tender_ref"]
    assert "UDYAM" in created["mandatory_requirements"]

    # 2. READ
    get_resp = client.get(
        f"/api/tenders/{tender_id}",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == tender_id

    # 3. UPDATE
    update_payload = {
        "title": "Automated Testing Tender [UPDATED]",
        "estimated_value": 1800000.0,
        "mandatory_requirements": ["UDYAM", "GST", "PAN", "MAKE_IN_INDIA", "EPFO_ESIC"]
    }
    update_resp = client.put(
        f"/api/tenders/{tender_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["title"] == "Automated Testing Tender [UPDATED]"
    assert updated["estimated_value"] == 1800000.0
    assert "EPFO_ESIC" in updated["mandatory_requirements"]

    # 4. DELETE
    del_resp = client.delete(
        f"/api/tenders/{tender_id}",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert del_resp.status_code == 200

    # 5. VERIFY DELETED
    verify_resp = client.get(
        f"/api/tenders/{tender_id}",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert verify_resp.status_code == 404

def test_published_and_closed_tender_lifecycle_rules(officer_token):
    now = datetime.now(timezone.utc)
    tender_payload = {
        "tender_ref": f"GEM/2026/PUB/{int(now.timestamp())}",
        "title": "Published Tender Frozen Test",
        "category": "Goods",
        "estimated_value": 500000.0,
        "department": "Indian Railways",
        "opening_date": now.isoformat(),
        "closing_date": (now + timedelta(days=10)).isoformat(),
        "status": "Published",
        "mandatory_requirements": ["GST"]
    }
    create_resp = client.post(
        "/api/tenders",
        json=tender_payload,
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert create_resp.status_code == 201
    tid = create_resp.json()["id"]

    # Trying to edit metadata while Published must fail with 400
    edit_resp = client.put(
        f"/api/tenders/{tid}",
        json={"title": "Illegal Attempt to Modify Published Tender"},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert edit_resp.status_code == 400
    assert "Published tenders cannot be edited" in edit_resp.json()["detail"]

    # Transitioning status to 'Under Evaluation' is allowed
    transition_resp = client.put(
        f"/api/tenders/{tid}",
        json={"status": "Under Evaluation"},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert transition_resp.status_code == 200
    assert transition_resp.json()["status"] == "Under Evaluation"

    # In 'Under Evaluation', editing metadata is allowed
    eval_edit_resp = client.put(
        f"/api/tenders/{tid}",
        json={"title": "Evaluation Stage Specifications Updated"},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert eval_edit_resp.status_code == 200

    # Transition to Closed
    close_resp = client.put(
        f"/api/tenders/{tid}",
        json={"status": "Closed"},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert close_resp.status_code == 200

    # In Closed, editing is completely blocked
    closed_edit_resp = client.put(
        f"/api/tenders/{tid}",
        json={"status": "Draft"},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert closed_edit_resp.status_code == 400
    assert "Closed and cannot be modified" in closed_edit_resp.json()["detail"]

def test_rbac_bidder_cannot_create_tender(bidder_token):
    now = datetime.now(timezone.utc)
    tender_payload = {
        "tender_ref": "GEM/UNAUTHORIZED/001",
        "title": "Unauthorized Bidder Tender Attempt",
        "category": "Goods",
        "estimated_value": 500000.0,
        "department": "Unauthorized Corp",
        "opening_date": now.isoformat(),
        "closing_date": (now + timedelta(days=10)).isoformat(),
        "status": "Published",
        "mandatory_requirements": ["GST"]
    }

    # Should be rejected with 403 Forbidden
    resp = client.post(
        "/api/tenders",
        json=tender_payload,
        headers={"Authorization": f"Bearer {bidder_token}"}
    )
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]
