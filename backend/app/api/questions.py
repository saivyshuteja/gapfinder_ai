import json

from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Document, Question, Topic, User

from app.schemas.question import (
    QuestionResponse
)

from app.services.question_service import (
    generate_diagnostic_question,
    generate_diagnostic_questions,
)


router = APIRouter(
    prefix="/questions",
    tags=["Diagnostic Questions"]
)
logger = logging.getLogger(__name__)


def ensure_topic_owner(db: Session, topic_id: int, user_id: int) -> None:
    topic = (
        db.query(Topic)
        .join(Document, Document.id == Topic.document_id)
        .filter(Topic.id == topic_id, Document.user_id == user_id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")


@router.post(
    "/generate/{topic_id}",
    response_model=QuestionResponse
)
def generate_question(
    topic_id: int,
    difficulty: str = "medium",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        ensure_topic_owner(db, topic_id, current_user.id)

        question = (
            generate_diagnostic_question(
                db=db,
                topic_id=topic_id,
                difficulty=difficulty
            )
        )

        return question

    except HTTPException:
        raise
    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Diagnostic question generation failed for topic %s", topic_id)
        raise HTTPException(
            status_code=502,
            detail="Question generation is temporarily unavailable. Please try again.",
        ) from exc


@router.post(
    "/generate-batch/{topic_id}",
    response_model=list[QuestionResponse],
)
def generate_question_batch(
    topic_id: int,
    difficulty: str = "medium",
    count: int = Query(default=5, ge=5, le=6),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        ensure_topic_owner(db, topic_id, current_user.id)
        return generate_diagnostic_questions(
            db=db,
            topic_id=topic_id,
            difficulty=difficulty,
            count=count,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Diagnostic question batch generation failed for topic %s", topic_id)
        raise HTTPException(
            status_code=502,
            detail="Question generation is temporarily unavailable. Please try again.",
        ) from exc


@router.get(
    "/topic/{topic_id}",
    response_model=list[QuestionResponse]
)
def get_topic_questions(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_topic_owner(db, topic_id, current_user.id)

    questions = (
        db.query(Question)
        .filter(
            Question.topic_id
            == topic_id
        )
        .order_by(
            Question.id
        )
        .all()
    )

    return questions