"""Evaluate scientific article summaries against abstract-reference proxies."""

import argparse
import json
from pathlib import Path

import pandas as pd
from rouge_score import rouge_scorer

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "selected_articles.json"
OUTPUT_DIR = ROOT / "outputs" / "evaluation"

MODEL_NAMES = {
    "phi": "phi4-mini",
    "qwen": "qwen2.5-3b",
}


def read_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def canonical_model(data, path):
    value = str(data.get("model", "")).lower()
    filename = path.name.lower()
    text = f"{value} {filename}"

    if "phi4-mini" in text or "phi-4-mini" in text:
        return MODEL_NAMES["phi"]
    if "qwen2.5:3b" in text or "qwen2.5-3b" in text:
        return MODEL_NAMES["qwen"]
    return None


def candidate_priority(path, model):
    """Prefer controlled batch outputs over exploratory/UI outputs."""
    name = path.name.lower()
    parent_parts = {part.lower() for part in path.parts}

    # Controlled same-input model-comparison outputs take precedence.
    if "batch" in parent_parts:
        return 100

    # Exploratory variants are fallbacks, not the primary comparison.
    if any(marker in name for marker in ("prompt-v2", "langfuse", "smoke")):
        return 10

    return 20


def load_best_summaries(pmcid):
    """Load one usable summary per model, preferring controlled batch outputs."""
    matches = []

    # Batch filenames such as PMC10025752_phi4-mini.json do not contain
    # the word "summary", so search every JSON filename matching the PMCID.
    for path in (ROOT / "outputs").rglob(f"*{pmcid}*.json"):
        if OUTPUT_DIR in path.parents:
            continue

        try:
            data = read_json(path)
        except (OSError, json.JSONDecodeError):
            continue

        summary = data.get("final_summary")
        if not isinstance(summary, str) or not summary.strip():
            continue

        model = canonical_model(data, path)
        if model is None:
            continue

        matches.append({
            "model": model,
            "path": path,
            "data": data,
            "summary": summary.strip(),
            "priority": candidate_priority(path, model),
        })

    best = {}
    for item in matches:
        model = item["model"]
        previous = best.get(model)
        if previous is None or item["priority"] > previous["priority"]:
            best[model] = item

    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-bertscore",
        action="store_true",
        help="Run ROUGE first without loading a BERTScore model.",
    )
    args = parser.parse_args()

    selected = read_json(MANIFEST)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=True,
    )

    rows = []
    missing = []
    bert_candidates = []

    for article in selected:
        pmcid = article["pmcid"]
        article_path = ROOT / article["json_path"]

        if not article_path.exists():
            missing.append({
                "pmcid": pmcid,
                "model": "ALL",
                "reason": f"Article file not found: {article_path}",
            })
            continue

        source = read_json(article_path)
        reference = str(source.get("abstract") or "").strip()

        if not reference:
            missing.append({
                "pmcid": pmcid,
                "model": "ALL",
                "reason": "Abstract reference unavailable",
            })
            continue

        summaries = load_best_summaries(pmcid)

        for model in MODEL_NAMES.values():
            item = summaries.get(model)

            if item is None:
                missing.append({
                    "pmcid": pmcid,
                    "model": model,
                    "reason": "No usable final summary found",
                })
                continue

            prediction = item["summary"]
            scores = scorer.score(reference, prediction)

            row = {
                "pmcid": pmcid,
                "pmid": article.get("pmid"),
                "title": article.get("title"),
                "model": model,
                "summary_file": str(item["path"].relative_to(ROOT)),
                "reference_type": "article_abstract_proxy",
                "reference_words": len(reference.split()),
                "summary_words": len(prediction.split()),
                "rouge1_precision": scores["rouge1"].precision,
                "rouge1_recall": scores["rouge1"].recall,
                "rouge1_f1": scores["rouge1"].fmeasure,
                "rouge2_f1": scores["rouge2"].fmeasure,
                "rougeL_f1": scores["rougeL"].fmeasure,
                # Do not infer latency from created_at timestamps.
                "latency_seconds": None,
                "bertscore_precision": None,
                "bertscore_recall": None,
                "bertscore_f1": None,
            }
            rows.append(row)
            bert_candidates.append({
                "row": row,
                "reference": reference,
                "prediction": prediction,
            })

    # Batch BERTScore calls to avoid loading its model for each document.
    if not args.skip_bertscore and bert_candidates:
        try:
            from bert_score import score as bert_score

            predictions = [item["prediction"] for item in bert_candidates]
            references = [item["reference"] for item in bert_candidates]
            precision, recall, f1 = bert_score(
                predictions,
                references,
                model_type="distilbert-base-uncased",
                lang="en",
                batch_size=4,
                device="cpu",
                verbose=False,
            )

            for index, item in enumerate(bert_candidates):
                item["row"]["bertscore_precision"] = float(precision[index])
                item["row"]["bertscore_recall"] = float(recall[index])
                item["row"]["bertscore_f1"] = float(f1[index])

        except Exception as exc:
            print(f"WARNING: BERTScore could not run: {exc}")
            print("ROUGE results will still be saved.")

    per_article_path = OUTPUT_DIR / "per_article_metrics.csv"
    comparison_path = OUTPUT_DIR / "model_comparison.csv"
    missing_path = OUTPUT_DIR / "missing_summaries.csv"
    summary_path = OUTPUT_DIR / "evaluation_summary.json"

    df = pd.DataFrame(rows)
    df.to_csv(per_article_path, index=False)

    if not df.empty:
        metric_columns = [
            "rouge1_precision",
            "rouge1_recall",
            "rouge1_f1",
            "rouge2_f1",
            "rougeL_f1",
            "bertscore_precision",
            "bertscore_recall",
            "bertscore_f1",
            "summary_words",
        ]
        comparison = df.groupby("model")[metric_columns].agg(
            ["mean", "median", "std", "count"]
        )
        comparison.columns = [
            f"{metric}_{stat}" for metric, stat in comparison.columns
        ]
        comparison.reset_index().to_csv(comparison_path, index=False)
    else:
        pd.DataFrame(columns=["model"]).to_csv(comparison_path, index=False)

    pd.DataFrame(
        missing,
        columns=["pmcid", "model", "reason"],
    ).to_csv(missing_path, index=False)

    paired_counts = (
        df.groupby("pmcid")["model"].nunique()
        if not df.empty else pd.Series(dtype=int)
    )

    report = {
        "selected_articles": len(selected),
        "unique_articles_evaluated": int(df["pmcid"].nunique())
        if not df.empty else 0,
        "summary_model_pairs_evaluated": len(df),
        "articles_with_both_models": int((paired_counts == 2).sum()),
        "phi4_mini_summaries": int(
            (df["model"] == MODEL_NAMES["phi"]).sum()
        ) if not df.empty else 0,
        "qwen2_5_3b_summaries": int(
            (df["model"] == MODEL_NAMES["qwen"]).sum()
        ) if not df.empty else 0,
        "missing_model_outputs": len(missing),
        "reference_method": (
            "Article abstract used as a proxy reference; "
            "not a human-authored gold summary of the full article."
        ),
        "latency_note": (
            "Latency is not populated by this evaluator. "
            "Use recorded inference timings or rerun with timing instrumentation."
        ),
        "bertscore_model": "distilbert-base-uncased",
        "bertscore_requested": not args.skip_bertscore,
        "metrics": [
            "ROUGE-1 precision/recall/F1",
            "ROUGE-2 F1",
            "ROUGE-L F1",
            "BERTScore precision/recall/F1 when available",
        ],
    }

    summary_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print("\nSaved evaluation files:")
    print(per_article_path)
    print(comparison_path)
    print(missing_path)
    print(summary_path)


if __name__ == "__main__":
    main()
