"""
High-Fidelity Simulated Government Responses for 15 Statutory Portals
Conforms to official Indian Government API response specifications (GSTN, MSME, CBDT, MCA21, etc.).
"""

from typing import Dict, Any, Optional

def get_simulated_udyam_response(udyam_no: Optional[str], company_name: str) -> Dict[str, Any]:
    return {
        "status": "SUCCESS",
        "portal": "Ministry of MSME - Udyam Registration Portal",
        "data": {
            "udyam_registration_number": udyam_no or "UDYAM-DL-01-0029145",
            "enterprise_name": company_name.upper(),
            "enterprise_type": "Micro, Small and Medium Enterprises",
            "classification": "Small Enterprise",
            "major_activity": "Manufacturing & ICT Services",
            "national_industry_classification_nic": [
                {"nic_code": "62011", "description": "Writing of software, computer programming"},
                {"nic_code": "26201", "description": "Manufacture of desktop and computing hardware"}
            ],
            "units": [
                {"unit_name": "Unit-1 Primary Production", "state": "Delhi", "district": "New Delhi"}
            ],
            "date_of_commencement": "2018-04-15",
            "date_of_registration": "2020-07-20",
            "status": "ACTIVE",
            "valid_up_to": "PERPETUAL_SUBJECT_TO_ANNUAL_ITR_GSTN"
        }
    }

def get_simulated_gstn_response(gstin: Optional[str], company_name: str) -> Dict[str, Any]:
    return {
        "status_code": 200,
        "portal": "GSTN - Goods and Services Tax Network",
        "data": {
            "gstin": gstin or "07ABCDE1234F1Z5",
            "trade_name": company_name,
            "legal_name": company_name,
            "taxpayer_type": "Regular",
            "status": "Active",
            "registration_date": "2017-07-01",
            "constitution_of_business": "Private Limited Company",
            "principal_place_of_business": {
                "address": "Block B-4, Okhla Industrial Area Phase-II",
                "state": "Delhi",
                "pincode": "110020"
            },
            "filing_status": {
                "gstr_1_recency": "FILING_COMPLIANT_CURRENT_MONTH",
                "gstr_3b_recency": "FILING_COMPLIANT_CURRENT_MONTH",
                "filings_history": [
                    {"financial_year": "2025-26", "tax_period": "January", "status": "Filed", "dof": "2026-02-18"},
                    {"financial_year": "2025-26", "tax_period": "December", "status": "Filed", "dof": "2026-01-19"},
                    {"financial_year": "2025-26", "tax_period": "November", "status": "Filed", "dof": "2025-12-19"}
                ]
            },
            "e_way_bill_blocked": False,
            "compliance_rating": "5/5"
        }
    }

def get_simulated_pan_cbdt_response(pan: Optional[str], company_name: str) -> Dict[str, Any]:
    return {
        "status": "VALID",
        "portal": "CBDT - Income Tax Department",
        "data": {
            "pan": pan or "ABCDE1234F",
            "pan_status": "EXISTING_AND_VALID",
            "registered_name": company_name.upper(),
            "category": "Company",
            "aadhaar_seeding_status": "NOT_APPLICABLE_CORPORATE",
            "itr_compliance_status": {
                "is_specified_person_u_s_206ab_206cca": False,
                "itr_filing_history": [
                    {"ay": "2025-26", "itr_form": "ITR-6", "acknowledgement_no": "981726354182910", "filing_date": "2025-10-28"},
                    {"ay": "2024-25", "itr_form": "ITR-6", "acknowledgement_no": "882736451928374", "filing_date": "2024-10-25"},
                    {"ay": "2023-24", "itr_form": "ITR-6", "acknowledgement_no": "773645192837465", "filing_date": "2023-10-30"}
                ]
            }
        }
    }

