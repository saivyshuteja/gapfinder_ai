from app.services.pdf_service import extract_text_from_pdf
from app.services.chunk_service import create_heading_chunks


PDF_PATH = (
    "storage/uploads/"
    "25ec8bdb-3b70-448b-bccc-f6f58688d3db.pdf"
)


# Extract PDF
pages = extract_text_from_pdf(
    PDF_PATH
)

print(
    f"Total pages: {len(pages)}"
)


# Create heading-aware chunks
chunks = create_heading_chunks(
    pages,
    max_chunk_size=1500
)


print(
    f"Total chunks: {len(chunks)}"
)


# Display chunks
for chunk in chunks:

    print("\n================================")
    print(
        f"Chunk ID: {chunk['chunk_id']}"
    )

    print(
        f"Page: {chunk['page_number']}"
    )

    print(
        f"Unit: {chunk['unit']}"
    )

    print(
        f"Topic: {chunk['topic']}"
    )

    print("================================")

    print(
        chunk["text"]
    )