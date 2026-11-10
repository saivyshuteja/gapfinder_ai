import contextlib
import json
import re
import sys

import fitz
import numpy as np
from rapidocr_onnxruntime import RapidOCR


def needs_ocr(text: str) -> bool:
    without_urls = re.sub(r"(?:https?://|www\.)\S+", "", text, flags=re.IGNORECASE)
    return len(re.sub(r"[^A-Za-z0-9]", "", without_urls)) < 100


def main() -> None:
    with contextlib.redirect_stdout(sys.stderr):
        engine = RapidOCR()
        document = fitz.open(sys.argv[1])
        pages = []
        for page in document:
            text = page.get_text("text")
            if needs_ocr(text):
                pixmap = page.get_pixmap(dpi=120, alpha=False)
                image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                    pixmap.height,
                    pixmap.width,
                    pixmap.n,
                )
                result, _ = engine(image)
                text = "\n".join(
                    line[1]
                    for line in result or []
                    if len(line) > 1 and line[1].strip()
                ) or text
            pages.append({"text": text})
        document.close()

    print(json.dumps(pages))


if __name__ == "__main__":
    main()