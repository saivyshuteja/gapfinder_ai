import re

from app.services.pdf_service import extract_text_from_pdf


def clean_question_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def is_question_start(line: str) -> bool:
    line = line.strip()

    patterns = [
        r"^\d+[\.\)]\s+",
        r"^[Qq]\.?\s*\d+[\.\)]?\s+",
        r"^[Qq]uestion\s+\d+",
    ]

    return any(
        re.match(pattern, line)
        for pattern in patterns
    )


def extract_exam_questions(
    file_path: str
) -> list[dict]:

    pages = extract_text_from_pdf(
        file_path
    )

    questions = []

    current_question = []
    current_page = None

    for page in pages:

        page_number = page["page_number"]

        for raw_line in page["text"].splitlines():

            line = raw_line.strip()

            if not line:
                continue

            if is_question_start(line):

                if current_question:
                    question_text = clean_question_text(
                        " ".join(current_question)
                    )

                    if len(question_text) >= 10:
                        questions.append({
                            "question": question_text,
                            "page_number": current_page
                        })

                current_question = [line]
                current_page = page_number

            elif current_question:

                current_question.append(line)

    if current_question:

        question_text = clean_question_text(
            " ".join(current_question)
        )

        if len(question_text) >= 10:
            questions.append({
                "question": question_text,
                "page_number": current_page
            })

    if questions:
        return questions
    return []