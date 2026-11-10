from typing import List, Dict

from sqlalchemy.orm import Session

from app.db.models import Chunk


def save_chunks(
    db: Session,
    document_id: int,
    chunks: List[Dict],
    commit: bool = True,
):
    """
    Save processed chunks into PostgreSQL.
    """

    saved_chunks = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        db_chunk = Chunk(
            document_id=document_id,
            chunk_index=index,
            page_number=chunk[
                "page_number"
            ],
            unit=chunk.get(
                "unit"
            ),
            topic=chunk.get(
                "topic"
            ),
            content=chunk[
                "text"
            ]
        )

        db.add(db_chunk)

        saved_chunks.append(
            db_chunk
        )

    if commit:
        db.commit()
        for chunk in saved_chunks:
            db.refresh(chunk)
    else:
        db.flush()

    return saved_chunks