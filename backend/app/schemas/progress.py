from pydantic import BaseModel


class TopicProgress(BaseModel):
    topic_id: int
    topic_name: str
    attempts: int
    accuracy: float
    status: str
    exam_importance: float
    priority_score: float


class OverallProgress(BaseModel):
    total_topics: int
    weak_topics: int
    medium_topics: int
    strong_topics: int
    overall_accuracy: float
    topics: list[TopicProgress]

    class Config:
        from_attributes = True
