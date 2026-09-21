import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from database import engine, SessionLocal, Base
from app.models.role import Role
from app.models.user import User
from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.document import Document, DocumentStatus
from app.models.compliance_check import ComplianceCheck, ComplianceCheckStatus
from app.models.audit_log import AuditLog, AuditAction
from app.core.security import get_password_hash
from app.utils.encryption import (
    encrypt_field,
    mask_pan,
    mask_gstin,
    mask_udyam
)

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def seed_database():
    print("[Seed] Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Roles
        roles_data = [
            {"name": "Procurement Officer", "description": "Government tender creation, evaluation, and bidder verification decision authority"},
            {"name": "Admin", "description": "System administrator with platform configuration rights"},
            {"name": "Bidder", "description": "Registered vendor submitting bids and statutory documentation"},
            {"name": "Auditor", "description": "Independent oversight officer inspecting compliance logs and audit trails"}
        ]

        roles = {}
        for r_info in roles_data:
            role = db.query(Role).filter(Role.name == r_info["name"]).first()
            if not role:
                role = Role(name=r_info["name"], description=r_info["description"])
                db.add(role)
                db.commit()
                db.refresh(role)
                print(f"[Seed] Created role: {role.name}")
            roles[role.name] = role

        # 2. Seed Default Procurement Officer
        officer_email = "officer@smartbid.gov.in"
        officer = db.query(User).filter(User.email == officer_email).first()
        if not officer:
            officer = User(
                email=officer_email,
                full_name="Rajesh Sharma",
                hashed_password=get_password_hash("SmartBid@2026!Officer"),
                role_id=roles["Procurement Officer"].id,
                department="SmartBid Central Public Procurement Directorate",
                is_active=True
            )
            db.add(officer)
            db.commit()
            db.refresh(officer)
            print(f"[Seed] Created Procurement Officer: {officer.email} (Password: SmartBid@2026!Officer)")
        else:
            print(f"[Seed] Procurement Officer {officer_email} already exists.")

        # Seed an alternative Bidder user for RBAC testing
        bidder_email = "bidder@techcorp.in"
        bidder_user = db.query(User).filter(User.email == bidder_email).first()
        if not bidder_user:
            bidder_user = User(
                email=bidder_email,
                full_name="Vikram Mehta",
                hashed_password=get_password_hash("Bidder@2026!Pass"),
                role_id=roles["Bidder"].id,
                department="TechCorp Solutions Pvt Ltd",
                is_active=True
            )
            db.add(bidder_user)
            db.commit()
            db.refresh(bidder_user)
            print(f"[Seed] Created Bidder user: {bidder_user.email} for RBAC testing")

        # 3. Seed Realistic SmartBid Tenders
        tenders_data = [
            {
                "tender_ref": "SMARTBID/2026/B/1049281",
                "title": "Procurement of High-Performance Server Infrastructure & AI Compute Racks",
                "description": "Supply, installation, commissioning, and 3-year warranty maintenance of enterprise server infrastructure for automated verification workloads.",
                "category": "Goods",
                "estimated_value": 4500000.0,
                "department": "Ministry of Electronics & Information Technology",
                "opening_date": datetime.now(timezone.utc) - timedelta(days=5),
                "closing_date": datetime.now(timezone.utc) + timedelta(days=20),
                "status": "Published",
                "mandatory_requirements": [
                    "UDYAM", "GST", "PAN", "MAKE_IN_INDIA", "OEM_AUTH", "DIGILOCKER", "NON_BLACKLIST", "TURNOVER"
                ]
            },
            {
                "tender_ref": "SMARTBID/2026/B/1054320",
                "title": "Comprehensive Facility Management & Data Centre Operations Services",
                "description": "24x7 facility management, electrical maintenance, security surveillance, and operational support for central data storage facilities.",
                "category": "Services",
                "estimated_value": 7850000.0,
                "department": "Department of Defence Production",
                "opening_date": datetime.now(timezone.utc) - timedelta(days=12),
                "closing_date": datetime.now(timezone.utc) + timedelta(days=8),
                "status": "Under Evaluation",
                "mandatory_requirements": [
                    "UDYAM", "GST", "PAN", "EPFO_ESIC", "NON_BLACKLIST", "TURNOVER", "DIGILOCKER"
                ]
            },
            {
                "tender_ref": "SMARTBID/2026/B/1067812",
                "title": "Supply of Desktop Workstations and Certified Secure Peripherals",
                "description": "Turnkey delivery of 350 enterprise desktop workstations with BIS certification and energy star compliance for regional CPSE offices.",
                "category": "Goods",
                "estimated_value": 2200000.0,
                "department": "Ministry of Heavy Industries",
                "opening_date": datetime.now(timezone.utc) - timedelta(days=2),
                "closing_date": datetime.now(timezone.utc) + timedelta(days=25),
                "status": "Published",
                "mandatory_requirements": [
                    "UDYAM", "GST", "PAN", "MAKE_IN_INDIA", "STARTUP_INDIA", "OEM_AUTH", "NON_BLACKLIST"
                ]
            }
        ]

        tenders_map = {}
        for t_info in tenders_data:
            tender = db.query(Tender).filter(Tender.tender_ref == t_info["tender_ref"]).first()
            if not tender:
                tender = Tender(
                    tender_ref=t_info["tender_ref"],
                    title=t_info["title"],
                    description=t_info["description"],
                    category=t_info["category"],
                    estimated_value=t_info["estimated_value"],
                    department=t_info["department"],
                    opening_date=t_info["opening_date"],
                    closing_date=t_info["closing_date"],
                    status=t_info["status"],
                    mandatory_requirements=t_info["mandatory_requirements"],
                    created_by_id=officer.id
                )
                db.add(tender)
                db.commit()
                db.refresh(tender)
                print(f"[Seed] Created tender: {tender.tender_ref}")
            tenders_map[tender.tender_ref] = tender

        # 4. Seed Bidders with AES-256 Encrypted PII
        server_tender = tenders_map.get("SMARTBID/2026/B/1049281")
        if server_tender:
            # Check if Alpha Data Systems exists
            b1 = db.query(Bidder).filter(Bidder.tender_id == server_tender.id, Bidder.company_name == "Alpha Data Systems Pvt Ltd").first()
            if not b1:
                pan1 = "ABCDE1234F"
                gstin1 = "07ABCDE1234F1Z5"
                udyam1 = "UDYAM-DL-01-0029145"

                b1 = Bidder(
                    tender_id=server_tender.id,
                    company_name="Alpha Data Systems Pvt Ltd",
                    pan_encrypted=encrypt_field(pan1),
                    pan_masked=mask_pan(pan1),
                    gstin_encrypted=encrypt_field(gstin1),
                    gstin_masked=mask_gstin(gstin1),
                    udyam_no_encrypted=encrypt_field(udyam1),
                    udyam_no_masked=mask_udyam(udyam1),
                    contact_email="procurement@alphadatasys.com",
                    contact_phone="+91 98101 23456",
                    composite_status="COMPLIANT",
                    compliance_score=94.0
                )
                db.add(b1)
                db.commit()
                db.refresh(b1)
                print(f"[Seed] Created Bidder '{b1.company_name}' with AES-256 encrypted identifiers")

                # Add Documents for Bidder 1
                doc1 = Document(
                    bidder_id=b1.id,
                    document_type="PAN_CARD",
                    file_name="alpha_pan_card.pdf",
                    file_size_bytes=245000,
                    mime_type="application/pdf",
                    storage_path="/secure/vault/alpha_pan.pdf",
                    file_hash=sha256("alpha_pan_sample_content"),
                    status=DocumentStatus.AI_VERIFIED.value,
                    extracted_data={"pan": pan1, "entity_name": "ALPHA DATA SYSTEMS PVT LTD"},
                    ocr_confidence=0.98
                )
                doc2 = Document(
                    bidder_id=b1.id,
                    document_type="GST_CERTIFICATE",
                    file_name="gst_registration_reg06.pdf",
                    file_size_bytes=520000,
                    mime_type="application/pdf",
                    storage_path="/secure/vault/alpha_gst.pdf",
                    file_hash=sha256("alpha_gst_sample_content"),
                    status=DocumentStatus.AI_VERIFIED.value,
                    extracted_data={"gstin": gstin1, "legal_name": "ALPHA DATA SYSTEMS PRIVATE LIMITED"},
                    ocr_confidence=0.96
                )
                db.add_all([doc1, doc2])

                # Add Compliance Checks for Bidder 1
                checks1 = [
                    ComplianceCheck(
                        bidder_id=b1.id,
                        requirement_key="GST",
                        portal_name="GSTN",
                        status=ComplianceCheckStatus.VERIFIED.value,
                        check_details={"portal": "GSTN", "gstin_status": "ACTIVE", "filing_status": "UP_TO_DATE"},
                        score_contribution=15.0,
                        verified_at=datetime.now(timezone.utc)
                    ),
                    ComplianceCheck(
                        bidder_id=b1.id,
                        requirement_key="UDYAM",
                        portal_name="MSME_UDYAM",
                        status=ComplianceCheckStatus.VERIFIED.value,
                        check_details={"portal": "MSME", "enterprise_type": "SMALL", "classification": "MANUFACTURING"},
                        score_contribution=15.0,
                        verified_at=datetime.now(timezone.utc)
                    ),
                    ComplianceCheck(
                        bidder_id=b1.id,
                        requirement_key="MAKE_IN_INDIA",
                        portal_name="DPIIT_MII",
                        status=ComplianceCheckStatus.FLAGGED.value,
                        check_details={"local_content_declared": "62%"},
                        discrepancy_notes="Local content self-declaration uploaded; statutory CA certificate pending.",
                        score_contribution=10.0,
                        verified_at=datetime.now(timezone.utc)
                    )
                ]
                db.add_all(checks1)

                # Add Audit Log for Bidder 1 creation
                audit1 = AuditLog(
                    user_id=officer.id,
                    user_email=officer.email,
                    user_role="Procurement Officer",
                    action=AuditAction.CREATE.value,
                    entity_type="BIDDER",
                    entity_id=str(b1.id),
                    summary=f"Created Bidder '{b1.company_name}' with encrypted PII and automated compliance checks.",
                    new_values={"company_name": b1.company_name, "pan_masked": b1.pan_masked, "score": 94.0}
                )
                db.add(audit1)
                db.commit()

            # Bidder 2: NetSecure Infotech LLP
            b2 = db.query(Bidder).filter(Bidder.tender_id == server_tender.id, Bidder.company_name == "NetSecure Infotech LLP").first()
            if not b2:
                pan2 = "AABCN9876K"
                gstin2 = "27AABCN9876K1ZY"
                udyam2 = "UDYAM-MH-02-0048190"

                b2 = Bidder(
                    tender_id=server_tender.id,
                    company_name="NetSecure Infotech LLP",
                    pan_encrypted=encrypt_field(pan2),
                    pan_masked=mask_pan(pan2),
                    gstin_encrypted=encrypt_field(gstin2),
                    gstin_masked=mask_gstin(gstin2),
                    udyam_no_encrypted=encrypt_field(udyam2),
                    udyam_no_masked=mask_udyam(udyam2),
                    contact_email="tenders@netsecure.in",
                    contact_phone="+91 99200 87654",
                    composite_status="FLAGGED",
                    compliance_score=68.0
                )
                db.add(b2)
                db.commit()
                db.refresh(b2)
                print(f"[Seed] Created Bidder '{b2.company_name}' with AES-256 encrypted identifiers")

                doc3 = Document(
                    bidder_id=b2.id,
                    document_type="PAN_CARD",
                    file_name="netsecure_pan.pdf",
                    file_size_bytes=190000,
                    mime_type="application/pdf",
                    storage_path="/secure/vault/netsecure_pan.pdf",
                    file_hash=sha256("netsecure_pan_content"),
                    status=DocumentStatus.AI_VERIFIED.value,
                    extracted_data={"pan": pan2},
                    ocr_confidence=0.95
                )
                db.add(doc3)

                audit2 = AuditLog(
                    user_id=officer.id,
                    user_email=officer.email,
                    user_role="Procurement Officer",
                    action=AuditAction.CREATE.value,
                    entity_type="BIDDER",
                    entity_id=str(b2.id),
                    summary=f"Created Bidder '{b2.company_name}' under Tender '{server_tender.tender_ref}'.",
                    new_values={"company_name": b2.company_name, "pan_masked": b2.pan_masked}
                )
                db.add(audit2)
                db.commit()

            # Bidder 3: Zenith Compute Systems Pvt Ltd
            b3 = db.query(Bidder).filter(Bidder.tender_id == server_tender.id, Bidder.company_name == "Zenith Compute Systems Pvt Ltd").first()
            if not b3:
                pan3 = "ZENITH123K"
                gstin3 = "27ZENITH123K1ZY"
                udyam3 = "UDYAM-MH-02-0048191"

                b3 = Bidder(
                    tender_id=server_tender.id,
                    company_name="Zenith Compute Systems Pvt Ltd",
                    pan_encrypted=encrypt_field(pan3),
                    pan_masked=mask_pan(pan3),
                    gstin_encrypted=encrypt_field(gstin3),
                    gstin_masked=mask_gstin(gstin3),
                    udyam_no_encrypted=encrypt_field(udyam3),
                    udyam_no_masked=mask_udyam(udyam3),
                    contact_email="tenders@zenith.in",
                    contact_phone="+91 99200 87655",
                    composite_status="COMPLIANT",
                    compliance_score=85.0
                )
                db.add(b3)
                db.commit()
                db.refresh(b3)
                print(f"[Seed] Created Bidder '{b3.company_name}' with AES-256 encrypted identifiers")
                
                doc_zenith = Document(
                    bidder_id=b3.id,
                    document_type="PAN_CARD",
                    file_name="zenith_pan.pdf",
                    file_size_bytes=210000,
                    mime_type="application/pdf",
                    storage_path="/secure/vault/zenith_pan.pdf",
                    file_hash=sha256("zenith_pan_content"),
                    status=DocumentStatus.AI_VERIFIED.value,
                    extracted_data={"pan": pan3, "entity_name": "ZENITH COMPUTE SYSTEMS PVT LTD"},
                    ocr_confidence=0.97
                )
                db.add(doc_zenith)

                check_zenith = ComplianceCheck(
                    bidder_id=b3.id,
                    requirement_key="GST",
                    portal_name="GSTN",
                    status=ComplianceCheckStatus.VERIFIED.value,
                    check_details={"portal": "GSTN", "gstin_status": "ACTIVE", "filing_status": "UP_TO_DATE"},
                    score_contribution=15.0,
                    verified_at=datetime.now(timezone.utc)
                )
                db.add(check_zenith)

                audit_zenith = AuditLog(
                    user_id=officer.id,
                    user_email=officer.email,
                    user_role="Procurement Officer",
                    action=AuditAction.CREATE.value,
                    entity_type="BIDDER",
                    entity_id=str(b3.id),
                    summary=f"Created Bidder '{b3.company_name}' under Tender '{server_tender.tender_ref}'.",
                    new_values={"company_name": b3.company_name, "pan_masked": b3.pan_masked}
                )
                db.add(audit_zenith)
                db.commit()

            # Bidder 4: Workflow Test Systems Pvt Ltd
            b4 = db.query(Bidder).filter(Bidder.tender_id == server_tender.id, Bidder.company_name == "Workflow Test Systems Pvt Ltd").first()
            if not b4:
                pan4 = "WORKF123K"
                gstin4 = "27WORKF123K1ZY"
                udyam4 = "UDYAM-MH-02-0048192"

                b4 = Bidder(
                    tender_id=server_tender.id,
                    company_name="Workflow Test Systems Pvt Ltd",
                    pan_encrypted=encrypt_field(pan4),
                    pan_masked=mask_pan(pan4),
                    gstin_encrypted=encrypt_field(gstin4),
                    gstin_masked=mask_gstin(gstin4),
                    udyam_no_encrypted=encrypt_field(udyam4),
                    udyam_no_masked=mask_udyam(udyam4),
                    contact_email="tenders@workflow.in",
                    contact_phone="+91 99200 87656",
                    composite_status="FLAGGED",
                    compliance_score=75.0
                )
                db.add(b4)
                db.commit()
                db.refresh(b4)
                print(f"[Seed] Created Bidder '{b4.company_name}' with AES-256 encrypted identifiers")

                doc_wf = Document(
                    bidder_id=b4.id,
                    document_type="UDYAM_CERTIFICATE",
                    file_name="workflow_udyam.pdf",
                    file_size_bytes=150000,
                    mime_type="application/pdf",
                    storage_path="/secure/vault/workflow_udyam.pdf",
                    file_hash=sha256("workflow_udyam_content"),
                    status=DocumentStatus.AI_VERIFIED.value,
                    extracted_data={"udyam": udyam4, "enterprise_type": "MICRO"},
                    ocr_confidence=0.91
                )
                db.add(doc_wf)

                audit_wf = AuditLog(
                    user_id=officer.id,
                    user_email=officer.email,
                    user_role="Procurement Officer",
                    action=AuditAction.CREATE.value,
                    entity_type="BIDDER",
                    entity_id=str(b4.id),
                    summary=f"Created Bidder '{b4.company_name}' under Tender '{server_tender.tender_ref}'.",
                    new_values={"company_name": b4.company_name, "pan_masked": b4.pan_masked}
                )
                db.add(audit_wf)
                db.commit()

            # Bidder 5: Quantum Networks Pvt Ltd
            b5 = db.query(Bidder).filter(Bidder.tender_id == server_tender.id, Bidder.company_name == "Quantum Networks Pvt Ltd").first()
            if not b5:
                pan5 = "QUANT9876M"
                gstin5 = "27QUANT9876M1Z5"
                udyam5 = "UDYAM-MH-01-0099887"

                b5 = Bidder(
                    tender_id=server_tender.id,
                    company_name="Quantum Networks Pvt Ltd",
                    pan_encrypted=encrypt_field(pan5),
                    pan_masked=mask_pan(pan5),
                    gstin_encrypted=encrypt_field(gstin5),
                    gstin_masked=mask_gstin(gstin5),
                    udyam_no_encrypted=encrypt_field(udyam5),
                    udyam_no_masked=mask_udyam(udyam5),
                    contact_email="sales@quantumnetworks.in",
                    contact_phone="+91 88000 11223",
                    composite_status="COMPLIANT",
                    compliance_score=92.0
                )
                db.add(b5)
                db.commit()
                db.refresh(b5)
                print(f"[Seed] Created Bidder '{b5.company_name}' with AES-256 encrypted identifiers")

                doc_qn1 = Document(
                    bidder_id=b5.id,
                    document_type="PAN_CARD",
                    file_name="quantum_pan.pdf",
                    file_size_bytes=220000,
                    mime_type="application/pdf",
                    storage_path="/secure/vault/quantum_pan.pdf",
                    file_hash=sha256("quantum_pan_content"),
                    status=DocumentStatus.AI_VERIFIED.value,
                    extracted_data={"pan": pan5},
                    ocr_confidence=0.98
                )
                db.add(doc_qn1)
                
                check_qn1 = ComplianceCheck(
                    bidder_id=b5.id,
                    requirement_key="PAN",
                    portal_name="INCOME_TAX",
                    status=ComplianceCheckStatus.VERIFIED.value,
                    check_details={"portal": "INCOME_TAX", "pan_status": "ACTIVE"},
                    score_contribution=15.0,
                    verified_at=datetime.now(timezone.utc)
                )
                db.add(check_qn1)
                
                audit_qn = AuditLog(
                    user_id=officer.id,
                    user_email=officer.email,
                    user_role="Procurement Officer",
                    action=AuditAction.CREATE.value,
                    entity_type="BIDDER",
                    entity_id=str(b5.id),
                    summary=f"Created Bidder '{b5.company_name}' under Tender '{server_tender.tender_ref}'.",
                    new_values={"company_name": b5.company_name, "pan_masked": b5.pan_masked}
                )
                db.add(audit_qn)
                db.commit()

        print("[Seed] Database seeding completed successfully with all ERD models, encryption, and audit logs!")
    except Exception as e:
        db.rollback()
        print(f"[Seed] Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

