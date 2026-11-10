import json
import re

from sqlalchemy.orm import Session

from app.db.models import Chunk, Question, Topic

from app.services.llm_service import (
    generate_response
)


def build_question_context(
    results: list[dict]
) -> str:

    context_parts = []

    for index, result in enumerate(
        results,
        start=1
    ):

        context_parts.append(
            f"""
SOURCE {index}

Document ID:
{result["document_id"]}

Page:
{result["page_number"]}

Topic:
{result["topic"]}

Content:
{result["content"]}
"""
        )

    return "\n\n".join(
        context_parts
    )


def normalize_answer_key(answer: str, options: list[str]) -> str:
    answer = answer.strip()
    answer_match = re.search(
        r"(?:correct\s+)?(?:answer|option|choice)\s*(?:is\s*)?[:=]?\s*([A-D])\b",
        answer,
        re.IGNORECASE,
    )
    if answer_match:
        answer_key = answer_match.group(1).upper()
        if ord(answer_key) - ord("A") < len(options):
            return answer_key

    for index, option in enumerate(options):
        option_text = re.sub(r"^\s*[A-D][.)]\s*", "", option, flags=re.IGNORECASE)
        if answer.casefold() in {option.casefold(), option_text.casefold()}:
            return chr(ord("A") + index)

    match = re.match(r"^\s*([A-D])(?:[.)]|\s|$)", answer, re.IGNORECASE)
    if match and ord(match.group(1).upper()) - ord("A") < len(options):
        return match.group(1).upper()

    raise ValueError("Generated question has an invalid correct answer.")


def normalize_topic_label(value: str) -> str:
    value = value.strip().casefold()
    value = re.sub(r"^(?:chapter\s+\d+\s*[-:.)]?\s*|\d+(?:\.\d+)*[.)]?\s*)", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def clean_source_text(content: str, topic_name: str) -> str:
    lines = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or normalize_topic_label(line) == normalize_topic_label(topic_name):
            continue
        if re.match(r"^(?:unit|page|chapter|difficulty)\s*(?:[:#-]|\d|$)", line, re.IGNORECASE):
            continue
        lines.append(line)

    return "\n".join(lines).strip()


def is_metadata_question(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:page number|which page|\bunit\b|chapter number|difficulty level|numeric identifier|title of the content|title of the topic)\b",
            question,
            re.IGNORECASE,
        )
    )


def match_source_quote(
    quote: str,
    source_text_by_id: dict[int, str],
    source_chunks: list[Chunk],
):
    if len(quote.strip()) < 20:
        return None, None

    pattern = r"\s+".join(re.escape(part) for part in quote.split())
    for chunk in source_chunks:
        match = re.search(pattern, source_text_by_id[chunk.id], re.IGNORECASE)
        if match:
            return chunk, match.group(0)
    return None, None


def generate_diagnostic_questions(
    db: Session,
    topic_id: int,
    difficulty: str = "medium",
    count: int = 5,
) -> list[Question]:

    topic = (
        db.query(Topic)
        .filter(
            Topic.id == topic_id
        )
        .first()
    )

    if not topic:
        raise ValueError(
            "Topic not found."
        )

    candidate_chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == topic.document_id)
        .order_by(Chunk.chunk_index)
        .all()
    )
    normalized_topic = normalize_topic_label(topic.name)
    source_chunks = []
    source_text_by_id = {}
    for chunk in candidate_chunks:
        if not chunk.topic or normalize_topic_label(chunk.topic) != normalized_topic:
            continue
        if topic.unit and chunk.unit != topic.unit:
            continue
        source_text = clean_source_text(chunk.content, topic.name)
        if len(re.findall(r"\b\w+\b", source_text)) < 8:
            continue
        source_chunks.append(chunk)
        source_text_by_id[chunk.id] = source_text
        if len(source_chunks) == 10:
            break

    if not source_chunks:
        raise ValueError(
            "This topic only has a heading and no lesson text. Upload detailed notes for it before generating an assessment."
        )

    context = "\n\n".join(
        f"LESSON PASSAGE {index}\n{source_text_by_id[chunk.id]}"
        for index, chunk in enumerate(source_chunks, start=1)
    )

    prompt = f"""
You are an expert Python competitive-exam question setter.

Generate exactly {count} distinct multiple-choice diagnostic questions
for the selected topic:

{topic.name}

Unit:
{topic.unit}

Difficulty:
{difficulty}

Use only claims, rules, and examples explicitly supported by the lesson passages. Do not use outside
knowledge, even if it is generally true about Python. Ask rigorous questions about the selected
topic, not about document metadata. Include exactly one unambiguously correct option and ensure the
explanation is supported by the same cited passage. Never ask about page numbers, unit/chapter
labels, difficulty metadata, identifiers, or the title/layout of the source document.
Every question MUST include a source_quote copied verbatim from a lesson passage and source_page
matching that passage. The quote must support the tested concept and answer; do not cite a heading.
If the material cannot support the requested number of distinct questions, return fewer questions
and explain the limitation in an "insufficient_material" field instead of using outside knowledge.

Return ONLY valid JSON. Do not include markdown fences.

Required JSON structure:

{{
    "questions": [
        {{
            "question": "...",
            "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
            "correct_answer": "A",
            "explanation": "...",
            "source_quote": "...",
            "source_page": 1
        }}
    ]
}}

Use different concepts or code scenarios; do not repeat the same question. The explanation must only
paraphrase the cited source_quote and connect it to the correct option. Do not add general facts or
explain distractors using information absent from the source_quote.

-------------------------
SOURCE MATERIAL
-------------------------

{context}
"""

    raw_response = generate_response(
        prompt=prompt,
        temperature=0.1
    )

    cleaned_response = (
        raw_response
        .replace(
            "```json",
            ""
        )
        .replace(
            "```",
            ""
        )
        .strip()
    )

    try:
        data = json.loads(cleaned_response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM returned invalid question JSON."
        ) from exc

    if isinstance(data, dict) and data.get("insufficient_material"):
        raise ValueError(str(data["insufficient_material"]))

    question_data = data if isinstance(data, list) else data.get("questions") if isinstance(data, dict) else None
    if not isinstance(question_data, list) or len(question_data) != count:
        raise ValueError(f"Question generator did not return exactly {count} questions.")

    questions = []
    for item in question_data:
        if not isinstance(item, dict) or not item.get("question"):
            raise ValueError("Question generator returned an incomplete question.")

        if is_metadata_question(str(item["question"])):
            raise ValueError(
                "Question generator returned document metadata instead of Python concepts. Please generate again."
            )

        options = item.get("options")
        if not isinstance(options, list) or len(options) < 2:
            raise ValueError("Generated questions must have at least two answer options.")
        options = [str(option).strip() for option in options]
        answer_key = normalize_answer_key(str(item.get("correct_answer", "")), options)

        source_chunk, source_excerpt = match_source_quote(
            str(item.get("source_quote", "")),
            source_text_by_id,
            source_chunks,
        )
        if source_chunk is None:
            raise ValueError(
                "A generated question could not be verified against a verbatim passage in your material. Try fewer questions or add more detailed notes."
            )

        questions.append(
            Question(
                topic_id=topic.id,
                document_id=topic.document_id,
                question=str(item["question"]).strip(),
                question_type="mcq",
                difficulty=difficulty,
                options=json.dumps(options),
                correct_answer=answer_key,
                explanation=str(item.get("explanation") or ""),
                source_page=source_chunk.page_number,
                source_excerpt=source_excerpt,
                source_chunk_id=source_chunk.id,
            )
        )

    try:
        db.add_all(questions)
        db.commit()
        for question in questions:
            db.refresh(question)
    except Exception:
        db.rollback()
        raise

    return questions


def generate_diagnostic_question(
    db: Session,
    topic_id: int,
    difficulty: str = "medium",
) -> Question:
    return generate_diagnostic_questions(
        db=db,
        topic_id=topic_id,
        difficulty=difficulty,
        count=1,
    )[0]