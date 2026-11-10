from datetime import datetime

from pydantic import BaseModel


class QuestionResponse(BaseModel):

    id: int
    topic_id: int
    document_id: int

    question: str
    question_type: str
    difficulty: str

    options: str | None
    correct_answer: str | None
    explanation: str | None

    source_page: int | None
    source_excerpt: str | None
    source_chunk_id: int | None

    created_at: datetime

    class Config:
        from_attributes = True