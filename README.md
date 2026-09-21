# AI-Powered SmartBid Verification

> **Automating Compliance. Ensuring Transparency. Accelerating Procurement.**  
> *AI-Driven Statutory Compliance Verification and Risk Assessment Platform for GeM*

---

### 🇮🇳 Smart India Hackathon (SIH 2026) Submission Details

| Parameter | Specification |
| :--- | :--- |
| **Problem Statement ID** | `26100` |
| **Problem Statement Title** | **AI-Powered SmartBid Verification for GeM Procurement** |
| **Theme** | **Smart Automation & E-Governance** |
| **PS Category** | **Software** |
| **Team ID** | `120765` |
| **Team Name** | **ARTARS** |

---

## 🏛️ Project Overview

**The SmartBid Verification** is an end-to-end, automated statutory compliance verification and risk assessment platform designed to revolutionize public procurement on the Government e-Marketplace (GeM).

Anchored in **AI Document Intelligence** and direct **Government API integrations**, the platform guarantees:
1. **Multi-Portal Integration Layer**: Automated adapters for 15+ Government APIs (GSTN, Income Tax/PAN (CBDT), Udyam/MSME, MCA21, EPFO, ESIC, CPPP Debarment, Startup India, NSIC, DigiLocker, BIS/DPIIT, GeM Blacklist, UIDAI (Aadhaar), FSSAI, and RBI Defaulters List) with circuit breaker protection and exponential backoff retry.
2. **AI Document Intelligence**: Computer vision (OpenCV) and OCR (PyTesseract) pipeline for structured entity extraction, signature, and official stamp/seal detection.
3. **Compliance & Scoring Engine**: Codified statutory rule evaluation (e.g., GST Active, PAN Verified) executing 3-way cross-verification and multi-tier risk classification (LOW, MEDIUM, HIGH).
4. **Split-Screen Verification Workspace**: Interactive UI featuring a PDF viewer side-by-side with live portal data and real-time pass/mismatch comparison chips.
5. **AI Safety Gate (GFR Rule 173)**: Automated qualification is strictly prohibited; requiring a certified human Procurement Officer to provide mandatory substantive remarks before approving or rejecting flagged bids.
6. **Cryptographic Audit Trail**: Append-only tamper-proof logs secured with SHA-256 chain hashes for legal non-repudiation, alongside AES-256-GCM encryption for bidder PII.

---

## 👥 Master Role Architecture

| Role (Internal Enum) | Display Label | Purpose & Scope | Primary Workspace |
| :--- | :--- | :--- | :--- |
| `PROCUREMENT_OFFICER` | **Procurement Officer** | Reviews automated AI flags, visually verifies documents, configured statutory checklists, and executes final approval (AI Safety Gate) | `/officer-dashboard` |
| `BIDDER` | **Bidder (Vendor)** | Uploads statutory certificates (PDF/Images) and tracks real-time bid compliance status | `/bidder-dashboard` |
| `SYSTEM_ADMIN` | **System Admin / Auditor** | Monitors tamper-proof audit trails, manages government portal API health, and oversees system performance | `/admin` |

---

## ⚖️ Comparative Analysis: Automated Platform vs Existing Solutions

