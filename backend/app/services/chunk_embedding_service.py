from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.services.embedding_service import generate_embeddings


def generate_and_store_chunk_embeddings(
    db: Session,
    document_id: int | None = None,
    user_id: int | None = None,
    commit: bool = True,
):
    """
    Generate embeddings for chunks that do not
    already have embeddings.
    """

    query = db.query(Chunk).filter(Chunk.embedding.is_(None))
    if document_id is not None:
        query = query.filter(Chunk.document_id == document_id)
    if user_id is not None:
        query = query.join(Document, Document.id == Chunk.document_id).filter(
            Document.user_id == user_id
        )
    chunks = query.all()

    if not chunks:
        print("No chunks need embeddings.")
        return 0

    texts = [
        chunk.content
        for chunk in chunks
    ]

    print(
        f"Generating embeddings for {len(texts)} chunks..."
    )

    embeddings = generate_embeddings(
        texts
    )

    for chunk, embedding in zip(
        chunks,
        embeddings
    ):
        chunk.embedding = embedding

    if commit:
        db.commit()
    else:
        db.flush()

    print(
        f"Successfully stored embeddings for {len(chunks)} chunks."
    )

    return len(chunks)