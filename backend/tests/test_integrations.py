import pytest
import asyncio
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus,
    normalize_legal_name,
    calculate_name_similarity
)
from app.utils.api_client import GovtAPIClient
from app.integrations.manager import portal_manager
from app.integrations.udyam_api import UdyamFetcher
from app.integrations.gstn_api import GstnFetcher
from app.integrations.pan_income_tax_api import PanIncomeTaxFetcher
from app.integrations.mca21_api import Mca21Fetcher
from app.integrations.epfo_api import EpfoFetcher
from app.integrations.esic_api import EsicFetcher
from app.integrations.startup_india_api import StartupIndiaFetcher
from app.integrations.nsic_api import NsicFetcher
from app.integrations.digilocker_api import DigiLockerFetcher
from app.integrations.blacklisting_api import BlacklistingFetcher
from app.integrations.dpiit_mii_api import DpiitMiiFetcher
from app.integrations.bis_api import BisFetcher
from app.integrations.oem_auth_api import OemAuthFetcher
from app.integrations.gem_incident_api import GemIncidentFetcher
from app.integrations.turnover_ca_api import TurnoverCaFetcher

client = TestClient(app)

@pytest.fixture
def sample_identifiers():
    return BidderIdentifiers(
        company_name="Alpha Data Systems Pvt Ltd",
        pan="ABCDE1234F",
        gstin="07ABCDE1234F1Z5",
        udyam_no="UDYAM-DL-01-0029145",
        cin="U72900DL2018PTC334567",
        epfo_code="DLCPM0045892000",
        esic_code="11000987650001001",
        startup_dipp_no="DIPP54982",
        nsic_no="NSIC/SPRS/2022/98412",
        contact_email="procurement@alphadatasys.com",
        contact_phone="+91 98101 23456"
    )

@pytest.fixture
def officer_token():
    resp = client.post(
        "/api/auth/login",
        json={"email": "officer@smartbid.gov.in", "password": "SmartBid@2026!Officer"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_name_normalization_and_similarity():
    # Identical after legal expansion
    sim = calculate_name_similarity("Alpha Data Systems Private Limited", "ALPHA DATA SYSTEMS PVT LTD")
    assert sim >= 0.90

    # Slight variation
    sim2 = calculate_name_similarity("Zenith Compute Systems Pvt Ltd", "Zenith Compute Systems Limited")
    assert sim2 >= 0.75

    # Completely different entity
    sim3 = calculate_name_similarity("Alpha Data Systems Pvt Ltd", "Random Other Corp")
    assert sim3 < 0.40

def test_portal_manager_catalog():
    portals = portal_manager.get_all_registered_portals()
    assert len(portals) == 15
    portal_ids = [p["portal_id"] for p in portals]
    expected_ids = [
        "UDYAM", "GSTN", "PAN_INCOME_TAX", "MCA21", "EPFO", "ESIC",
        "STARTUP_INDIA", "NSIC", "DIGILOCKER", "NON_BLACKLIST",
        "MAKE_IN_INDIA", "BIS_CERTIFICATION", "OEM_AUTH", "GEM_INCIDENT", "TURNOVER"
    ]
    for eid in expected_ids:
        assert eid in portal_ids

@pytest.mark.anyio
async def test_all_15_fetchers_execute_and_normalize(sample_identifiers):
    fetchers = [
        UdyamFetcher(),
        GstnFetcher(),
        PanIncomeTaxFetcher(),
        Mca21Fetcher(),
        EpfoFetcher(),
        EsicFetcher(),
        StartupIndiaFetcher(),
        NsicFetcher(),
        DigiLockerFetcher(),
        BlacklistingFetcher(),
        DpiitMiiFetcher(),
        BisFetcher(),
        OemAuthFetcher(),
        GemIncidentFetcher(),
        TurnoverCaFetcher()
    ]

    for fetcher in fetchers:
        res = await fetcher.fetch_data(sample_identifiers)
        assert isinstance(res, NormalizedPortalResponse)
        assert res.portal_id == fetcher.portal_id
        assert res.portal_name == fetcher.portal_name
        assert res.status in (PortalStatus.VERIFIED, PortalStatus.FLAGGED)
        assert res.confidence_score > 0.0
        assert isinstance(res.normalized_data, dict)
        assert isinstance(res.raw_data, dict)
        assert res.latency_ms >= 0.0

@pytest.mark.anyio
async def test_parallel_fetch_all_for_bidder(sample_identifiers):
    results = await portal_manager.fetch_all_for_bidder(sample_identifiers)
    assert len(results) == 15
    score, status, discrepancies = portal_manager.aggregate_compliance(results)
    assert score >= 80.0
    assert status == "COMPLIANT"

@pytest.mark.anyio
async def test_flagged_entity_detection():
    flagged_bidder = BidderIdentifiers(
        company_name="NetSecure Infotech LLP",
        pan="AABCN9876K",
        gstin="27AABCN9876K1ZY"
    )
    fetcher = BlacklistingFetcher()
    res = await fetcher.fetch_data(flagged_bidder)
    assert res.status == PortalStatus.FLAGGED
    assert res.is_valid is False
    assert len(res.discrepancies) > 0
    assert any("debarment registry" in d for d in res.discrepancies)

def test_api_list_registered_portals(officer_token):
    resp = client.get(
        "/api/integrations/portals",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_portals"] == 15
    assert len(data["items"]) == 15

def test_api_fetch_single_portal(officer_token, sample_identifiers):
    resp = client.post(
        "/api/integrations/fetch/GSTN",
        json=sample_identifiers.model_dump(),
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["portal_id"] == "GSTN"
    assert data["status"] == "VERIFIED"
    assert data["is_valid"] is True
    assert "gstin" in data["normalized_data"]

def test_api_verify_bidder_across_all_portals(officer_token):
    # Fetch existing bidder ID 1 (Alpha Data Systems)
    resp = client.post(
        "/api/integrations/verify-bidder/1",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["bidder_id"] == 1
    assert data["total_portals_checked"] == 15
    assert data["compliance_score"] >= 80.0
    assert "portal_results" in data
    assert len(data["portal_results"]) == 15
    assert "UDYAM" in data["portal_results"]
    assert "GSTN" in data["portal_results"]
    assert "PAN_INCOME_TAX" in data["portal_results"]
    assert "DIGILOCKER" in data["portal_results"]
