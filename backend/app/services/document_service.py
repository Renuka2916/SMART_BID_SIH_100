import hashlib
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.bidder import Bidder
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.document_schema import DocumentCreate, DocumentUpdateStatus
from app.services.audit_service import record_audit_log

def compute_sha256(content: bytes) -> str:
    """Computes SHA-256 checksum for binary file content."""
    return hashlib.sha256(content).hexdigest()

def register_document(
    db: Session,
    bidder_id: int,
    doc_in: DocumentCreate,
    current_user: Optional[User] = None
) -> Document:
    """
    Registers a new document uploaded for a Bidder:
    1. Validates bidder exists.
    2. Calculates or assigns SHA-256 hash.
    3. Persists document metadata.
    4. Logs an audit entry.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bidder with ID {bidder_id} not found."
        )

    file_hash = doc_in.file_hash
    if not file_hash:
        # Generate hash based on storage path and filename
        fallback_bytes = f"{bidder_id}:{doc_in.document_type}:{doc_in.file_name}:{doc_in.storage_path}".encode("utf-8")
        file_hash = compute_sha256(fallback_bytes)

    document = Document(
        bidder_id=bidder_id,
        document_type=doc_in.document_type.upper(),
        file_name=doc_in.file_name,
        file_size_bytes=doc_in.file_size_bytes or 0,
        mime_type=doc_in.mime_type,
        storage_path=doc_in.storage_path,
        file_hash=file_hash,
        status=DocumentStatus.UPLOADED.value,
        extracted_data={},
        ocr_confidence=None
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    record_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.DOCUMENT_UPLOAD.value,
        entity_type="DOCUMENT",
        entity_id=str(document.id),
        summary=f"Uploaded {document.document_type} ('{document.file_name}') for Bidder '{bidder.company_name}'.",
        new_values={
            "document_id": document.id,
            "bidder_id": bidder_id,
            "document_type": document.document_type,
            "file_hash": document.file_hash,
            "status": document.status
        }
    )

    return document

def update_document_status(
    db: Session,
    document_id: str,
    update_in: DocumentUpdateStatus,
    current_user: Optional[User] = None
) -> Document:
    """
    Transitions a document through its lifecycle:
    UPLOADED -> OCR_PROCESSING -> AI_VERIFIED or FLAGGED.
    Records audit log with status diff.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )

    old_status = document.status
    old_data = document.extracted_data

    document.status = update_in.status.value
    if update_in.extracted_data is not None:
        document.extracted_data = update_in.extracted_data
    if update_in.ocr_confidence is not None:
        document.ocr_confidence = update_in.ocr_confidence

    db.commit()
    db.refresh(document)

    record_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.STATUS_CHANGE.value,
        entity_type="DOCUMENT",
        entity_id=str(document.id),
        summary=f"Document '{document.file_name}' status changed: {old_status} -> {document.status}.",
        old_values={"status": old_status, "extracted_data": old_data},
        new_values={
            "status": document.status,
            "extracted_data": document.extracted_data,
            "ocr_confidence": document.ocr_confidence
        }
    )

    return document

def get_documents_by_bidder(db: Session, bidder_id: int) -> List[Document]:
    """Retrieves all documents associated with a bidder."""
    return db.query(Document).filter(Document.bidder_id == bidder_id).all()

def get_document_by_id(db: Session, document_id: str) -> Document:
    """Retrieves a single document by UUID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )
    return doc
