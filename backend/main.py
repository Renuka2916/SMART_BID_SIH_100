from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import app.models  # Ensure all models are imported for Base.metadata
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.tenders import router as tenders_router
from app.api.users import router as users_router
from app.api.bidders import router as bidders_router
from app.api.documents import router as documents_router
from app.api.audit_logs import router as audit_logs_router
from app.api.integrations import router as integrations_router
from app.api.ai_documents import router as ai_documents_router
from app.api.compliance import router as compliance_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on application startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="""
## Smart India Hackathon (PS100)
### AI-Powered SmartBid Verification Platform for SmartBid Procurement

This backend provides:
* **JWT Authentication & RBAC**: Enforcing the **'Procurement Officer'** role.
* **Tender Management CRUD**: Tender metadata & statutory checklist configuration.
* **Bidder Core & AES-256 Encryption**: Encrypted storage for sensitive PII (PAN, GSTIN, Udyam No).
* **Document Management & Hash Integrity**: SHA-256 integrity checks, OCR lifecycle transitions.
* **Immutable Audit Trail**: Append-only tamper-proof operational logging.
* **API Documentation**: Interactive OpenAPI Swagger specification.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces strict Government-grade HTTP security headers for SmartBid procurement."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://127.0.0.1:* http://localhost:* ws:;"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(tenders_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(bidders_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(audit_logs_router, prefix=settings.API_V1_STR)
app.include_router(integrations_router, prefix=settings.API_V1_STR)
app.include_router(ai_documents_router, prefix=settings.API_V1_STR)
app.include_router(compliance_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["System"])
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "SmartBid Verification Engine API"}
