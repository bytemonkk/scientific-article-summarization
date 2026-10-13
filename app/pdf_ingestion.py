
"""Extract readable text from uploaded scientific PDFs."""

import re
from pathlib import Path

from pypdf import PdfReader


COMMON_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "literature review",
    "materials and methods",
    "methods",
    "methodology",
    "experimental setup",
    "results",
    "discussion",
    "results and discussion",
    "limitations",
    "conclusion",
    "conclusions",
    "acknowledgments",
    "acknowledgements",
}


def extract_pdf_article(
    pdf_path: str | Path,
    title: str | None = None,
) -> dict:
    """Convert a text-based scientific PDF into the existing article schema."""

    path = Path(pdf_path)
    reader = PdfReader(str(path))

    if reader.is_encrypted:
        try:
            unlocked = reader.decrypt("")
            if not unlocked:
                raise ValueError("This PDF is password-protected.")
        except Exception as exc:
            raise ValueError(
                "Cannot read this protected PDF. Upload an unlocked copy."
            ) from exc

    page_texts = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text(extraction_mode="layout") or ""
        except TypeError:
            # Compatibility with older pypdf releases.
            text = page.extract_text() or ""

        text = text.replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        if text:
            page_texts.append(text)

    full_text = "\n\n".join(page_texts).strip()

    if len(full_text) < 100:
        raise ValueError(
            "Very little readable text was extracted. This may be a scanned "
            "PDF; OCR is not enabled in this version."
        )

    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    detected_title = title.strip() if title and title.strip() else (
        lines[0][:300] if lines else path.stem
    )

    sections = []
    current_heading = "Article text"
    current_lines = []

    def save_section():
        text = "\n".join(current_lines).strip()
        if text:
            sections.append({
                "heading": current_heading,
                "text": text,
            })

    for line in lines:
        normalized = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", line)
        normalized = normalized.strip(" .:-").lower()

        is_heading = (
            normalized in COMMON_HEADINGS
            or (
                len(line) <= 90
                and len(line.split()) <= 10
                and line.isupper()
                and any(char.isalpha() for char in line)
            )
        )

        if is_heading and current_lines:
            save_section()
            current_heading = line[:200]
            current_lines = []
        elif is_heading:
            current_heading = line[:200]
        else:
            current_lines.append(line)

    save_section()

    if not sections:
        sections = [{"heading": "Full article", "text": full_text}]

    abstract = ""
    for section in sections:
        if section["heading"].strip().lower() == "abstract":
            abstract = section["text"]
            break

    # The existing summarizer expects these article fields.
    return {
        "pmid": "",
        "pmcid": path.stem,
        "title": detected_title,
        "abstract": abstract,
        "journal": "Uploaded document",
        "publication_year": None,
        "sections": sections,
    }
