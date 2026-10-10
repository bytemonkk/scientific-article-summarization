"""Preprocessing utilities for scientific article summarization."""

import json
import re
from pathlib import Path
from typing import Any


EXCLUDED_HEADINGS = {
    "acknowledgments",
    "acknowledgements",
    "author contributions",
    "author contribution",
    "conflict of interest",
    "conflicts of interest",
    "competing interests",
    "funding",
    "references",
    "bibliography",
    "supplementary materials",
    "supplementary material",
    "data availability",
    "availability of data and materials",
    "credit author statement",
}


def normalize_text(text: str) -> str:
    """Normalize whitespace without changing the scientific content."""
    return re.sub(r"\s+", " ", text).strip()


def is_substantive_section(section: dict[str, Any]) -> bool:
    """Return whether a section contains substantive article content."""
    heading = normalize_text(str(section.get("heading", ""))).lower()
    text = normalize_text(str(section.get("text", "")))

    if not text:
        return False

    if heading in EXCLUDED_HEADINGS:
        return False

    return True


def load_article(json_path: str | Path) -> dict[str, Any]:
    """Load an article JSON file and validate its basic structure."""
    path = Path(json_path)

    with path.open("r", encoding="utf-8") as file:
        article = json.load(file)

    required_fields = {"pmcid", "title", "abstract", "sections"}
    missing = required_fields - article.keys()

    if missing:
        raise ValueError(
            f"Article is missing required fields: {sorted(missing)}"
        )

    if not isinstance(article["sections"], list):
        raise ValueError("'sections' must be a list")

    return article


def prepare_article(article: dict[str, Any]) -> dict[str, Any]:
    """Prepare article metadata and substantive sections for summarization."""
    sections = []

    for index, section in enumerate(article["sections"]):
        if not isinstance(section, dict):
            raise ValueError(f"Section at index {index} must be a dictionary")

        if not is_substantive_section(section):
            continue

        sections.append(
            {
                "heading": normalize_text(
                    str(section.get("heading") or "Untitled section")
                ),
                "text": normalize_text(str(section["text"])),
            }
        )

    if not sections:
        raise ValueError("No substantive sections found in the article")

    return {
        "pmcid": article["pmcid"],
        "pmid": article.get("pmid"),
        "title": normalize_text(str(article["title"])),
        "abstract": normalize_text(str(article["abstract"])),
        "journal": article.get("journal"),
        "publication_year": article.get("publication_year"),
        "sections": sections,
    }


def split_text(text: str, max_words: int = 1200) -> list[str]:
    """Split text into word-bounded chunks while preserving all words."""
    if max_words < 1:
        raise ValueError("max_words must be at least 1")

    words = normalize_text(text).split()

    return [
        " ".join(words[start : start + max_words])
        for start in range(0, len(words), max_words)
    ]


def prepare_section_chunks(
    article: dict[str, Any], max_words: int = 1200
) -> list[dict[str, Any]]:
    """Split substantive sections into ordered, labeled chunks."""
    prepared = prepare_article(article)
    chunks = []

    for section_index, section in enumerate(prepared["sections"]):
        section_chunks = split_text(section["text"], max_words=max_words)

        for chunk_index, chunk_text in enumerate(section_chunks):
            chunks.append(
                {
                    "section_index": section_index,
                    "section_heading": section["heading"],
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                }
            )

    return chunks