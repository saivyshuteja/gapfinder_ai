from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Document, Topic, User

from app.schemas.topic import (
    TopicResponse
)

from app.services.topic_service import (
    generate_topics_for_document,
    normalize_topic,
)
from app.services.document_service import process_document


router = APIRouter(
    prefix="/topics",
    tags=["Topics"]
)


@router.post(
    "/generate/{document_id}",
    response_model=list[TopicResponse]
)
def generate_topics(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        process_document(db, document)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    topics = generate_topics_for_document(
        db=db,
        document_id=document_id
    )

    if not topics:
        raise HTTPException(
            status_code=404,
            detail=(
                "No valid topics found "
                "for this document."
            )
        )

    return topics


@router.get(
    "/document/{document_id}",
    response_model=list[TopicResponse]
)
def get_document_topics(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    topics = (
        db.query(Topic)
        .filter(
            Topic.document_id
            == document_id
        )
        .order_by(
            Topic.unit,
            Topic.id
        )
        .all()
    )

    return [topic for topic in topics if normalize_topic(topic.name)]