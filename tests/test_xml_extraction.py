import sys
from pathlib import Path

from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.parser import _extract_text as extract_pubmed_text
from app.validation import _extract_text as extract_pmc_text


def test_pubmed_extraction_preserves_inline_word_boundaries():
    element = etree.fromstring(
        b"<title>medical <i>imaging</i> datasets</title>"
    )

    assert extract_pubmed_text(element) == "medical imaging datasets"


def test_pmc_extraction_preserves_inline_word_boundaries():
    element = etree.fromstring(
        b"<title>medical <italic>imaging</italic> datasets</title>"
    )

    assert extract_pmc_text(element) == "medical imaging datasets"


def test_extraction_preserves_punctuation_and_abbreviations():
    element = etree.fromstring(
        b"<title>Machine learning (ML) for lung cancer</title>"
    )

    expected = "Machine learning (ML) for lung cancer"

    assert extract_pubmed_text(element) == expected
    assert extract_pmc_text(element) == expected