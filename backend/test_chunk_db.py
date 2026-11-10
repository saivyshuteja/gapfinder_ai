from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Chunk

from app.services.pdf_service import (
    extract_text_from_pdf
)

from app.services.chunk_service import (
    create_heading_chunks
)

from app.services.chunk_db_service import (
    save_chunks
)


PDF_PATH = (
    "storage/uploads/"
    "25ec8bdb-3b70-448b-bccc-f6f58688d3db.pdf"
)

DOCUMENT_ID = 1


# --------------------------------
# 1. Create database connection
# --------------------------------

engine = create_engine(
    settings.DATABASE_URL
)

SessionLocal = sessionmaker(
    bind=engine
)

db = SessionLocal()


try:

    # --------------------------------
    # 2. Extract PDF
    # --------------------------------

    pages = extract_text_from_pdf(
        PDF_PATH
    )

    print(
        f"Pages extracted: {len(pages)}"
    )


    # --------------------------------
    # 3. Create chunks
    # --------------------------------

    chunks = create_heading_chunks(
        pages,
        max_chunk_size=1500
    )

    print(
        f"Chunks created: {len(chunks)}"
    )


    # --------------------------------
    # 4. Save chunks
    # --------------------------------

    saved_chunks = save_chunks(
        db=db,
        document_id=DOCUMENT_ID,
        chunks=chunks
    )

    print(
        f"Chunks saved: {len(saved_chunks)}"
    )


    # --------------------------------
    # 5. Display first 5
    # --------------------------------

    for chunk in saved_chunks[:5]:

        print("\n============================")

        print(
            f"Database ID: {chunk.id}"
        )

        print(
            f"Document ID: {chunk.document_id}"
        )

        print(
            f"Chunk Index: {chunk.chunk_index}"
        )

        print(
            f"Page: {chunk.page_number}"
        )

        print(
            f"Unit: {chunk.unit}"
        )

        print(
            f"Topic: {chunk.topic}"
        )

        print("----------------------------")

        print(
            chunk.content[:500]
        )

finally:

    db.close()