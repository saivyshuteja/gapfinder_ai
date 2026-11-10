import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User

from app.schemas.revision_plan import (
    RevisionPlanCreate,
    RevisionPlanResponse,
)

from app.services.revision_plan_service import (
    generate_revision_plan,
)

router = APIRouter(
    prefix="/revision-plans",
    tags=["Revision Plans"]
)


@router.post(
    "/generate",
    response_model=RevisionPlanResponse
)
def create_revision_plan(
    payload: RevisionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        plan = generate_revision_plan(
            db=db,
            user_id=current_user.id,
            document_id=payload.document_id,
            available_minutes_per_day=(
                payload.available_minutes_per_day
            ),
            total_days=payload.total_days,
            exam_date=payload.exam_date
        )

        return plan

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.get(
    "/{plan_id}",
    response_model=RevisionPlanResponse
)
def get_revision_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    from app.db.models import RevisionPlan

    plan = (
        db.query(RevisionPlan)
        .filter(
            RevisionPlan.id == plan_id,
            RevisionPlan.user_id == current_user.id
        )
        .first()
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Revision plan not found."
        )

    return plan


@router.get(
    "/document/{document_id}"
)
def get_document_revision_plans(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    from app.db.models import RevisionPlan

    plans = (
        db.query(RevisionPlan)
        .filter(
            RevisionPlan.document_id == document_id,
            RevisionPlan.user_id == current_user.id
        )
        .order_by(
            RevisionPlan.created_at.desc()
        )
        .all()
    )

    result = []

    for plan in plans:

        result.append({
            "id": plan.id,
            "document_id": plan.document_id,
            "exam_date": plan.exam_date,
            "available_minutes_per_day": (
                plan.available_minutes_per_day
            ),
            "total_days": plan.total_days,
            "plan": json.loads(
                plan.plan_data
            ),
            "created_at": plan.created_at
        })

    return result