def get_simulated_mca21_response(cin: Optional[str], company_name: str) -> Dict[str, Any]:
    return {
        "status": "ACTIVE",
        "portal": "Ministry of Corporate Affairs (MCA21)",
        "data": {
            "cin": cin or "U72900DL2018PTC334567",
            "company_name": company_name.upper(),
            "roc_code": "RoC-Delhi",
            "company_category": "Company limited by shares",
            "company_sub_category": "Non-govt company",
            "class_of_company": "Private",
            "authorized_capital_inr": 50000000,
            "paid_up_capital_inr": 25000000,
            "date_of_incorporation": "2018-05-12",
            "active_compliance": "ACTIVE_COMPLIANT_INC_22A",
            "directors": [
                {"din": "08123456", "name": "Rajesh Kumar Sharma", "designation": "Managing Director", "disqualified": False},
                {"din": "08654321", "name": "Ananya Gupta", "designation": "Whole-time Director", "disqualified": False}
            ],
            "charges": {"active_open_charges_count": 0, "amount_inr": 0}
        }
    }

def get_simulated_epfo_response(epfo_code: Optional[str], company_name: str) -> Dict[str, Any]:
    is_netsecure = "NETSECURE" in company_name.upper()
    return {
        "status": "COMPLIANT" if not is_netsecure else "FLAGGED",
        "portal": "EPFO - Shram Suvidha Unified Portal",
        "data": {
            "establishment_code": epfo_code or ("DLCPM0045892000" if not is_netsecure else "MHBAN0089123000"),
            "establishment_name": company_name,
            "regional_office": "Delhi Central" if not is_netsecure else "Bandra Mumbai",
            "active_members_count": 142 if not is_netsecure else 34,
            "ecr_filing_status": "REGULAR" if not is_netsecure else "DELAYED",
            "last_wage_month_filed": "2026-01" if not is_netsecure else "2025-11",
            "challan_reference": "TRRN1029384756182" if not is_netsecure else "TRRN9823741029384",
            "payment_verified": not is_netsecure,
            "defaulter_list": False
        }
    }

def get_simulated_esic_response(esic_code: Optional[str], company_name: str) -> Dict[str, Any]:
    return {
        "status": "COMPLIANT",
        "portal": "ESIC - Employee State Insurance Portal",
        "data": {
            "employer_code": esic_code or "11000987650001001",
            "employer_name": company_name,
            "coverage_status": "COVERED",
            "active_insured_persons": 98,
            "monthly_contribution_status": "UP_TO_DATE",
            "last_contribution_month": "2026-01",
            "inspection_observations": "NIL_CLEARED"
        }
    }

def get_simulated_startup_india_response(dipp_no: Optional[str], company_name: str) -> Dict[str, Any]:
    return {
        "status": "RECOGNIZED",
        "portal": "Startup India - DPIIT Recognition Registry",
        "data": {
            "dipp_recognition_number": dipp_no or "DIPP54982",
            "startup_name": company_name,
            "industry": "IT Services & Technology Hardware",
            "sector": "Enterprise Solutions",
            "date_of_recognition": "2021-03-14",
            "gem_exemptions_eligible": {
                "prior_turnover_waiver": True,
                "prior_experience_waiver": True,
                "tender_fee_waiver": True
            },
            "validity_status": "ACTIVE"
        }
    }

def get_simulated_nsic_response(nsic_no: Optional[str], company_name: str) -> Dict[str, Any]:
    return {
        "status": "ACTIVE_CERTIFIED",
        "portal": "NSIC - Single Point Registration Scheme (SPRS)",
        "data": {
            "sprs_certificate_number": nsic_no or "NSIC/SPRS/2022/98412",
            "unit_name": company_name,
            "category": "Small Enterprise",
            "monetary_limit_inr": 80000000,
            "valid_from": "2023-01-01",
            "valid_up_to": "2027-12-31",
            "emd_exemption_qualified": True
        }
    }

