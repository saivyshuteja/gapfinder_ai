from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.attempt import (
    AnswerSubmit,
    AnswerResponse,
    AttemptResponse,
    AttemptStartResponse,
)
from app.services.attempt_service import (
    calculate_attempt_score,
    complete_attempt,
    get_attempt_answers,
    start_attempt,
    submit_answer,
)

router = APIRouter(
    prefix="/attempts",
    tags=["Attempts"]
)


@router.post(
    "/start/{topic_id}",
    response_model=AttemptStartResponse
)
def start_diagnostic_attempt(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        attempt = start_attempt(
            db=db,
            user_id=current_user.id,
            topic_id=topic_id
        )

        return attempt

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


@router.post(
    "/{attempt_id}/answer",
    response_model=AnswerResponse
)
def submit_diagnostic_answer(
    attempt_id: int,
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        answer = submit_answer(
            db=db,
            attempt_id=attempt_id,
            question_id=payload.question_id,
            student_answer=payload.student_answer,
            user_id=current_user.id,
        )

        return answer

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.post(
    "/{attempt_id}/complete",
    response_model=AttemptResponse
)
def finish_diagnostic_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        attempt = complete_attempt(
            db=db,
            attempt_id=attempt_id,
            user_id=current_user.id,
        )

        return attempt

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


@router.get(
    "/{attempt_id}/answers",
    response_model=list[AnswerResponse]
)
def get_answers(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        return get_attempt_answers(
            db=db,
            attempt_id=attempt_id,
            user_id=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


@router.get(
    "/{attempt_id}/score"
)
def get_attempt_score(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        return calculate_attempt_score(
            db=db,
            attempt_id=attempt_id,
            user_id=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )