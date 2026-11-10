import re

from sqlalchemy.orm import Session

from app.db.models import Chunk, Topic
from app.services.chunk_service import is_real_topic_heading, is_unit_heading


INVALID_TOPICS = {
    "HELLOCOLLEGE",
    "COLLEGE",
    "MRCET",
    "LECTURE NOTES",
    "SYLLABUS",
    "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING",
}


def normalize_topic(topic: str | None) -> str | None:
    if not topic:
        return None

    topic = topic.strip()
    topic = re.sub(r"\s+", " ", topic)

    if not topic:
        return None

    if is_unit_heading(topic) or not is_real_topic_heading(topic):
        return None

    if len(topic) > 120:
        return None

    if topic.upper() in INVALID_TOPICS:
        return None

    if topic.startswith(("[", "{", "(")):
        return None

    if any(
        value in topic
        for value in ["[", "]", "{", "}", "://", "\\", "/"]
    ):
        return None

    if not re.search(r"[A-Za-z]", topic):
        return None

    return topic


def extract_topics_from_chunks(
    db: Session,
    document_id: int
) -> list[dict]:

    chunks = (
        db.query(Chunk)
        .filter(
            Chunk.document_id == document_id
        )
        .all()
    )

    topics = {}

    for chunk in chunks:
        topic_name = normalize_topic(chunk.topic)
        if not topic_name:
            continue

        key = (
            document_id,
            chunk.unit,
            topic_name.lower()
        )

        if key not in topics:
            topics[key] = {
                "document_id": document_id,
                "unit": chunk.unit,
                "name": topic_name,
            }

    if not topics and any(chunk.content.strip() for chunk in chunks):
        return [{
            "document_id": document_id,
            "unit": None,
            "name": "General concepts",
        }]

    return list(topics.values())


def get_section_number(name: str) -> str | None:
    match = re.match(r"^(\d+(?:\.\d+)*)(?:[.)])?\s+\S", name)
    return match.group(1) if match else None


def save_topics(
    db: Session,
    topics: list[dict]
) -> list[Topic]:

    topics_by_key = {}

    for topic_data in topics:

        existing = (
            db.query(Topic)
            .filter(
                Topic.document_id
                == topic_data["document_id"],
                Topic.unit
                == topic_data["unit"],
                Topic.name
                == topic_data["name"]
            )
            .first()
        )

        topic = existing or Topic(
            document_id=topic_data["document_id"],
            unit=topic_data["unit"],
            name=topic_data["name"],
        )
        if existing is None:
            db.add(topic)
        key = (topic_data["document_id"], topic_data["unit"], topic_data["name"])
        topics_by_key[key] = topic

    db.flush()

    by_section = {}
    for key, topic in topics_by_key.items():
        section_number = get_section_number(topic.name)
        if section_number:
            by_section[(topic.document_id, topic.unit, section_number)] = topic

    for topic in topics_by_key.values():
        section_number = get_section_number(topic.name)
        parent_number = section_number.rsplit(".", 1)[0] if section_number and "." in section_number else None
        parent = by_section.get((topic.document_id, topic.unit, parent_number)) if parent_number else None
        topic.parent_topic_id = parent.id if parent and parent.id != topic.id else None

    db.commit()
    saved_topics = list(topics_by_key.values())
    for topic in saved_topics:
        db.refresh(topic)

    return saved_topics


def generate_topics_for_document(
    db: Session,
    document_id: int
) -> list[Topic]:

    topics = extract_topics_from_chunks(
        db=db,
        document_id=document_id
    )

    return save_topics(
        db=db,
        topics=topics
    )