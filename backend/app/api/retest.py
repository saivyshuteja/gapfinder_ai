from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services.retest_service import (
    compare_attempts,
    get_retest_questions,
    get_retest_topics,
)

router = APIRouter(
    prefix="/retest",
    tags=["Retesting"],
)


@router.get("/topics/{document_id}")
def retest_topics(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_retest_topics(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )


@router.get("/questions/{topic_id}")
def retest_questions(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_retest_questions(db=db, topic_id=topic_id)


@router.get("/compare/{previous_attempt_id}/{new_attempt_id}")
def retest_compare(
    previous_attempt_id: int,
    new_attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return compare_attempts(
            db=db,
            previous_attempt_id=previous_attempt_id,
            new_attempt_id=new_attempt_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
