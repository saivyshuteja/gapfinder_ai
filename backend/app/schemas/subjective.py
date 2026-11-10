from pydantic import BaseModel


class SubjectiveAnswerSubmit(BaseModel):
    question_id: int
    student_answer: str


class SubjectiveEvaluationResponse(BaseModel):
    answer_id: int
    question_id: int
    classification: str
    score: float
    evaluation_reason: str
    misconception: str | None
    supporting_evidence: str
    source_pages: list[int]

    class Config:
        from_attributes = True
