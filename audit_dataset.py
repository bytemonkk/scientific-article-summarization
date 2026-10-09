import csv
import json
import re
from pathlib import Path


DATASET_DIR = Path("data/articles")
REPORT_PATH = Path("data/dataset_audit.csv")

DISEASE_TERMS = re.compile(
    r"\blung cancer\b"
    r"|\blung carcinoma\b"
    r"|\bpulmonary\b"
    r"|\bnon[- ]small[- ]cell lung\b"
    r"|\bsmall[- ]cell lung\b"
    r"|\bNSCLC\b"
    r"|\bSCLC\b"
    r"|\blung nodule\b"
    r"|\blung adenocarcinoma\b"
    r"|\blung tumor\b"
    r"|\blung tumour\b"
    r"|\bthoracic oncology\b",
    re.IGNORECASE,
)

METHOD_TERMS = re.compile(
    r"\bmachine learning\b"
    r"|\bdeep learning\b"
    r"|\bartificial intelligence\b"
    r"|\bradiomics\b"
    r"|\bneural network\b"
    r"|\bcomputer[- ]aided\b"
    r"|\bautomated classification\b"
    r"|\bimage analysis\b"
    r"|\bhistopatholog\w*\b"
    r"|\bcomputer vision\b"
    r"|\bpredictive model\w*\b"
    r"|\bAI\b",
    re.IGNORECASE,
)


def audit_article(path: Path) -> dict:
    """Inspect one saved article without modifying it."""

    article = json.loads(path.read_text(encoding="utf-8"))

    title = article.get("title") or ""
    abstract = article.get("abstract") or ""

    # Use title and abstract for initial screening.
    searchable_text = f"{title}\n{abstract}"

    disease_match = bool(DISEASE_TERMS.search(searchable_text))
    method_match = bool(METHOD_TERMS.search(searchable_text))

    if disease_match and method_match:
        recommendation = "KEEP_CANDIDATE"
    elif disease_match or method_match:
        recommendation = "REVIEW"
    else:
        recommendation = "LIKELY_OUT_OF_SCOPE"

    validation = article.get("validation", {})
    sections = article.get("sections", [])

    return {
        "file": path.name,
        "pmid": article.get("pmid") or "",
        "pmcid": article.get("pmcid") or "",
        "title": title,
        "journal": article.get("journal") or "",
        "publication_year": article.get("publication_year") or "",
        "abstract_characters": len(abstract),
        "section_count": len(sections),
        "body_characters": validation.get("body_characters", 0),
        "validation_passed": validation.get("passed", False),
        "disease_match": disease_match,
        "ai_ml_match": method_match,
        "recommendation": recommendation,
    }


def main():
    if not DATASET_DIR.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {DATASET_DIR}"
        )

    article_files = sorted(DATASET_DIR.glob("PMC*.json"))

    if not article_files:
        print("No article JSON files found.")
        return

    results = []
    errors = []

    for path in article_files:
        try:
            results.append(audit_article(path))
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            errors.append((path.name, str(exc)))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if results:
        with REPORT_PATH.open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=list(results[0].keys())
            )
            writer.writeheader()
            writer.writerows(results)

    counts = {
        status: sum(
            row["recommendation"] == status for row in results
        )
        for status in (
            "KEEP_CANDIDATE",
            "REVIEW",
            "LIKELY_OUT_OF_SCOPE",
        )
    }

    print("=" * 65)
    print("DATASET QUALITY AUDIT")
    print("=" * 65)
    print(f"Article files discovered: {len(article_files)}")
    print(f"Successfully audited:     {len(results)}")
    print(f"Audit errors:             {len(errors)}")
    print(f"Keep candidates:          {counts['KEEP_CANDIDATE']}")
    print(f"Needs review:             {counts['REVIEW']}")
    print(f"Likely out of scope:      {counts['LIKELY_OUT_OF_SCOPE']}")
    print(f"Report saved to:          {REPORT_PATH}")

    print("\nArticles requiring attention:")

    for row in results:
        if row["recommendation"] != "KEEP_CANDIDATE":
            print(
                f"- {row['pmcid']}: {row['recommendation']} | "
                f"{row['title']}"
            )

    if errors:
        print("\nFiles that could not be audited:")

        for filename, message in errors:
            print(f"- {filename}: {message}")


if __name__ == "__main__":
    main()