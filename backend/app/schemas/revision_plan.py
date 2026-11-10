from datetime import datetime, date

from pydantic import BaseModel, Field


class RevisionPlanCreate(BaseModel):
    document_id: int

    exam_date: date | None = None

    available_minutes_per_day: int = Field(
        gt=0,
        le=1440
    )

    total_days: int = Field(
        gt=0,
        le=365
    )


class RevisionTask(BaseModel):
    topic_id: int
    topic_name: str
    priority_score: float
    status: str
    accuracy: float
    exam_importance: float

    allocated_minutes: int

    activity: str
    objective: str


class RevisionDay(BaseModel):
    day: int
    date: date | None
    total_minutes: int
    tasks: list[RevisionTask]


class RevisionPlanResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    exam_date: datetime | None
    available_minutes_per_day: int
    total_days: int
    plan_data: str
    created_at: datetime

    class Config:
        from_attributes = True