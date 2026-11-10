from sqlalchemy.orm import Session

from app.db.models import ExamQuestion, Topic


def create_exam_question(
    db: Session,
    topic_id: int,
    question: str,
    source_page: int | None = None,
    exam_document_id: int | None = None,
):

    topic = (
        db.query(Topic)
        .filter(Topic.id == topic_id)
        .first()
    )

    if not topic:
        raise ValueError(
            "Topic not found."
        )

    query = db.query(ExamQuestion).filter(
        ExamQuestion.topic_id == topic.id,
        ExamQuestion.question == question,
    )
    if exam_document_id is not None:
        query = query.filter(ExamQuestion.document_id == exam_document_id)
    if source_page is not None:
        query = query.filter(ExamQuestion.source_page == source_page)
    existing = query.first()
    if existing:
        return existing

    exam_question = ExamQuestion(
        document_id=exam_document_id or topic.document_id,
        topic_id=topic.id,
        question=question,
        source_page=source_page
    )

    db.add(exam_question)
    db.commit()
    db.refresh(exam_question)

    return exam_question


def get_exam_questions(
    db: Session,
    topic_id: int
):

    return (
        db.query(ExamQuestion)
        .filter(
            ExamQuestion.topic_id == topic_id
        )
        .order_by(
            ExamQuestion.id
        )
        .all()
    )