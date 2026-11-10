from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Chunk

from app.services.chunk_embedding_service import (
    generate_and_store_chunk_embeddings
)


engine = create_engine(
    settings.DATABASE_URL
)

SessionLocal = sessionmaker(
    bind=engine
)

db = SessionLocal()


try:

    count = generate_and_store_chunk_embeddings(
        db
    )

    print()
    print(
        f"Embeddings processed: {count}"
    )

    print("\nChecking database...")

    chunks = (
        db.query(Chunk)
        .filter(
            Chunk.embedding.isnot(None)
        )
        .limit(3)
        .all()
    )

    for chunk in chunks:

        print("\n============================")

        print(
            f"Chunk ID: {chunk.id}"
        )

        print(
            f"Topic: {chunk.topic}"
        )

        print(
            f"Page: {chunk.page_number}"
        )

        print(
            f"Embedding dimension: "
            f"{len(chunk.embedding)}"
        )

        print(
            "First 5 values:"
        )

        print(
            chunk.embedding[:5]
        )

finally:

    db.close()