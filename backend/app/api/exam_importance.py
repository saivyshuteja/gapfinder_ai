from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Document, User
from app.schemas.topic import TopicResponse
from app.services.exam_importance_service import (
    calculate_exam_importance,
    get_exam_importance,
)

router = APIRouter(
    prefix="/exam-importance",
    tags=["Exam Importance"]
)


@router.post(
    "/calculate/{document_id}",
    response_model=list[TopicResponse]
)
def calculate_importance(
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

    try:
        return calculate_exam_importance(
            db=db,
            document_id=document_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


@router.get(
    "/document/{document_id}",
    response_model=list[TopicResponse]
)
def get_importance(
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

    return get_exam_importance(
        db=db,
        document_id=document_id
    )