from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.subjective import SubjectiveAnswerSubmit, SubjectiveEvaluationResponse
from app.services.subjective_service import evaluate_subjective_answer

router = APIRouter(
    prefix="/subjective",
    tags=["Subjective Evaluation"],
)


@router.post(
    "/{attempt_id}/evaluate",
    response_model=SubjectiveEvaluationResponse,
)
def evaluate_answer(
    attempt_id: int,
    payload: SubjectiveAnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = evaluate_subjective_answer(
            db=db,
            attempt_id=attempt_id,
            question_id=payload.question_id,
            student_answer=payload.student_answer,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
