# AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement
## Smart India Hackathon (SIH) — Problem Statement 100 (PS100)

An end-to-end, automated, AI-driven statutory compliance verification and risk assessment platform designed for **Government e-Marketplace (GeM)** procurement officers.

---

## 🌟 Key Features

1. **Multi-Portal Integration Layer (15+ Government APIs)**:
   - Automated adapters for **GSTN**, **Income Tax / PAN (CBDT)**, **Udyam / MSME**, **MCA21**, **EPFO**, **ESIC**, **CPPP Debarment**, **Startup India**, **NSIC**, **DigiLocker**, **BIS/DPIIT**, **Gem Blacklist**, and more.
   - Standardized normalization, circuit breaker protection, exponential backoff retry with jitter, and offline fallback mock generators.

2. **AI Document Intelligence (OCR & NLP Pipeline)**:
   - Computer vision pre-processing via **OpenCV** (adaptive thresholding, deskewing, noise reduction).
   - Structured entity extraction via **PyTesseract** and regex/NLP parsing for GSTIN, PAN, turnover, and Make in India percentages.
   - Contour analysis for automatic signature and official stamp/seal detection.
   - Document lifecycle state transitions: `UPLOADED` → `OCR_PROCESSING` → `AI_VERIFIED` / `FLAGGED`.

3. **Compliance & Scoring Engine**:
   - Codified statutory rule evaluation (e.g., GST Active, PAN Verified, Non-Debarred).
   - Tender-specific customizable checklist rules with dynamic weights.
   - Multi-source field-by-field cross-verification (Uploaded Documents vs Government Portals vs Bidder DB).
   - Weighted scoring algorithm with discrepancy penalty deductions.
   - Multi-tier risk classification (**LOW**, **MEDIUM**, **HIGH**) and natural language AI recommendations.

4. **Split-Screen Verification Workspace (UI/UX)**:
   - **Interactive PDF Viewer**: Visual document bounding box inspection with auto-zoom on flagged fields.
   - **Side-by-Side Comparison Table**: Bidder Document data vs Live Portal data with real-time pass/mismatch chips.
   - **Pinned Evidence Docket**: Ability for officers to pin discrepancies directly into the formal evaluation record.
   - **AI Safety Gate**: Automated qualification strictly prohibited; requires certified human Procurement Officer authorization with mandatory minimum 15-character substantive remarks under GFR Rule 173.

5. **Security, Audit & Governance**:
   - **Append-Only Tamper-Proof Audit Trail**: SQLAlchemy event hooks prevent update/deletion of audit logs; SHA-256 cryptographic chain hashes ensure legal non-repudiation.
   - **AES-256-GCM Encryption**: PII identifiers (PAN, GSTIN, Udyam) encrypted at rest with unique IVs and PBKDF2 key derivation.
   - **Portal Outage Handling**: Graceful degradation to `PENDING_MANUAL_REVIEW` when government services experience downtime.
   - **Security Headers**: Production middleware enforcing strict CSP, HSTS, X-Frame-Options, and X-Content-Type-Options.

---

## 🏗️ Project Architecture

```
PS100_SIH/
├── backend/
│   ├── app/
│   │   ├── ai/               # OCR pipeline, NLP extractor, signature/stamp verifier
│   │   ├── api/              # FastAPI REST routers (auth, tenders, bidders, compliance, audit, etc.)
│   │   ├── audit/            # Append-only audit model, SHA-256 hashing & docket export
│   │   ├── compliance/       # Rule engine, scoring module, risk classifier, cross verifier
│   │   ├── core/             # JWT configuration, security settings
│   │   ├── integrations/     # 15+ government portal API fetchers & normalizers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── security/         # AES-256-GCM encryption, circuit breaker, retry manager
│   │   ├── services/         # Core business logic services
│   │   ├── utils/            # Cryptography & string normalizer utilities
│   │   └── workflow/         # AI Safety Gate & officer decision controller
│   ├── tests/                # Automated pytest suite (61 tests, 100% pass rate)
│   ├── Dockerfile            # Containerized backend deployment
│   ├── main.py               # FastAPI application entrypoint
│   └── seed.py               # Pre-seeded tenders, bidders, and credentials
├── frontend/
│   ├── src/
│   │   ├── components/       # UI components (VerificationWorkspace, Split-Screen, Dashboard, Tenders)
│   │   ├── context/          # React Auth and State contexts
│   │   └── services/         # Axios API clients
│   ├── Dockerfile            # Containerized frontend deployment
│   ├── nginx.conf            # Production Nginx reverse proxy configuration
│   └── package.json          # Dependencies (React 18, Tailwind CSS, Lucide icons)
├── deployment/
│   └── docker-compose.yml    # Full-stack container orchestration
├── .github/workflows/
│   └── ci.yml                # GitHub Actions automated CI/CD pipeline
└── run_backend.bat / run_frontend.bat
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.12 / 3.14)
- **Node.js**: 18+ (tested on Node 20 LTS)
- **Git**: 2.30+

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

---

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed initial database with demo tenders, bidders, and encrypted PII
python seed.py

# Start FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- **Backend API URL**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Swagger Docs**: `http://127.0.0.1:8000/docs`
- **System Health Check**: `http://127.0.0.1:8000/health`

---

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
```

- **Application URL**: `http://127.0.0.1:5173`

---

## 🐳 Docker Deployment (One-Command Launch)

You can launch the entire stack using Docker Compose:

```bash
docker-compose up --build -d
```

- **Frontend Application**: `http://localhost:80`
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 🔑 Default Credentials & Role-Based Access Control (RBAC)

The system is pre-seeded with accounts ready for evaluation:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Procurement Officer** | `officer@gem.gov.in` | `GeM@2026!Officer` | Full Tender CRUD, Statutory Checklist Configuration, Verification Workspace, Decision Authority |
| **Bidder (Vendor)** | `bidder@techcorp.in` | `Bidder@2026!Pass` | Bid submission and compliance status viewing (Tender modification blocked by RBAC) |

*(A 1-click evaluator login button is also provided on the `/login` screen)*

---

## 🧪 Automated Testing & Verification

The project includes automated test coverage with **100% passing tests**:

```bash
cd backend
pytest tests -v
```

### Test Suites Summary:
- `test_ai_document_pipeline.py`: OCR image preprocessing, contour detection, LayoutLM extraction (7 tests)
- `test_auth.py`: JWT authentication, bcrypt validation, RBAC enforcement (6 tests)
- `test_compliance_engine.py`: Statutory rule catalog, weighted scoring, risk classification, AI recommendations (12 tests)
- `test_core_services.py`: AES-256 encryption, PII masking, bidder cascade deletion, audit log immutability (10 tests)
- `test_final_audit_security_workflow.py`: Append-only audit logs, SHA-256 chain hashes, circuit breaker, portal outage handling, AI safety gate, security headers, concurrent load (12 tests)
- `test_integrations.py`: 15+ external government portal adapters, normalization, fuzzy similarity (8 tests)
- `test_tenders.py`: Tender CRUD lifecycle, Draft editable, Published/Closed editing locks (6 tests)

**Total**: 61 passed out of 61 tests.

---

## 📜 Compliance & Legal References
- **GFR 2017 Rule 173**: Non-discriminatory evaluation and transparent audit trail.
- **GeM Guidelines**: Public Procurement (Preference to Make in India) Order.
- **IT Act 2000**: Digital evidence integrity and tamper-evident audit logging.
