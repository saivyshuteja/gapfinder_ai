from sqlalchemy.orm import Session

from app.db.models import Answer, Attempt, GapReport, Question


def get_retest_topics(db: Session, user_id: int, document_id: int):
    reports = (
        db.query(GapReport)
        .filter(
            GapReport.user_id == user_id,
            GapReport.document_id == document_id,
        )
        .order_by(GapReport.priority_score.desc())
        .all()
    )
    return [report for report in reports if report.status in {"weak", "medium"}]


def get_retest_questions(db: Session, topic_id: int):
    return (
        db.query(Question)
        .filter(Question.topic_id == topic_id)
        .order_by(Question.id)
        .all()
    )


def _calculate_attempt_accuracy(db: Session, attempt_id: int) -> float:
    answers = (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt_id)
        .all()
    )
    if not answers:
        return 0.0
    correct = sum(1 for answer in answers if answer.is_correct)
    return round((correct / len(answers)) * 100, 2)


def compare_attempts(db: Session, previous_attempt_id: int, new_attempt_id: int):
    previous_attempt = db.query(Attempt).filter(Attempt.id == previous_attempt_id).first()
    new_attempt = db.query(Attempt).filter(Attempt.id == new_attempt_id).first()

    if not previous_attempt or not new_attempt:
        raise ValueError("Attempt not found.")

    previous_accuracy = _calculate_attempt_accuracy(db, previous_attempt_id)
    new_accuracy = _calculate_attempt_accuracy(db, new_attempt_id)
    improvement = round(new_accuracy - previous_accuracy, 2)

    return {
        "previous_attempt_id": previous_attempt.id,
        "new_attempt_id": new_attempt.id,
        "previous_accuracy": previous_accuracy,
        "new_accuracy": new_accuracy,
        "improvement": improvement,
        "improved": improvement > 0,
    }
