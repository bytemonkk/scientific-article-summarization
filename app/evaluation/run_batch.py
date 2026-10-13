
"""Batch-generate summaries for the selected scientific articles."""

import json
import os
import time
import traceback
from pathlib import Path

# Disable Langfuse before importing the summarizer or LLM client.
os.environ["LANGFUSE_ENABLED"] = "false"

from app.summarizer import summarize_article_file

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "selected_articles.json"
OUTPUT_DIR = ROOT / "outputs" / "batch"
LOG_PATH = ROOT / "outputs" / "evaluation" / "batch_run_log.jsonl"

MODELS = ["phi4-mini", "qwen2.5:3b"]


def read_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_valid_summary(path, expected_model):
    if not path.exists():
        return False

    try:
        data = read_json(path)
    except (OSError, json.JSONDecodeError):
        return False

    summary = data.get("final_summary")
    actual_model = str(data.get("model", "")).lower()
    expected = expected_model.lower().replace(":", "-")

    return (
        isinstance(summary, str)
        and len(summary.strip()) > 100
        and (
            actual_model == expected
            or actual_model.replace(":", "-") == expected
        )
    )


def append_log(record):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    articles = read_json(MANIFEST)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    totals = {"completed": 0, "skipped": 0, "failed": 0}

    for model in MODELS:
        # llm_client.py reads OLLAMA_MODEL from the environment.
        os.environ["OLLAMA_MODEL"] = model
        print(f"\n{'=' * 65}\nMODEL: {model}\n{'=' * 65}")

        for index, article in enumerate(articles, start=1):
            pmcid = article["pmcid"]
            source_path = ROOT / article["json_path"]
            output_path = OUTPUT_DIR / f"{pmcid}_{model.replace(':', '-')}.json"

            print(f"\n[{index}/{len(articles)}] {pmcid}: {article['title']}")

            if is_valid_summary(output_path, model):
                print(f"SKIP: valid output already exists: {output_path.name}")
                totals["skipped"] += 1
                continue

            if not source_path.exists():
                message = f"Article source not found: {source_path}"
                print(f"FAIL: {message}")
                append_log({
                    "pmcid": pmcid,
                    "model": model,
                    "status": "failed",
                    "error": message,
                })
                totals["failed"] += 1
                continue

            start = time.perf_counter()

            try:
                result = summarize_article_file(
                    json_path=str(source_path),
                    output_path=str(output_path),
                )
                elapsed = time.perf_counter() - start

                record = {
                    "pmcid": pmcid,
                    "pmid": article.get("pmid"),
                    "title": article.get("title"),
                    "model_requested": model,
                    "model_reported": result.get("model"),
                    "status": "completed",
                    "elapsed_seconds": round(elapsed, 3),
                    "chunk_count": result.get("chunk_count"),
                    "output_path": str(output_path.relative_to(ROOT)),
                }
                append_log(record)
                totals["completed"] += 1

                print(
                    f"OK: {elapsed:.1f}s | "
                    f"{result.get('chunk_count')} chunks | "
                    f"{output_path.name}"
                )

            except Exception as exc:
                elapsed = time.perf_counter() - start
                record = {
                    "pmcid": pmcid,
                    "model": model,
                    "status": "failed",
                    "elapsed_seconds": round(elapsed, 3),
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                }
                append_log(record)
                totals["failed"] += 1
                print(f"FAIL after {elapsed:.1f}s: {exc}")
                print("Continuing to the next article.")

    os.environ.pop("OLLAMA_MODEL", None)

    print("\nBATCH RUN TOTALS")
    print(json.dumps(totals, indent=2))
    print(f"Run log: {LOG_PATH}")
    print(f"Summary output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()