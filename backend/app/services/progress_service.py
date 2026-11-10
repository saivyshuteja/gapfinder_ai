from sqlalchemy.orm import Session

from app.db.models import Answer, Attempt, GapReport, Topic
from app.schemas.progress import OverallProgress, TopicProgress


def get_progress(db: Session, user_id: int, document_id: int):
    topics = (
        db.query(Topic)
        .filter(Topic.document_id == document_id)
        .all()
    )

    reports = (
        db.query(GapReport)
        .filter(
            GapReport.user_id == user_id,
            GapReport.document_id == document_id,
        )
        .order_by(GapReport.created_at.desc())
        .all()
    )

    latest_reports = {}
    for report in reports:
        if report.topic_id not in latest_reports:
            latest_reports[report.topic_id] = report

    topic_items = []
    weak_topics = 0
    medium_topics = 0
    strong_topics = 0
    total_accuracy = 0.0

    for topic in topics:
        report = latest_reports.get(topic.id)
        attempts = (
            db.query(Attempt)
            .filter(
                Attempt.user_id == user_id,
                Attempt.document_id == document_id,
                Attempt.topic_id == topic.id,
            )
            .count()
        )

        accuracy = float(report.accuracy) if report else 0.0
        status = report.status if report else "strong"
        priority_score = float(report.priority_score) if report else 0.0

        if status == "weak":
            weak_topics += 1
        elif status == "medium":
            medium_topics += 1
        else:
            strong_topics += 1

        total_accuracy += accuracy

        topic_items.append(
            TopicProgress(
                topic_id=topic.id,
                topic_name=topic.name,
                attempts=attempts,
                accuracy=accuracy,
                status=status,
                exam_importance=float(topic.exam_importance),
                priority_score=priority_score,
            )
        )

    total_topics = len(topic_items)
    overall_accuracy = (total_accuracy / total_topics) if total_topics else 0.0

    return OverallProgress(
        total_topics=total_topics,
        weak_topics=weak_topics,
        medium_topics=medium_topics,
        strong_topics=strong_topics,
        overall_accuracy=round(overall_accuracy, 2),
        topics=topic_items,
    )


def get_progress_history(db: Session, user_id: int, document_id: int) -> list[dict]:
    attempts = (
        db.query(Attempt, Topic.name)
        .join(Topic, Topic.id == Attempt.topic_id)
        .filter(
            Attempt.user_id == user_id,
            Attempt.document_id == document_id,
            Attempt.status == "completed",
        )
        .order_by(Attempt.started_at, Attempt.id)
        .all()
    )

    document_attempt_number = 0
    topic_attempt_numbers = {}
    history = []
    for attempt, topic_name in attempts:
        answers = (
            db.query(Answer.is_correct)
            .filter(Answer.attempt_id == attempt.id)
            .all()
        )
        if not answers:
            continue

        document_attempt_number += 1
        topic_attempt_numbers[attempt.topic_id] = topic_attempt_numbers.get(attempt.topic_id, 0) + 1
        total_questions = len(answers)
        correct_answers = sum(1 for (is_correct,) in answers if is_correct)
        history.append({
            "attempt_id": attempt.id,
            "topic_id": attempt.topic_id,
            "topic_name": topic_name,
            "attempt_number": document_attempt_number,
            "topic_attempt_number": topic_attempt_numbers[attempt.topic_id],
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": round(correct_answers * 100 / total_questions, 2),
            "completed_at": (attempt.completed_at or attempt.started_at).isoformat(),
        })

    return history