def get_simulated_digilocker_response(company_name: str) -> Dict[str, Any]:
    return {
        "status": "AUTHENTICATED",
        "portal": "DigiLocker National Repository (MeitY)",
        "data": {
            "issuer_id": "in.gov.gem",
            "entity_name": company_name,
            "repository_uri": "in.gov.digilocker/cert/gem_statutory_docket_2026",
            "tamper_proof_checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "digital_signature": {
                "format": "PKCS#7 / XML-DSig",
                "signer_cn": "National Informatics Centre (NIC) e-Sign Gateway",
                "cert_validity": "VALID",
                "ocsp_revocation_status": "GOOD"
            },
            "verified_credentials": [
                "Certificate of Incorporation",
                "PAN Card Credential",
                "GST Registration Certificate (REG-06)",
                "Udyam Verification Asset"
            ]
        }
    }

def get_simulated_blacklisting_response(company_name: str, pan: Optional[str]) -> Dict[str, Any]:
    # NetSecure triggers a warning in demo
    is_flagged = "NETSECURE" in company_name.upper()
    return {
        "status": "CLEARED" if not is_flagged else "FLAGGED",
        "portal": "CPPP Debarment, GeM Watchlist & CVC Vigilance Portal",
        "data": {
            "query_company": company_name,
            "query_pan": pan or "ABCDE1234F",
            "is_blacklisted": is_flagged,
            "is_debarred": is_flagged,
            "database_matches": [] if not is_flagged else [
                {
                    "registry": "State Public Procurement Watchlist",
                    "reason": "Non-execution of SLA within stipulated notice period in 2024",
                    "authority": "State PWD Directorate",
                    "period_from": "2024-06-01",
                    "period_to": "2025-05-31",
                    "current_status": "EXPIRED_FLAG_AUDIT_REQUIRED"
                }
            ],
            "vigilance_clearance_status": "CLEAR" if not is_flagged else "REVIEW_REQUIRED",
            "last_checked_timestamp": "2026-09-06T18:50:00Z"
        }
    }

def get_simulated_dpiit_mii_response(company_name: str) -> Dict[str, Any]:
    is_zenith = "ZENITH" in company_name.upper()
    if is_zenith:
        return {
            "status": "FLAGGED",
            "portal": "DPIIT Make in India (Public Procurement Preference) Portal",
            "data": {
                "supplier_name": company_name,
                "local_content_percentage": 35.0,
                "supplier_classification": "Class-II Local Supplier (>= 20% & < 50%)",
                "manufacturing_locations": [
                    {"facility": "MIDC Electronic Zone", "city": "Pune", "state": "Maharashtra"}
                ],
                "ca_declaration_attached": False,
                "statutory_declaration_ref": "MII-SELF-2026-1029",
                "preference_benefit_eligible": False
            }
        }
    return {
        "status": "VERIFIED",
        "portal": "DPIIT Make in India (Public Procurement Preference) Portal",
        "data": {
            "supplier_name": company_name,
            "local_content_percentage": 68.5,
            "supplier_classification": "Class-I Local Supplier (>= 50%)",
            "manufacturing_locations": [
                {"facility": "Sector 62 Electronics Zone", "city": "Noida", "state": "Uttar Pradesh"}
            ],
            "ca_declaration_attached": True,
            "statutory_declaration_ref": "MII-DEC-2026-8819",
            "preference_benefit_eligible": True
        }
    }

def get_simulated_bis_response(company_name: str) -> Dict[str, Any]:
    return {
        "status": "VERIFIED",
        "portal": "Bureau of Indian Standards (BIS)",
        "data": {
            "entity_name": company_name,
            "bis_standard": "IS 13252 (Part 1): 2010 / IEC 60950-1: 2005",
            "product_category": "Information Technology Equipment - General Requirements",
            "registration_number": "R-41098234",
            "status": "OPERATIVE",
            "valid_till": "2027-08-31",
            "factory_address": "Plot 18, Kasna Industrial Area, Greater Noida, UP"
        }
    }

