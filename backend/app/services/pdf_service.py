import json
import re
import subprocess
import sys

import fitz

def needs_ocr(text: str) -> bool:
    without_urls = re.sub(r"(?:https?://|www\.)\S+", "", text, flags=re.IGNORECASE)
    return len(re.sub(r"[^A-Za-z0-9]", "", without_urls)) < 100


def extract_text_from_pdf(file_path: str):

    document = fitz.open(file_path)

    pages = [
        {"page_number": page_number + 1, "text": page.get_text("text")}
        for page_number, page in enumerate(document)
    ]
    should_ocr = any(needs_ocr(page["text"]) for page in pages)

    document.close()

    if should_ocr:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "app.services.ocr_worker", file_path],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError("OCR timed out while reading this scanned PDF.") from exc

        if result.returncode != 0:
            raise ValueError("OCR could not read this scanned PDF. Try a clearer scan.")
        try:
            payload_start = result.stdout.find("[")
            if payload_start < 0:
                raise json.JSONDecodeError("OCR JSON payload missing", result.stdout, 0)
            ocr_pages, _ = json.JSONDecoder().raw_decode(result.stdout[payload_start:])
        except json.JSONDecodeError as exc:
            raise ValueError("OCR returned invalid page data for this PDF.") from exc

        for page, ocr_page in zip(pages, ocr_pages):
            if needs_ocr(page["text"]):
                page["text"] = ocr_page.get("text", page["text"])

    return pages