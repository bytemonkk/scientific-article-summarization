import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.preprocessing import (
    load_article,
    normalize_text,
    prepare_article,
    prepare_section_chunks,
    split_text,
)


def test_load_and_prepare_real_article():
    path = PROJECT_ROOT / "data" / "articles" / "PMC10025752.json"

    article = load_article(path)
    prepared = prepare_article(article)

    assert prepared["pmcid"] == "PMC10025752"
    assert prepared["title"]
    assert prepared["abstract"]
    assert prepared["sections"]
    assert all(section["text"] for section in prepared["sections"])


def test_excludes_references_and_funding():
    article = {
        "pmcid": "PMC123",
        "title": "Example",
        "abstract": "Example abstract.",
        "sections": [
            {"heading": "Introduction", "text": "Scientific content."},
            {"heading": "References", "text": "Reference content."},
            {"heading": "Funding", "text": "Funding content."},
        ],
    }

    prepared = prepare_article(article)
    headings = [section["heading"] for section in prepared["sections"]]

    assert headings == ["Introduction"]


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  Lung   cancer\nresearch  ") == (
        "Lung cancer research"
    )


def test_split_text_preserves_all_words():
    text = "one two three four five six seven"
    chunks = split_text(text, max_words=3)

    assert chunks == ["one two three", "four five six", "seven"]
    assert " ".join(chunks) == text


def test_split_text_rejects_invalid_limit():
    with pytest.raises(ValueError):
        split_text("some text", max_words=0)


def test_chunk_metadata_preserves_section_order():
    article = {
        "pmcid": "PMC123",
        "title": "Example",
        "abstract": "Example abstract.",
        "sections": [
            {"heading": "Introduction", "text": "one two three four"},
            {"heading": "Methods", "text": "five six seven"},
        ],
    }

    chunks = prepare_section_chunks(article, max_words=2)

    assert [chunk["section_heading"] for chunk in chunks] == [
        "Introduction",
        "Introduction",
        "Methods",
        "Methods",
    ]

    assert [chunk["text"] for chunk in chunks] == [
        "one two",
        "three four",
        "five six",
        "seven",
    ]