def get_simulated_oem_auth_response(company_name: str) -> Dict[str, Any]:
    is_zenith = "ZENITH" in company_name.upper()
    if is_zenith:
        return {
            "status": "ADVISORY",
            "portal": "OEM Manufacturer Authorization Registry",
            "data": {
                "partner_company": company_name,
                "oem_principal": "Bharath Tech Computronix India Pvt Ltd",
                "maf_code": "MAF-DIST-2026-9041",
                "authorization_tier": "Tier-2 Regional Reseller",
                "scope_of_authorization": "Distributor-backed supply; SLA contingent on distributor channel",
                "validity": "VALID_FOR_TENDER_DURATION",
                "oem_signatory_email": "reseller-channel@bharathtech.co.in",
                "verification_checksum": "OEM-SHA256-DISTRIBUTOR-FLAGGED"
            }
        }
    return {
        "status": "AUTHENTIC",
        "portal": "OEM Manufacturer Authorization Registry",
        "data": {
            "partner_company": company_name,
            "oem_principal": "Bharath Tech Computronix India Pvt Ltd",
            "maf_code": "MAF-IN-2026-GEM-99018",
            "authorization_tier": "Tier-1 Master Enterprise Partner",
            "scope_of_authorization": "Supply, Onsite Deployment & Comprehensive 3-Year 24x7 SLA",
            "validity": "VALID_FOR_TENDER_DURATION",
            "oem_signatory_email": "procurement-support@bharathtech.co.in",
            "verification_checksum": "OEM-SHA256-VALIDATED"
        }
    }

def get_simulated_gem_incident_response(company_name: str) -> Dict[str, Any]:
    is_netsecure = "NETSECURE" in company_name.upper()
    return {
        "status": "CLEARED" if not is_netsecure else "ADVISORY",
        "portal": "GeM Incident Management & Seller Rating System",
        "data": {
            "seller_name": company_name,
            "overall_seller_rating": 4.8 if not is_netsecure else 3.6,
            "total_completed_orders": 240 if not is_netsecure else 42,
            "delivery_timeliness_pct": 98.2 if not is_netsecure else 88.5,
            "open_incidents_count": 0 if not is_netsecure else 1,
            "show_cause_notices_count": 0,
            "incident_details": [] if not is_netsecure else [
                {"incident_id": "INC-2025-098", "severity": "LOW", "status": "RESOLVED_WITH_CAUTION", "reason": "Minor 4-day delivery delay on regional order"}
            ]
        }
    }

def get_simulated_turnover_ca_response(company_name: str) -> Dict[str, Any]:
    is_zenith = "ZENITH" in company_name.upper()
    if is_zenith:
        return {
            "status": "PROVISIONAL_VERIFIED",
            "portal": "ICAI UDIN Registry & Corporate Financials Verification",
            "data": {
                "client_name": company_name,
                "udin_number": "26084920PROVISIONAL11",
                "chartered_accountant_firm": "P.V. Joshi & Co (FRN: 004812W)",
                "udin_generation_date": "2026-01-20",
                "financial_turnover": {
                    "fy_2024_25_inr_crores": 8.4,
                    "fy_2023_24_inr_crores": 7.9,
                    "fy_2022_23_inr_crores": 6.8,
                    "avg_3yr_turnover_inr_crores": 7.7
                },
                "net_worth_inr_crores": 3.2,
                "solvency_status": "SOLVENT_PROVISIONAL_UDIN",
                "working_capital_inr_crores": 1.9
            }
        }
    return {
        "status": "AUDITED_VALID",
        "portal": "ICAI UDIN Registry & Corporate Financials Verification",
        "data": {
            "client_name": company_name,
            "udin_number": "26084920AAAAAB9812",
            "chartered_accountant_firm": "K.S. Mehta & Associates (FRN: 001928N)",
            "udin_generation_date": "2025-09-15",
            "financial_turnover": {
                "fy_2024_25_inr_crores": 14.8,
                "fy_2023_24_inr_crores": 12.2,
                "fy_2022_23_inr_crores": 10.4,
                "avg_3yr_turnover_inr_crores": 12.47
            },
            "net_worth_inr_crores": 8.1,
            "solvency_status": "SOLVENT",
            "working_capital_inr_crores": 4.6
        }
    }
