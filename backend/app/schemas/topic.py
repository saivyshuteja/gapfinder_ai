from datetime import datetime

from pydantic import BaseModel


class TopicResponse(BaseModel):
    id: int
    document_id: int
    parent_topic_id: int | None
    unit: str | None
    name: str
    description: str | None

    exam_question_count: int
    exam_importance: float

    created_at: datetime

    class Config:
        from_attributes = True