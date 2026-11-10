import os

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Document, User
from app.schemas.document import DocumentResponse
from app.schemas.document import DocumentTypeUpdate
from app.services.document_service import (
    process_document,
    save_uploaded_file,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.patch("/{document_id}/type", response_model=DocumentResponse)
def update_document_type(
    document_id: int,
    payload: DocumentTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    document.document_type = payload.document_type
    db.commit()
    db.refresh(document)
    return document


@router.post(
    "/upload",
    response_model=DocumentResponse
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("material"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing"
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_path = await save_uploaded_file(file)
    try:
        normalized_document_type = document_type.strip().lower() or "material"
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            file_type="pdf",
            document_type=normalized_document_type
        )

        db.add(document)
        db.flush()
        if normalized_document_type != "exam":
            process_document(db, document)
        db.commit()
        db.refresh(document)
    except ValueError as exc:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return documents