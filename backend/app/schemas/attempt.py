from datetime import datetime
from pydantic import BaseModel


class AttemptStartResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    topic_id: int
    status: str
    started_at: datetime

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    question_id: int
    student_answer: str


class AnswerResponse(BaseModel):
    id: int
    attempt_id: int
    question_id: int
    student_answer: str
    is_correct: bool
    score: float
    evaluation_reason: str | None
    misconception: str | None
    answered_at: datetime

    class Config:
        from_attributes = True


class AttemptResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    topic_id: int
    status: str
    started_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True