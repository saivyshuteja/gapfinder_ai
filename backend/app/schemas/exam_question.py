from datetime import datetime

from pydantic import BaseModel


class ExamQuestionCreate(BaseModel):
    question: str
    source_page: int | None = None
    topic_id: int
    document_id: int | None = None


class ExamQuestionResponse(BaseModel):
    id: int
    document_id: int
    topic_id: int
    question: str
    source_page: int | None
    created_at: datetime

    class Config:
        from_attributes = True