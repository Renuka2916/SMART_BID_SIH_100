from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.models.document import Document
from app.api.auth import get_current_user
from app.schemas.ai_extraction_result import AIExtractionResult
from app.services.ai_service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Document Intelligence"])

@router.post("/extract-file", response_model=AIExtractionResult)
async def extract_data_from_uploaded_file(
    file: UploadFile = File(...),
    doc_type: str = Form("GENERAL_STATUTORY"),
    expected_bidder_name: Optional[str] = Form(None),
    expected_pan: Optional[str] = Form(None),
    expected_gstin: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Directly uploads a PDF or scanned image certificate and executes:
    1. OpenCV image preprocessing (bilateral denoise, binarization, deskew).
    2. Dual-engine OCR extraction (pypdf text stream / PyTesseract OCR).
    3. NLP Named Entity Recognition (GSTIN, PAN, Udyam, % Local Content, UDIN, Dates).
    4. Computer Vision Signature & Official Stamp/Seal Verification.
    5. Cross-check consistency analysis.
    """
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    result = ai_service.process_file_bytes(
        file_bytes=content,
        filename=file.filename or "uploaded_document.pdf",
        doc_type=doc_type,
        expected_bidder_name=expected_bidder_name,
        expected_pan=expected_pan,
        expected_gstin=expected_gstin
    )
    return result

@router.post("/documents/{document_id}/process-ai")
def trigger_ai_processing_for_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers AI Document Intelligence on a stored bidder document.
    Transitions lifecycle: UPLOADED -> OCR_PROCESSING -> AI_VERIFIED / FLAGGED.
    """
    return ai_service.process_stored_document(
        db=db,
        document_id=document_id,
        current_user=current_user
    )

@router.get("/documents/{document_id}/ai-results")
def get_document_ai_extraction(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the structured AI extraction result and cross-validation status for a document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )

    return {
        "document_id": doc.id,
        "bidder_id": doc.bidder_id,
        "document_type": doc.document_type,
        "file_name": doc.file_name,
        "status": doc.status,
        "ocr_confidence": doc.ocr_confidence,
        "extracted_data": doc.extracted_data
    }
