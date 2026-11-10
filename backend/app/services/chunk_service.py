import re
from typing import List, Dict


# Repeated headers/footers from the PDF
IGNORED_LINES = {
    "MRCET",
    "PYTHON PROGRAMMING",
    "III YEAR/II SEM",
}


def clean_line(line: str) -> str:
    """
    Clean one extracted PDF line.
    """

    line = line.strip()

    if not line:
        return ""

    # Normalize multiple spaces
    line = re.sub(r"\s+", " ", line)

    return line


def clean_text(text: str) -> str:
    """
    Clean complete page text.
    """

    cleaned_lines = []

    for raw_line in text.splitlines():

        line = clean_line(raw_line)

        if not line:
            continue

        # Remove repeated PDF headers
        if line.upper() in IGNORED_LINES:
            continue

        # Ignore standalone page numbers
        if line.isdigit():
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def is_unit_heading(line: str) -> bool:
    """
    Detect headings such as:

    UNIT I
    UNIT II
    UNIT III
    UNIT IV
    UNIT V
    """

    normalized = re.sub(r"[\u2012-\u2015]", "-", line.upper()).strip()
    return bool(re.fullmatch(r"UNIT\s*[-:]?\s*(?:[IVXLCDM]+|\d+)(?:\s*[:.]\s*.*)?", normalized))


def is_real_topic_heading(line: str) -> bool:
    """
    Detect actual section/topic headings.

    We deliberately make this conservative.
    """

    upper = line.upper()

    # Known non-topic text
    if upper in IGNORED_LINES:
        return False

    # Empty / very long lines
    if len(line) < 4 or len(line) > 100:
        return False

    # Page numbers
    if line.isdigit():
        return False

    if re.match(r"^(?:step\s+\d+|column\s+\d+|row\s+\d+|cell\s+\d+)\b", line, re.IGNORECASE):
        return False

    if re.fullmatch(r"(?:because|comments?|entity|character|meaning|syntax|description)", line, re.IGNORECASE):
        return False

    if re.search(r"(?:https?://|www\.)|[<>]", line, re.IGNORECASE):
        return False

    if re.search(r"[=`\";]|&&|\|\||\bOP\d+\b", line, re.IGNORECASE):
        return False

    if re.match(r"^(?:top|bottom)\s+of\s+form\b", line, re.IGNORECASE) or line.endswith("*"):
        return False

    if line.count(",") >= 2:
        return False

    # Code-like content
    code_patterns = [
        ">>>",
        "import ",
        "from ",
        "print(",
        "def ",
        "class ",
        "if ",
        "for ",
        "while ",
        "return ",
        "input(",
    ]

    if any(
        line.lower().startswith(pattern)
        for pattern in code_patterns
    ):
        return False

    # Bullets are generally content, not headings
    if line.startswith(
        ("•", "-", "*", "#")
    ):
        return False

    words = re.findall(r"[A-Za-z][A-Za-z'-]*", line)
    if len(words) > 8 or line.endswith((".", ":", ";", ",")):
        return False

    if len(words) >= 4 and re.search(
        r"\b(?:is|are|was|were|will|would|should|provides|providing|used|uses|means|when|which|that)\b",
        line,
        re.IGNORECASE,
    ) and not re.match(r"^what\s+is\b", line, re.IGNORECASE):
        return False

    # Calculate uppercase ratio
    letters = [
        char
        for char in line
        if char.isalpha()
    ]

    if not letters:
        return False

    uppercase_count = sum(
        char.isupper()
        for char in letters
    )

    uppercase_ratio = (
        uppercase_count /
        len(letters)
    )

    title_case_ratio = (
        sum(word[0].isupper() for word in words) / len(words)
        if words and 2 <= len(words) <= 8
        else 0
    )

    return uppercase_ratio >= 0.80 or title_case_ratio >= 0.65


def create_heading_chunks(
    pages: List[Dict],
    max_chunk_size: int = 1500
) -> List[Dict]:
    """
    Create chunks while preserving:

    - document page
    - UNIT
    - topic
    - related content
    """

    chunks = []

    chunk_id = 1

    current_unit = None
    current_topic = None
    current_page = None

    current_lines = []

    def current_text() -> str:
        return "\n".join(
            current_lines
        ).strip()

    def save_chunk():

        nonlocal chunk_id
        nonlocal current_lines

        text = current_text()

        if not text:
            return

        chunks.append({
            "chunk_id": chunk_id,
            "page_number": current_page,
            "unit": current_unit,
            "topic": current_topic,
            "text": text,
        })

        chunk_id += 1
        current_lines = []

    for page in pages:

        page_number = page["page_number"]

        text = clean_text(
            page["text"]
        )

        if not text:
            continue

        lines = text.splitlines()

        for line in lines:

            # -------------------------
            # UNIT
            # -------------------------

            if is_unit_heading(line):

                save_chunk()

                current_unit = (
                    line.upper()
                )

                current_topic = None
                current_page = page_number

                current_lines.append(
                    line
                )

                continue

            # -------------------------
            # TOPIC
            # -------------------------

            if is_real_topic_heading(
                line
            ):

                # Don't immediately
                # split tiny fragments.
                if current_lines:

                    save_chunk()

                current_topic = line
                current_page = page_number

                current_lines.append(
                    line
                )

                continue

            # -------------------------
            # NORMAL CONTENT
            # -------------------------

            if current_page is None:

                current_page = (
                    page_number
                )

            if current_topic is None:
                current_topic = "General concepts"

            current_lines.append(
                line
            )

            # -------------------------
            # SIZE CONTROL
            # -------------------------

            if len(
                current_text()
            ) >= max_chunk_size:

                save_chunk()

    # Save remaining content
    save_chunk()

    return chunks