| Dimension / Feature | Central Public Procurement Portal & GeM<br>*(Traditional Process)* | Commercial ERPs & Bidding Tools<br>*(SAP Ariba, Oracle, QuickBid, BidXtra)* | 🏛️ **PS100 Integration Platform**<br>*(AI-Driven Public Procurement)* |
| :--- | :--- | :--- | :--- |
| **Verification Speed** | **Manual / Disconnected**<br>(Officers must manually verify uploads against other Govt portals) | **Fast but Siloed**<br>(Quick process, but commercial tools lack native Indian Govt API synchronization) | **Seconds**<br>(Async concurrent fetching from 15+ Govt APIs) |
| **Error & Fraud Rate** | **High**<br>(Relies heavily on visual checks of easily forged uploaded PDFs) | **Medium**<br>(Strong financial compliance, but unable to live-verify Indian statutory certificates natively) | **Near Zero**<br>(3-way cross-verification: User vs PDF vs Live API) |
| **Evaluation Interface** | **Legacy UI**<br>(Basic file upload/download requiring juggling of multiple tabs) | **Complex Dashboards**<br>(Enterprise grids or estimation UIs, lacking AI document bounding boxes) | **Split-Screen Workspace**<br>(Interactive PDF Viewer side-by-side with live comparison chips) |
| **Risk Assessment** | **Subjective**<br>(Dependent entirely on the evaluating officer's individual scrutiny) | **Financial / Cost Focused**<br>(ERPs focus on credit; Bidding tools on cost. Neither provides statutory AI risk scoring) | **Dynamic Risk Engine**<br>(Automated LOW/MEDIUM/HIGH classification with AI recommendations) |
| **Accountability & Audit** | **Basic Application Logs**<br>(Standard server logs that can be altered or lost) | **Standard Database Logs**<br>(Proprietary logs; lacks cryptographic assurance) | **Tamper-Proof Audit Trail**<br>(Append-only SHA-256 chain hashes for legal non-repudiation) |

---

## 💡 Key Differentiators: What Makes SmartBid Revolutionary?

1. **Multi-Portal Integration Layer (15+ Government APIs)**:
   - Automated adapters for **GSTN**, **Income Tax / PAN (CBDT)**, **Udyam / MSME**, **MCA21**, **EPFO**, **ESIC**, **CPPP Debarment**, **Startup India**, **NSIC**, **DigiLocker**, **BIS/DPIIT**, **Gem Blacklist**, and more.
   - Standardized normalization, circuit breaker protection, exponential backoff retry with jitter, and offline fallback mock generators.

2. **AI Document Intelligence (OCR & NLP Pipeline)**:
   - Computer vision pre-processing via **OpenCV** (adaptive thresholding, deskewing, noise reduction).
   - Structured entity extraction via **PyTesseract** and regex/NLP parsing for GSTIN, PAN, turnover, and Make in India percentages.
   - Contour analysis for automatic signature and official stamp/seal detection.

3. **Compliance & Scoring Engine**:
   - Codified statutory rule evaluation (e.g., GST Active, PAN Verified, Non-Debarred).
   - Multi-source field-by-field cross-verification (Uploaded Documents vs Government Portals vs Bidder DB).
   - Multi-tier risk classification (**LOW**, **MEDIUM**, **HIGH**) and natural language AI recommendations.

4. **Security, Audit & Governance**:
   - **Append-Only Tamper-Proof Audit Trail**: SHA-256 cryptographic chain hashes ensure legal non-repudiation.
   - **AES-256-GCM Encryption**: PII identifiers (PAN, GSTIN, Udyam) encrypted at rest.

---

## 🏗️ Repository Structure

```text
PS100_SIH/
├── backend/
│   ├── app/
│   │   ├── ai/                # Computer vision & OCR pipeline, signature/stamp extraction
│   │   ├── api/               # FastAPI REST routers (tenders, bidders, compliance, audit)
│   │   ├── compliance/        # Rule engine, multi-portal cross verification, scoring module
│   │   ├── database.py        # SQLAlchemy 2.0 engine & SQLite connection logic
│   │   ├── models/            # SQLAlchemy ORM models (AuditLog, Bidder, Tender, Document)
│   │   ├── security/          # AES-256-GCM encryption, circuit breakers, retry managers
│   │   ├── services/          # Core logic (AI, audit, bidder, and document services)
│   │   ├── utils/             # API clients, response normalizers, cryptographic helpers
│   │   └── workflow/          # AI Safety Gate & GFR 173 decision controllers
│   ├── tests/                 # Automated pytest suites (Core services, integrations, auth)
│   ├── seed.py                # Development seeder (Mock Tenders, Bidders, encrypted PII)
│   └── main.py                # FastAPI initialization & application entrypoint
├── frontend/
│   ├── public/                # Static assets, branding, and icons
│   ├── src/
│   │   ├── components/        # Reusable UI (VerificationWorkspace, Navbar, Sidebar)
│   │   ├── context/           # React contexts (AuthContext for role-based access)
│   │   ├── pages/             # App views (ActiveBids, Dashboard, Tenders, Verification)
│   │   ├── services/          # Axios API wrapper (api.js) for backend communication
│   │   ├── App.jsx            # Main React component tree and router setup
│   │   ├── index.css          # Global Tailwind CSS configurations
│   │   └── main.jsx           # React DOM rendering entrypoint
│   ├── package.json           # Frontend dependencies (React, Tailwind, Axios)
│   └── tailwind.config.js     # Tailwind utility class configurations
├── docker-compose.yml         # Full-stack container orchestration for isolated deployment
└── README.md                  # Project overview, architecture, and instructions
```

---

## 🚀 Instructions to Run Locally

### Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+

### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed initial database
python seed.py

# Start FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API URL**: `http://127.0.0.1:8000`

### Step 2: Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
- **Application URL**: `http://localhost:5173`
