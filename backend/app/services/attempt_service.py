from datetime import datetime
import json
import re

from sqlalchemy.orm import Session

from app.db.models import Attempt, Answer, Document, Question, Topic


def start_attempt(
    db: Session,
    user_id: int,
    topic_id: int
) -> Attempt:

    topic = (
        db.query(Topic)
        .join(Document, Document.id == Topic.document_id)
        .filter(Topic.id == topic_id, Document.user_id == user_id)
        .first()
    )

    if not topic:
        raise ValueError("Topic not found.")

    attempt = Attempt(
        user_id=user_id,
        document_id=topic.document_id,
        topic_id=topic.id,
        status="in_progress"
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


def submit_answer(
    db: Session,
    attempt_id: int,
    question_id: int,
    student_answer: str,
    user_id: int | None = None,
) -> Answer:

    attempt_query = db.query(Attempt).filter(Attempt.id == attempt_id)
    if user_id is not None:
        attempt_query = attempt_query.filter(Attempt.user_id == user_id)
    attempt = attempt_query.first()

    if not attempt:
        raise ValueError("Attempt not found.")

    if attempt.status != "in_progress":
        raise ValueError("This attempt is already completed.")

    question = (
        db.query(Question)
        .filter(Question.id == question_id)
        .filter(
            Question.topic_id == attempt.topic_id,
            Question.document_id == attempt.document_id,
        )
        .first()
    )

    if not question:
        raise ValueError("Question not found.")

    existing_answer = (
        db.query(Answer)
        .filter(
            Answer.attempt_id == attempt_id,
            Answer.question_id == question_id
        )
        .first()
    )

    if existing_answer:
        raise ValueError(
            "This question has already been answered."
        )

    options = question.options or []
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except json.JSONDecodeError:
            options = []

    submitted_text = (student_answer or "").strip()
    answer_match = re.match(r"^\s*([A-D])(?:[.)]|\s|$)", submitted_text, re.IGNORECASE)
    if answer_match:
        submitted_answer = answer_match.group(1).upper()
    else:
        submitted_answer = ""
        for index, option in enumerate(options):
            option_text = re.sub(r"^\s*[A-D][.)]\s*", "", str(option), flags=re.IGNORECASE)
            if submitted_text.casefold() in {str(option).strip().casefold(), option_text.casefold()}:
                submitted_answer = chr(ord("A") + index)
                break
        if not submitted_answer:
            submitted_answer = submitted_text[:1].upper()

    expected_answer = (
        question.correct_answer or ""
    ).strip().upper()

    is_correct = (
        submitted_answer == expected_answer
    )

    score = 1.0 if is_correct else 0.0

    if is_correct:
        reason = "Correct answer."
        misconception = None
    else:
        reason = (
            f"The selected answer was '{submitted_answer}', "
            f"but the correct answer is '{expected_answer}'."
        )

        misconception = (
            "The student may need to review this topic "
            "and understand why the correct option is supported "
            "by the learning material."
        )

    answer = Answer(
        attempt_id=attempt_id,
        question_id=question_id,
        student_answer=submitted_answer,
        is_correct=is_correct,
        score=score,
        evaluation_reason=reason,
        misconception=misconception
    )

    db.add(answer)
    db.commit()
    db.refresh(answer)

    return answer


def complete_attempt(
    db: Session,
    attempt_id: int,
    user_id: int | None = None,
) -> Attempt:

    attempt_query = db.query(Attempt).filter(Attempt.id == attempt_id)
    if user_id is not None:
        attempt_query = attempt_query.filter(Attempt.user_id == user_id)
    attempt = attempt_query.first()

    if not attempt:
        raise ValueError("Attempt not found.")

    attempt.status = "completed"
    attempt.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(attempt)

    return attempt


def get_attempt_answers(
    db: Session,
    attempt_id: int,
    user_id: int | None = None,
) -> list[Answer]:

    attempt_query = db.query(Attempt).filter(Attempt.id == attempt_id)
    if user_id is not None:
        attempt_query = attempt_query.filter(Attempt.user_id == user_id)
    attempt = attempt_query.first()

    if not attempt:
        raise ValueError("Attempt not found.")

    return (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt_id)
        .order_by(Answer.id)
        .all()
    )


def calculate_attempt_score(
    db: Session,
    attempt_id: int,
    user_id: int | None = None,
) -> dict:

    answers = get_attempt_answers(
        db=db,
        attempt_id=attempt_id,
        user_id=user_id,
    )

    total_questions = len(answers)

    if total_questions == 0:
        return {
            "total_questions": 0,
            "correct_answers": 0,
            "incorrect_answers": 0,
            "accuracy": 0.0
        }

    correct_answers = sum(
        1 for answer in answers
        if answer.is_correct
    )

    incorrect_answers = (
        total_questions - correct_answers
    )

    accuracy = (
        correct_answers / total_questions
    ) * 100

    return {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "incorrect_answers": incorrect_answers,
        "accuracy": round(accuracy, 2)
    }