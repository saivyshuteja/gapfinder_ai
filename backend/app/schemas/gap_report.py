from datetime import datetime

from pydantic import BaseModel


class GapReportResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    topic_id: int
    attempt_id: int

    total_questions: int
    correct_answers: int
    incorrect_answers: int

    accuracy: float

    status: str

    weakness_score: float
    priority_score: float

    reason: str | None

    created_at: datetime

    class Config:
        from_attributes = True