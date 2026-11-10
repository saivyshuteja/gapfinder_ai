import re

from sqlalchemy.orm import Session

from app.services.vector_search_service import (
    search_similar_chunks
)
from app.services.chunk_embedding_service import generate_and_store_chunk_embeddings

from app.services.llm_service import (
    generate_response
)


def build_context(
    results: list[dict]
) -> str:
    """
    Convert retrieved chunks into grounded
    context for the LLM.
    """

    context_parts = []

    for index, result in enumerate(
        results,
        start=1
    ):

        context_parts.append(
            f"""
SOURCE {index}

Document: {result["document_name"]}
Page: {result["page_number"]}
Unit: {result["unit"]}
Section: {result["topic"] or result["unit"] or f"Page {result['page_number']}"}

Content:
{result["content"]}
"""
        )

    return "\n\n".join(
        context_parts
    )


def answer_question(
    db: Session,
    question: str,
    user_id: int,
    document_id: int | None = None,
    top_k: int = 5,
):
    """
    Retrieve relevant chunks and generate
    a grounded answer.
    """

    generate_and_store_chunk_embeddings(
        db,
        document_id=document_id,
        user_id=user_id,
    )
    retrieved_chunks = search_similar_chunks(
        db=db,
        query=question,
        top_k=top_k,
        document_id=document_id,
        user_id=user_id,
    )

    if not retrieved_chunks:
        return {
            "answer": (
                "I could not find relevant "
                "information in the uploaded material."
            ),
            "sources": []
        }

    context = build_context(
        retrieved_chunks
    )

    prompt = f"""
You are the educational assistant for GapFinder AI.

Answer the student's question using ONLY
the provided source material.

Do NOT use outside knowledge.

If the answer cannot be supported by
the provided material, say:

"I could not find enough information
in the uploaded material to answer this."

Do not invent facts, examples, page numbers,
or citations.

Explain the answer clearly for a student. Cite every factual paragraph with an inline reference
such as [Source 1], using only the source numbers shown above.

-------------------------
SOURCE MATERIAL
-------------------------

{context}

-------------------------
STUDENT QUESTION
-------------------------

{question}

-------------------------
ANSWER
-------------------------
"""

    answer = generate_response(
        prompt=prompt,
        temperature=0.1
    )

    if not re.search(r"\[Source\s+\d+\]", answer, re.IGNORECASE):
        answer = answer.rstrip() + "\n\nSources: " + ", ".join(
            f"[Source {index}]" for index in range(1, len(retrieved_chunks) + 1)
        )

    sources = []

    for result in retrieved_chunks:

        sources.append({
            "chunk_id": result["id"],
            "document_id": result["document_id"],
            "document_name": result["document_name"],
            "page_number": result["page_number"],
            "unit": result["unit"],
            "topic": result["topic"],
            "section": result["topic"] or result["unit"] or f"Page {result['page_number']}",
            "similarity": result["similarity"]
        })

    return {
        "answer": answer,
        "sources": sources
    }