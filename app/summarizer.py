"""Section-aware summarization for scientific articles."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langfuse import get_client

langfuse = get_client()

from app.llm_client import MODEL, generate_response
from app.preprocessing import load_article, prepare_section_chunks


CHUNK_SYSTEM_PROMPT = """
You are an expert scientific research summarizer.
Summarize only the supplied source text.
Preserve important methods, findings, numerical results, and limitations.
Do not invent facts, citations, or conclusions.
Clearly distinguish reported findings from speculation.
Write concise, information-dense prose.
"""

FINAL_SYSTEM_PROMPT = """
You are an expert scientific editor.
Produce a coherent summary of a scientific research article using
only the supplied article metadata, abstract, and section summaries.
Preserve important findings, methods, numerical results, and limitations.
Do not invent evidence or claim that a result is clinically validated
unless the supplied material supports that statement.
Avoid repetition and distinguish evidence from speculation.
"""


def _summarize_article_data_impl(
    article: dict[str, Any],
    max_words: int = 1200,
    generate_fn: Callable[..., str] = generate_response,
) -> dict[str, Any]:
    """Summarize an article using chunk summaries and final synthesis."""
    chunks = prepare_section_chunks(article, max_words=max_words)
    print(f"Prepared {len(chunks)} chunks for summarization.", flush=True)

    if not chunks:
        raise ValueError("No substantive text chunks to summarize")

    chunk_summaries = []

    for index, chunk in enumerate(chunks, start=1):
        prompt = f"""
Article title: {article["title"]}
Section: {chunk["section_heading"]}
Chunk: {chunk["chunk_index"] + 1}

Summarize this portion of the article in approximately 100–180 words.
Preserve specific findings and numerical details when present.
If the passage describes background rather than results, retain that distinction.

SOURCE TEXT:
{chunk["text"]}
"""

        summary = generate_fn(
            prompt,
            system_prompt=CHUNK_SYSTEM_PROMPT,
            max_tokens=450,
        )
        
        print(
            f"Summarizing chunk {index}/{len(chunks)}: "
            f"{chunk['section_heading']}",
            flush=True,
        )

        chunk_summaries.append(
            {
                "chunk_number": index,
                "section_heading": chunk["section_heading"],
                "summary": summary,
            }
        )

    summaries_text = "\n\n".join(
        f"Section: {item['section_heading']}\n{item['summary']}"
        for item in chunk_summaries
    )

    final_prompt = f"""
Write a structured scientific article summary.

TITLE:
{article["title"]}

ABSTRACT:
{article.get("abstract", "")}

INTERMEDIATE SECTION SUMMARIES:
{summaries_text}

Use these headings:
1. Research objective
2. Methods and data
3. Key findings
4. Limitations and caveats
5. Overall conclusion

If a heading is not supported by the supplied material, say so briefly.
Do not invent numerical results, methods, limitations, or citations.
Avoid repeating the abstract verbatim.
"""
    print("Generating the final article summary...", flush=True)
    final_summary = generate_fn(
        final_prompt,
        system_prompt=FINAL_SYSTEM_PROMPT,
        max_tokens=1000,
    )

    return {
        "pmcid": article["pmcid"],
        "pmid": article.get("pmid"),
        "title": article["title"],
        "model": MODEL,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "chunk_count": len(chunks),
        "chunk_summaries": chunk_summaries,
        "final_summary": final_summary,
    }


def summarize_article_data(
    article: dict[str, Any],
    max_words: int = 1200,
    generate_fn: Callable[..., str] = generate_response,
) -> dict[str, Any]:
    """Summarize an article and trace the complete pipeline."""

    with langfuse.start_as_current_observation(
        as_type="span",
        name="scientific-article-summarization",
        input={
            "pmcid": article.get("pmcid"),
            "pmid": article.get("pmid"),
            "title": article.get("title"),
        },
        metadata={
            "configured_model": MODEL,
            "max_words": max_words,
        },
    ) as trace:
        result = _summarize_article_data_impl(
            article,
            max_words=max_words,
            generate_fn=generate_fn,
        )

        trace.update(
            output={
                "pmcid": result["pmcid"],
                "chunk_count": result["chunk_count"],
                "final_summary": result["final_summary"],
            },
            metadata={
                "model": result["model"],
                "chunk_count": result["chunk_count"],
            },
        )

        return result

def summarize_article_file(
    json_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Load, summarize, and save one article."""
    article = load_article(json_path)
    result = summarize_article_data(article)

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return result