import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Document, User
from app.services.rag_service import answer_question

router = APIRouter(
    prefix="/explain",
    tags=["Explain"],
)
logger = logging.getLogger(__name__)


@router.get("/")
def explain_topic(
    question: str,
    document_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if document_id is not None:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        ).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")

    try:
        return answer_question(
            db=db,
            question=question,
            user_id=current_user.id,
            document_id=document_id,
        )
    except Exception as exc:
        logger.exception("Explain request failed for user %s and document %s", current_user.id, document_id)
        raise HTTPException(
            status_code=502,
            detail="I could not search or explain this material right now. Please try again.",
        ) from exc
