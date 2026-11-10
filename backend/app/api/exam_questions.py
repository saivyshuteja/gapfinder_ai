from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Document, Topic, User
from app.schemas.exam_question import ExamQuestionCreate, ExamQuestionResponse
from app.schemas.exam_ingestion import (
    ExamIngestionResponse,
)
from app.services.exam_question_ingestion_service import (
    ingest_exam_question_paper,
)
from app.services.exam_question_service import (
    create_exam_question,
    get_exam_questions,
)
from app.services.exam_importance_service import calculate_exam_importance

router = APIRouter(
    prefix="/exam-questions",
    tags=["Exam Questions"]
)


@router.post(
    "",
    response_model=ExamQuestionResponse
)
def add_exam_question(
    payload: ExamQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        topic = (
            db.query(Topic)
            .join(Document, Document.id == Topic.document_id)
            .filter(Topic.id == payload.topic_id, Document.user_id == current_user.id)
            .first()
        )
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found.")

        exam_document_id = payload.document_id
        if exam_document_id is not None:
            exam_document = db.query(Document).filter(
                Document.id == exam_document_id,
                Document.user_id == current_user.id,
                Document.document_type == "exam",
            ).first()
            if not exam_document:
                raise HTTPException(status_code=404, detail="Past-paper document not found.")

        saved = create_exam_question(
            db=db,
            topic_id=payload.topic_id,
            question=payload.question,
            source_page=payload.source_page,
            exam_document_id=exam_document_id,
        )
        calculate_exam_importance(db=db, document_id=topic.document_id)
        return saved

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


@router.get(
    "/topic/{topic_id}",
    response_model=list[ExamQuestionResponse]
)
def list_exam_questions(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    topic = (
        db.query(Topic)
        .join(Document, Document.id == Topic.document_id)
        .filter(Topic.id == topic_id, Document.user_id == current_user.id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    return get_exam_questions(
        db=db,
        topic_id=topic_id
    )
@router.post(
    "/ingest/{document_id}",
    response_model=ExamIngestionResponse
)
def ingest_exam_paper(
    document_id: int,
    topic_document_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    if document.file_type.lower() != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Exam question paper must be a PDF."
        )
    if document.document_type != "exam":
        raise HTTPException(status_code=400, detail="Upload or classify this file as a past exam paper first.")

    topic_document = (
        db.query(Document)
        .filter(
            Document.id == topic_document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )
    if not topic_document:
        raise HTTPException(status_code=404, detail="Syllabus document not found.")
    if topic_document.document_type == "exam":
        raise HTTPException(status_code=400, detail="Choose a syllabus or study material document.")

    try:

        mappings = ingest_exam_question_paper(
            db=db,
            document_id=document_id,
            file_path=document.file_path,
            topic_document_id=topic_document_id,
        )
        calculate_exam_importance(db=db, document_id=topic_document_id)

        return {
            "document_id": document_id,
            "questions_processed": len(
                mappings
            ),
            "mappings": mappings
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )