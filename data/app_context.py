from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def load_app_context(pdf_path: str) -> str:
    if not pdf_path or not os.path.exists(pdf_path):
        return ""

    try:
        from pypdf import PdfReader
    except Exception:
        return ""

    try:
        reader = PdfReader(pdf_path)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        text = "\n".join(pages).strip()
        return text[:8000]
    except Exception:
        return ""
