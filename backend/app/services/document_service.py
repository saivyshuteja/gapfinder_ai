import os
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Chunk, Document
from app.services.chunk_db_service import save_chunks
from app.services.chunk_service import create_heading_chunks
from app.services.chunk_embedding_service import generate_and_store_chunk_embeddings
from app.services.pdf_service import extract_text_from_pdf


async def save_uploaded_file(
    file: UploadFile
) -> str:

    upload_dir = settings.UPLOAD_DIR

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    file_extension = os.path.splitext(
        file.filename
    )[1]

    unique_filename = (
        f"{uuid.uuid4()}{file_extension}"
    )

    file_path = os.path.join(
    upload_dir,
    unique_filename
    ).replace("\\", "/")

    file_content = await file.read()

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(file_content)

    return file_path


def process_document(db: Session, document: Document) -> int:
    existing_chunk = (
        db.query(Chunk.id)
        .filter(Chunk.document_id == document.id)
        .first()
    )
    if existing_chunk:
        chunk_count = db.query(Chunk).filter(Chunk.document_id == document.id).count()
        generate_and_store_chunk_embeddings(
            db,
            document_id=document.id,
            commit=False,
        )
        return chunk_count

    pages = extract_text_from_pdf(document.file_path)
    chunks = create_heading_chunks(pages, max_chunk_size=1500)
    if not chunks:
        raise ValueError(
            "No readable text was found in this PDF. Scanned PDFs need OCR before upload."
        )

    save_chunks(
        db=db,
        document_id=document.id,
        chunks=chunks,
        commit=False,
    )
    generate_and_store_chunk_embeddings(
        db,
        document_id=document.id,
        commit=False,
    )
    return len(chunks)