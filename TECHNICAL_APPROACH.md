# Technical Approach: AI-Powered SmartBid Verification Platform

## TECH STACK SUMMARY
* **Frontend (UI)**
  * React + Vite
  * Tailwind CSS
* **Backend**
  * FastAPI (Python 3.10+)
  * Pydantic + SQLAlchemy
  * Asyncio (Parallel processing)
* **Database**
  * PostgreSQL / SQLite (Zero-config fallback)
* **AI / ML**
  * OpenCV (Computer Vision)
  * PyTesseract (OCR)
  * NLP & Contour Analysis
* **Govt Integrations**
  * 15+ Statutory Portals (GSTN, MCA21, EPFO, DigiLocker, etc.)
* **Security & Audit**
  * AES-256-GCM Encryption
  * SHA-256 Cryptographic Hashing

---

## USERS (Stakeholders)
* **Procurement Officer**
  * Reviews automated AI flags, visually verifies documents, and executes final approval (AI Safety Gate).
* **Bidder (Vendor)**
  * Uploads statutory certificates and tracks real-time compliance status.
* **System Admin / Auditor**
  * Monitors tamper-proof audit trails and manages government portal API health.

---

## FRONTEND (User Interface)
* **React (18+)**
  * Modern, responsive component-based UI.
* **Split-Screen Workspace**
  * Interactive PDF Viewer (left) side-by-side with Live Data Comparison Table (right).
* **Tailwind CSS**
  * Rapid, modern styling and design system.
* **Pinned Evidence Docket**
  * Tools for officers to pin visual discrepancies directly to the formal evaluation record.
* **Role-Based Dashboards**
  * Custom views isolated by JWT-based RBAC (Officer vs. Bidder).

---

## BACKEND + AI PIPELINE (Brain of the System)
* **FastAPI (Python 3.10+)**
  * High-performance, asynchronous REST APIs.
* **AI Document Intelligence**
  * Pre-processes images (OpenCV), extracts text (OCR/NLP), and detects official stamps/signatures.
* **Compliance & Scoring Engine**
  * Executes 3-way cross-verification (User vs. PDF vs. Govt API) and calculates weighted risk scores.
* **Pydantic**
  * Strict data validation and schema enforcement.
* **SQLAlchemy ORM**
  * Secure database mapping with append-only event hooks for audit logs.

---

## TOOLS & INTEGRATIONS (External Services)
* **15+ Govt APIs**
  * Direct adapters for GSTN, CBDT (PAN), Udyam, MCA21, Startup India, CPPP Debarment, etc.
* **Async Orchestrator**
  * Dispatches 15 API calls concurrently using `asyncio.gather` for ultra-fast response times.
* **Resilient Middleware**
  * Circuit breakers and exponential backoff ensure the system survives government portal outages gracefully.
* **Security Services**
  * AES-256-GCM module encrypts bidder PII (PAN/GSTIN) instantly before storage.

---

## DATA LAYER (Stores & Processes Data)
* **Raw Uploads (Certificates)**
  * PDFs and scanned images uploaded by bidders for OCR extraction.
* **Data Normalization Pipeline**
  * Cleans, validates, and standardizes vastly different JSON/XML responses from 15 government portals into one uniform schema.
* **Cryptographic Audit Trail**
  * Blockchain-inspired logging where every action is sealed with a SHA-256 chain hash for legal non-repudiation.
* **Relational Database (Main)**
  * Stores Tenders, Bidders, Encrypted PII, and Verification Results securely.
