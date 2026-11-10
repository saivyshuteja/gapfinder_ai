from sqlalchemy.orm import Session

from app.db.models import (
    Answer,
    Attempt,
    GapReport,
    Question,
    Topic,
)


def calculate_status(accuracy: float) -> str:
    if accuracy < 50:
        return "weak"

    if accuracy < 75:
        return "medium"

    return "strong"


def calculate_weakness_score(accuracy: float) -> float:
    """
    Converts accuracy into a weakness score.

    0% accuracy  -> 1.0 weakness
    50% accuracy -> 0.5 weakness
    100% accuracy -> 0.0 weakness
    """

    score = 1.0 - (accuracy / 100)

    return round(
        max(0.0, min(1.0, score)),
        3
    )


def calculate_priority_score(
    weakness_score: float,
    exam_importance: float = 1.0
) -> float:

    priority = (
        weakness_score * exam_importance
    )

    return round(priority, 3)


def build_gap_reason(
    topic_name: str,
    accuracy: float,
    status: str,
    total_questions: int,
    incorrect_answers: int,
    missed_focus: list[str],
) -> str:

    if incorrect_answers:
        reason = (
            f"You got {incorrect_answers} of {total_questions} questions on "
            f"{topic_name} wrong ({accuracy:.1f}% accuracy)."
        )
        if missed_focus:
            focus = "; ".join(f'“{item[:180]}”' for item in missed_focus[:2])
            reason += f" Review these source passages from the missed questions: {focus}."
        return reason

    return f"You answered all {total_questions} questions on {topic_name} correctly. Keep it fresh with spaced review."


def generate_gap_report(
    db: Session,
    attempt_id: int,
    user_id: int | None = None,
) -> GapReport:

    attempt_query = db.query(Attempt).filter(Attempt.id == attempt_id)
    if user_id is not None:
        attempt_query = attempt_query.filter(Attempt.user_id == user_id)
    attempt = attempt_query.first()

    if not attempt:
        raise ValueError("Attempt not found.")

    answers = (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt_id)
        .all()
    )

    if not answers:
        raise ValueError(
            "No answers found for this attempt."
        )

    topic = (
        db.query(Topic)
        .filter(Topic.id == attempt.topic_id)
        .first()
    )

    if not topic:
        raise ValueError("Topic not found.")

    total_questions = len(answers)

    correct_answers = sum(
        1
        for answer in answers
        if answer.is_correct
    )

    incorrect_answers = (
        total_questions - correct_answers
    )

    accuracy = (
        correct_answers /
        total_questions
    ) * 100

    accuracy = round(
        accuracy,
        2
    )

    status = calculate_status(
        accuracy
    )

    weakness_score = (
        calculate_weakness_score(
            accuracy
        )
    )

    # For now exam importance is 1.0.
    # Later this will come from the topic's
    # exam/question-paper frequency.
    exam_importance = topic.exam_importance

    priority_score = (
        calculate_priority_score(
            weakness_score,
            exam_importance
        )
    )

    reason = build_gap_reason(
        topic_name=topic.name,
        accuracy=accuracy,
        status=status,
        total_questions=total_questions,
        incorrect_answers=incorrect_answers,
        missed_focus=[
            excerpt or question
            for excerpt, question in (
                db.query(Question.source_excerpt, Question.question)
                .join(Answer, Answer.question_id == Question.id)
                .filter(
                    Answer.attempt_id == attempt_id,
                    Answer.is_correct.is_(False),
                )
                .order_by(Answer.id)
                .all()
            )
        ],
    )

    report = GapReport(
        user_id=attempt.user_id,
        document_id=attempt.document_id,
        topic_id=attempt.topic_id,
        attempt_id=attempt.id,
        total_questions=total_questions,
        correct_answers=correct_answers,
        incorrect_answers=incorrect_answers,
        accuracy=accuracy,
        status=status,
        weakness_score=weakness_score,
        priority_score=priority_score,
        reason=reason
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


def get_gap_reports(
    db: Session,
    user_id: int,
    document_id: int | None = None
):

    query = (
        db.query(GapReport)
        .filter(
            GapReport.user_id == user_id
        )
    )

    if document_id is not None:
        query = query.filter(
            GapReport.document_id == document_id
        )

    return (
        query
        .order_by(
            GapReport.priority_score.desc()
        )
        .all()
    )


def get_topic_gap_report(
    db: Session,
    user_id: int,
    topic_id: int
):

    return (
        db.query(GapReport)
        .filter(
            GapReport.user_id == user_id,
            GapReport.topic_id == topic_id
        )
        .order_by(
            GapReport.created_at.desc()
        )
        .first()
    )