from datetime import datetime

from typing import Literal

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    document_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentTypeUpdate(BaseModel):
    document_type: Literal["syllabus", "material", "exam"]