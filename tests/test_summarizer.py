
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.summarizer import summarize_article_data


def test_summarizer_uses_chunks_and_final_synthesis():
    article = {
        "pmcid": "PMC123",
        "pmid": "12345",
        "title": "Example Scientific Article",
        "abstract": "This study evaluates a hypothetical method.",
        "sections": [
            {
                "heading": "Introduction",
                "text": "The research addresses a scientific problem.",
            },
            {
                "heading": "Results",
                "text": "The proposed method improved the reported metric.",
            },
        ],
    }

    calls = []

    def fake_generate(prompt, system_prompt, max_tokens):
        calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
            }
        )
        return f"Test summary {len(calls)}"

    result = summarize_article_data(
        article,
        max_words=100,
        generate_fn=fake_generate,
    )

    assert result["pmcid"] == "PMC123"
    assert result["chunk_count"] == 2
    assert len(result["chunk_summaries"]) == 2
    assert len(calls) == 3
    assert result["final_summary"] == "Test summary 3"
    assert result["model"]



def test_summarizer_rejects_articles_without_substantive_sections():
    article = {
        "pmcid": "PMC123",
        "title": "Empty Article",
        "abstract": "Example abstract.",
        "sections": [
            {"heading": "References", "text": "Reference text."},
        ],
    }

    from app.preprocessing import prepare_article

    try:
        summarize_article_data(
            article,
            generate_fn=lambda *args, **kwargs: "",
        )
    except ValueError as exc:
        assert "No substantive sections found" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

