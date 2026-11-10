import json

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import (
    GapReport,
    RevisionPlan,
    Topic,
)


def get_latest_gap_reports(
    db: Session,
    user_id: int,
    document_id: int
):
    reports = (
        db.query(GapReport)
        .filter(
            GapReport.user_id == user_id,
            GapReport.document_id == document_id
        )
        .order_by(
            GapReport.topic_id,
            GapReport.created_at.desc()
        )
        .all()
    )

    latest = {}

    for report in reports:

        if report.topic_id not in latest:
            latest[report.topic_id] = report

    return list(latest.values())


def calculate_topic_minutes(
    report: GapReport,
    total_available_minutes: int
) -> int:

    priority = max(
        report.priority_score,
        0.01
    )

    return priority * total_available_minutes


def build_revision_tasks(
    db: Session,
    reports: list[GapReport],
    daily_minutes: int
):

    if not reports:
        raise ValueError(
            "No gap reports found. Complete a diagnostic first."
        )

    tasks = []

    for report in reports:

        topic = (
            db.query(Topic)
            .filter(
                Topic.id == report.topic_id
            )
            .first()
        )

        if not topic:
            continue

        weakness = max(0.0, min(1.0, 1.0 - report.accuracy / 100))
        exam_importance = max(0.0, min(1.0, topic.exam_importance))
        priority_score = round(0.7 * weakness + 0.3 * exam_importance, 3)

        if report.status == "weak":
            activity = (
                "Concept revision + guided practice"
            )

            objective = (
                f"Rebuild understanding of {topic.name} "
                "using the uploaded learning material."
            )

        elif report.status == "medium":
            activity = (
                "Targeted practice + error review"
            )

            objective = (
                f"Improve application of {topic.name} "
                "and eliminate recurring mistakes."
            )

        else:
            activity = (
                "Quick review + retention practice"
            )

            objective = (
                f"Maintain proficiency in {topic.name}."
            )

        tasks.append({
            "topic_id": topic.id,
            "topic_name": topic.name,
            "priority_score": priority_score,
            "status": report.status,
            "accuracy": report.accuracy,
            "exam_importance": exam_importance,
            "allocated_minutes": 0,
            "activity": activity,
            "objective": objective,
        })

    tasks.sort(
        key=lambda item: item["priority_score"],
        reverse=True
    )

    return tasks


def generate_revision_plan(
    db: Session,
    user_id: int,
    document_id: int,
    available_minutes_per_day: int,
    total_days: int,
    exam_date=None
):

    reports = get_latest_gap_reports(
        db=db,
        user_id=user_id,
        document_id=document_id
    )

    tasks = build_revision_tasks(
        db=db,
        reports=reports,
        daily_minutes=available_minutes_per_day
    )

    if not tasks:
        raise ValueError(
            "No revision topics available."
        )

    plan_days = []

    start_date = date.today()
    tasks_per_day = min(len(tasks), max(1, available_minutes_per_day // 30))
    minutes_per_task, extra_minutes = divmod(
        available_minutes_per_day,
        tasks_per_day,
    )

    for day_number in range(
        1,
        total_days + 1
    ):

        if exam_date:
            current_date = (
                exam_date -
                timedelta(
                    days=total_days - day_number
                )
            )

        else:
            current_date = (
                start_date +
                timedelta(
                    days=day_number - 1
                )
            )

        day_tasks = []
        start_index = ((day_number - 1) * tasks_per_day) % len(tasks)
        for offset in range(tasks_per_day):
            task = tasks[(start_index + offset) % len(tasks)].copy()
            task["allocated_minutes"] = minutes_per_task + (1 if offset < extra_minutes else 0)
            day_tasks.append(task)

        plan_days.append({
            "day": day_number,
            "date": current_date.isoformat(),
            "total_minutes": available_minutes_per_day,
            "tasks": day_tasks
        })

    plan_data = json.dumps(
        plan_days
    )

    plan = (
        db.query(RevisionPlan)
        .filter(
            RevisionPlan.user_id == user_id,
            RevisionPlan.document_id == document_id,
        )
        .order_by(RevisionPlan.created_at.desc())
        .first()
    )
    if plan is None:
        plan = RevisionPlan(user_id=user_id, document_id=document_id)
        db.add(plan)

    plan.exam_date = exam_date
    plan.available_minutes_per_day = available_minutes_per_day
    plan.total_days = total_days
    plan.plan_data = plan_data
    plan.created_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)

    return plan


def refresh_latest_revision_plan(
    db: Session,
    user_id: int,
    document_id: int,
):
    plan = (
        db.query(RevisionPlan)
        .filter(
            RevisionPlan.user_id == user_id,
            RevisionPlan.document_id == document_id,
        )
        .order_by(RevisionPlan.created_at.desc())
        .first()
    )
    if plan is None:
        return None

    exam_date = plan.exam_date.date() if plan.exam_date else None
    return generate_revision_plan(
        db=db,
        user_id=user_id,
        document_id=document_id,
        available_minutes_per_day=plan.available_minutes_per_day,
        total_days=plan.total_days,
        exam_date=exam_date,
    )