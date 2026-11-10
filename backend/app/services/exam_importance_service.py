from sqlalchemy.orm import Session

from app.db.models import ExamQuestion, Topic


def calculate_exam_importance(
    db: Session,
    document_id: int
):
    topics = (
        db.query(Topic)
        .filter(
            Topic.document_id == document_id
        )
        .all()
    )

    if not topics:
        raise ValueError(
            "No topics found for this document."
        )

    question_counts = {}

    for topic in topics:
        count = (
            db.query(ExamQuestion)
            .filter(
                ExamQuestion.topic_id == topic.id
            )
            .count()
        )

        question_counts[topic.id] = count

    max_count = max(
        question_counts.values(),
        default=0
    )

    updated_topics = []

    for topic in topics:

        count = question_counts[topic.id]

        if max_count == 0:
            importance = 0.0
        else:
            importance = count / max_count

        topic.exam_question_count = count
        topic.exam_importance = round(
            importance,
            3
        )

        updated_topics.append(topic)

    db.commit()

    for topic in updated_topics:
        db.refresh(topic)

    return updated_topics


def get_exam_importance(
    db: Session,
    document_id: int
):
    return (
        db.query(Topic)
        .filter(
            Topic.document_id == document_id
        )
        .order_by(
            Topic.exam_importance.desc()
        )
        .all()
    )