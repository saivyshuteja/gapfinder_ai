from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.embedding_service import generate_embedding


def search_similar_chunks(
    db: Session,
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.0,
    document_id: int | None = None,
    user_id: int | None = None,
):
    """
    Search PostgreSQL using pgvector cosine distance.

    Returns the most semantically relevant chunks.
    """

    query_embedding = generate_embedding(
        query
    )

    filters = ["chunks.embedding IS NOT NULL"]
    params = {
        "query_embedding": str(query_embedding),
        "top_k": top_k,
    }
    if document_id is not None:
        filters.append("chunks.document_id = :document_id")
        params["document_id"] = document_id
    if user_id is not None:
        filters.append("documents.user_id = :user_id")
        params["user_id"] = user_id

    sql = text(f"""
        SELECT
            chunks.id,
            chunks.document_id,
            chunks.chunk_index,
            chunks.page_number,
            chunks.unit,
            chunks.topic,
            chunks.content,
            documents.filename AS document_name,

            chunks.embedding <=> CAST(
                :query_embedding AS vector
            ) AS distance

        FROM chunks
        JOIN documents ON documents.id = chunks.document_id

                WHERE {" AND ".join(filters)}

        ORDER BY chunks.embedding <=> CAST(
            :query_embedding AS vector
        )

        LIMIT :top_k
    """)

    result = db.execute(sql, params)

    rows = result.mappings().all()

    results = []

    for row in rows:

        distance = float(
            row["distance"]
        )

        similarity = 1.0 - distance

        if similarity < min_similarity:
            continue

        results.append({
            "id": row["id"],
            "document_id": row["document_id"],
            "document_name": row["document_name"],
            "chunk_index": row["chunk_index"],
            "page_number": row["page_number"],
            "unit": row["unit"],
            "topic": row["topic"],
            "content": row["content"],
            "distance": distance,
            "similarity": similarity
        })

    return results