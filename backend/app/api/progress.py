from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Document, User
from app.services.progress_service import get_progress, get_progress_history

router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
)


@router.get("/document/{document_id}")
def document_progress(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    return get_progress(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )


@router.get("/document/{document_id}/history")
def document_progress_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    return get_progress_history(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )
