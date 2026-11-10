import json

from sqlalchemy.orm import Session

from app.db.models import Answer, Question
from app.services.llm_service import generate_response
from app.services.vector_search_service import search_similar_chunks


def _build_context(results: list[dict]) -> str:
    context_parts = []
    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"""
SOURCE {index}

Document ID: {result['document_id']}
Page: {result['page_number']}
Unit: {result.get('unit')}
Topic: {result.get('topic')}

Content:
{result['content']}
"""
        )
    return "\n\n".join(context_parts)


def evaluate_subjective_answer(
    db: Session,
    attempt_id: int,
    question_id: int,
    student_answer: str,
):
    question = (
        db.query(Question)
        .filter(Question.id == question_id)
        .first()
    )

    if not question:
        raise ValueError("Question not found.")

    if not student_answer or not student_answer.strip():
        raise ValueError("Student answer cannot be empty.")

    retrieved_chunks = search_similar_chunks(
        db=db,
        query=question.question,
        top_k=5,
    )

    if not retrieved_chunks:
        raise ValueError("No supporting material found for this question.")

    context = _build_context(retrieved_chunks)

    prompt = f"""
You are grading a student's subjective answer for GapFinder AI.

Evaluate the answer using ONLY the supplied source material.
Return only valid JSON, with the following structure:

{{
  "classification": "Correct | Partial | Incorrect",
  "score": 0.0,
  "evaluation_reason": "Short explanation of the grade.",
  "misconception": "Brief misconception summary or null",
  "supporting_evidence": "A quoted or paraphrased evidence from the source material.",
  "source_pages": [1, 2, 3]
}}

Question:
{question.question}

Student answer:
{student_answer}

Source material:
{context}
"""

    raw_response = generate_response(prompt=prompt, temperature=0.1)
    cleaned_response = (
        raw_response.replace("```json", "").replace("```", "").strip()
    )

    try:
        data = json.loads(cleaned_response)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM returned invalid subjective evaluation JSON.") from exc

    classification = str(data.get("classification", "Incorrect")).strip().title()
    if classification not in {"Correct", "Partial", "Incorrect"}:
        classification = "Incorrect"

    score = float(data.get("score", 0.0))
    score = max(0.0, min(1.0, score))

    supporting_evidence = str(
        data.get("supporting_evidence") or "The answer is grounded in the provided source material."
    )
    evaluation_reason = str(
        data.get("evaluation_reason") or "The answer was evaluated against the topic material."
    )
    misconception = data.get("misconception")
    if misconception is not None:
        misconception = str(misconception)

    source_pages = data.get("source_pages", [])
    if not isinstance(source_pages, list):
        source_pages = []
    source_pages = [int(page) for page in source_pages if str(page).strip()]
    if not source_pages:
        source_pages = [chunk["page_number"] for chunk in retrieved_chunks[:3]]

    answer = (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt_id, Answer.question_id == question_id)
        .first()
    )

    if answer is None:
        answer = Answer(
            attempt_id=attempt_id,
            question_id=question_id,
            student_answer=student_answer,
            is_correct=(classification != "Incorrect"),
            score=score,
        )
    else:
        answer.student_answer = student_answer
        answer.is_correct = classification != "Incorrect"
        answer.score = score

    answer.classification = classification
    answer.supporting_evidence = supporting_evidence
    answer.source_pages = json.dumps(source_pages)
    answer.evaluation_reason = evaluation_reason
    answer.misconception = misconception

    db.add(answer)
    db.commit()
    db.refresh(answer)

    return {
        "answer_id": answer.id,
        "question_id": question.id,
        "classification": classification,
        "score": round(score, 3),
        "evaluation_reason": evaluation_reason,
        "misconception": misconception,
        "supporting_evidence": supporting_evidence,
        "source_pages": source_pages,
    }
