from pydantic import BaseModel


class ExamQuestionMappingResponse(BaseModel):
    question: str
    page_number: int | None
    topic_id: int
    confidence: float
    reason: str


class ExamIngestionResponse(BaseModel):
    document_id: int
    questions_processed: int
    mappings: list[ExamQuestionMappingResponse]