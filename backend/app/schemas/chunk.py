from pydantic import BaseModel


class ChunkResponse(BaseModel):

    id: int
    document_id: int
    chunk_index: int
    page_number: int
    unit: str | None
    topic: str | None
    content: str

    class Config:
        from_attributes = True