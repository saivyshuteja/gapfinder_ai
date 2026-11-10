import json

from sqlalchemy.orm import Session

from app.db.models import Chunk, Topic
from app.services.llm_service import generate_response
from app.services.vector_search_service import search_similar_chunks


def build_topic_context(
    topics: list[Topic]
) -> str:

    parts = []

    for topic in topics:

        parts.append(
            f"""
TOPIC ID: {topic.id}
UNIT: {topic.unit}
TOPIC NAME: {topic.name}
DESCRIPTION: {topic.description or ""}
"""
        )

    return "\n".join(parts)


def map_question_to_topic(
    db: Session,
    document_id: int,
    question: str,
    topic_document_id: int | None = None,
) -> dict:
    topic_document_id = topic_document_id or document_id

    topics = (
        db.query(Topic)
        .filter(
            Topic.document_id == topic_document_id
        )
        .all()
    )

    if not topics:
        raise ValueError(
            "No topics found for this document."
        )

    has_embeddings = (
        db.query(Chunk.id)
        .filter(
            Chunk.document_id == topic_document_id,
            Chunk.embedding.is_not(None),
        )
        .first()
        is not None
    )
    retrieved_chunks = (
        search_similar_chunks(
            db=db,
            query=question,
            top_k=5,
            document_id=topic_document_id,
        )
        if has_embeddings
        else []
    )

    topic_context = build_topic_context(
        topics
    )

    retrieved_context = ""

    for index, chunk in enumerate(
        retrieved_chunks,
        start=1
    ):
        retrieved_context += f"""
SOURCE {index}

Page:
{chunk["page_number"]}

Topic:
{chunk["topic"]}

Content:
{chunk["content"]}

Similarity:
{chunk["similarity"]}
"""

    prompt = f"""
You are the exam question classification engine
for GapFinder AI.

Your task is to identify which learning topic
best matches the exam question.

EXAM QUESTION:
{question}

AVAILABLE TOPICS:
{topic_context}

RELEVANT TEXTBOOK MATERIAL:
{retrieved_context}

Rules:

1. Select exactly ONE topic.
2. The selected topic must come from the AVAILABLE TOPICS.
3. Use the textbook evidence to make the decision.
4. Do not invent a topic.
5. Return only valid JSON.

Required format:

{{
    "topic_id": 123,
    "confidence": 0.92,
    "reason": "The question directly tests..."
}}
"""

    response = generate_response(
        prompt=prompt,
        temperature=0.0
    )

    cleaned = (
        response
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        result = json.loads(
            cleaned
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM returned invalid topic mapping JSON."
        ) from exc

    topic_ids = {
        topic.id
        for topic in topics
    }

    topic_id = result.get(
        "topic_id"
    )

    if topic_id not in topic_ids:
        raise ValueError(
            "LLM returned an invalid topic ID."
        )

    confidence = float(
        result.get(
            "confidence",
            0.0
        )
    )

    return {
        "topic_id": topic_id,
        "confidence": max(
            0.0,
            min(1.0, confidence)
        ),
        "reason": result.get(
            "reason",
            ""
        )
    }