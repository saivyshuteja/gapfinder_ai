from sqlalchemy.orm import Session

from app.db.models import ExamQuestion
from app.services.exam_question_extraction_service import (
    extract_exam_questions,
)
from app.services.exam_topic_mapping_service import (
    map_question_to_topic,
)


def ingest_exam_question_paper(
    db: Session,
    document_id: int,
    file_path: str,
    topic_document_id: int,
):

    extracted_questions = (
        extract_exam_questions(
            file_path
        )
    )

    if not extracted_questions:
        raise ValueError(
            "No complete numbered exam questions could be extracted from this PDF. The paper may be unnumbered or the scan may be unreadable; use a selectable-text copy or enter its questions manually."
        )

    created_questions = []

    for item in extracted_questions:

        question = item["question"]

        mapping = map_question_to_topic(
            db=db,
            document_id=document_id,
            question=question,
            topic_document_id=topic_document_id,
        )

        existing = (
            db.query(ExamQuestion)
            .filter(
                ExamQuestion.document_id == document_id,
                ExamQuestion.source_page == item["page_number"],
                ExamQuestion.question == question,
            )
            .first()
        )
        if not existing:
            db.add(ExamQuestion(
                document_id=document_id,
                topic_id=mapping["topic_id"],
                question=question,
                source_page=item["page_number"],
            ))

        created_questions.append({
            "question": question,
            "page_number": item["page_number"],
            "topic_id": mapping["topic_id"],
            "confidence": mapping["confidence"],
            "reason": mapping["reason"]
        })

    db.commit()

    return created_questions