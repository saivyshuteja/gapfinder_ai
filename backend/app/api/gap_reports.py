from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.gap_report import GapReportResponse
from app.services.gap_service import (
    generate_gap_report,
    get_gap_reports,
    get_topic_gap_report,
)
from app.services.revision_plan_service import refresh_latest_revision_plan

router = APIRouter(
    prefix="/gap-reports",
    tags=["Gap Analysis"]
)


@router.post(
    "/generate/{attempt_id}",
    response_model=GapReportResponse
)
def generate_report(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        report = generate_gap_report(
            db=db,
            attempt_id=attempt_id,
            user_id=current_user.id,
        )
        refresh_latest_revision_plan(
            db=db,
            user_id=current_user.id,
            document_id=report.document_id,
        )

        return report

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.get(
    "",
    response_model=list[GapReportResponse]
)
def list_gap_reports(
    document_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    reports = get_gap_reports(
        db=db,
        user_id=current_user.id,
        document_id=document_id
    )

    return reports


@router.get(
    "/topic/{topic_id}",
    response_model=GapReportResponse
)
def topic_gap_report(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    report = get_topic_gap_report(
        db=db,
        user_id=current_user.id,
        topic_id=topic_id
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Gap report not found."
        )

    return report