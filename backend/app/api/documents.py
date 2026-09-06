from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.schemas.document_schema import (
    DocumentCreate,
    DocumentUpdateStatus,
    DocumentResponse,
    DocumentListResponse
)
from app.api.auth import get_current_user
from app.services.document_service import (
    register_document,
    update_document_status,
    get_documents_by_bidder,
    get_document_by_id
)

router = APIRouter(tags=["Document Management"])

@router.post("/bidders/{bidder_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document_metadata(
    bidder_id: int,
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registers a new document uploaded for a bidder:
    - Calculates SHA-256 integrity hash
    - Sets initial status to UPLOADED
    - Records immutable audit log
    """
    return register_document(db, bidder_id, doc_in, current_user)

@router.get("/bidders/{bidder_id}/documents", response_model=DocumentListResponse)
def list_bidder_documents(
    bidder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all documents registered for a specific bidder."""
    docs = get_documents_by_bidder(db, bidder_id)
    return DocumentListResponse(total=len(docs), items=docs)

@router.get("/documents/{id}", response_model=DocumentResponse)
def get_document_details(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves single document metadata and extracted OCR data."""
    return get_document_by_id(db, id)

@router.put("/documents/{id}/status", response_model=DocumentResponse)
def change_document_status(
    id: str,
    status_in: DocumentUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates document status (UPLOADED, OCR_PROCESSING, AI_VERIFIED, FLAGGED).
    Appends audit log recording old vs new status transition.
    """
    return update_document_status(db, id, status_in, current_user)
