import csv
import json
from pathlib import Path


DATASET_DIR = Path("data/articles")
REVIEW_CSV = Path("data/article_review.csv")
SELECTION_CSV = Path("data/dataset_selection.csv")
MANIFEST_JSON = Path("data/selected_articles.json")

# Initial decisions based on our previous abstract review.
# These are provisional and can be edited in article_review.csv.
INITIAL_DECISIONS = {
    "PMC11674357": "EXCLUDE",
    "PMC8709297": "REVIEW",
    "PMC9646838": "REVIEW",
    "PMC6879441": "REVIEW",
    "PMC7616143": "REVIEW",
}

ALLOWED_DECISIONS = {"KEEP", "REVIEW", "EXCLUDE"}


def load_review_rows():
    if not REVIEW_CSV.exists():
        raise FileNotFoundError(
            f"Review file not found: {REVIEW_CSV}"
        )

    with REVIEW_CSV.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows:
        raise ValueError("The review CSV contains no articles.")

    if "PMCID" not in fieldnames:
        raise ValueError("The review CSV must contain a PMCID column.")

    if "ManualDecision" not in fieldnames:
        fieldnames.append("ManualDecision")

    for row in rows:
        pmcid = (row.get("PMCID") or "").strip()

        if not pmcid:
            raise ValueError("An article has a missing PMCID.")

        decision = (
            row.get("ManualDecision") or ""
        ).strip().upper()

        if not decision:
            decision = INITIAL_DECISIONS.get(pmcid, "REVIEW")

        if decision not in ALLOWED_DECISIONS:
            raise ValueError(
                f"Invalid decision '{decision}' for {pmcid}. "
                f"Choose one of {sorted(ALLOWED_DECISIONS)}."
            )

        row["PMCID"] = pmcid
        row["ManualDecision"] = decision

    # Save the decisions so the selection can be reproduced.
    with REVIEW_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main():
    rows = load_review_rows()

    selected = []
    selection_rows = []
    seen_pmcids = set()

    for row in rows:
        pmcid = row["PMCID"]
        decision = row["ManualDecision"]
        article_path = DATASET_DIR / f"{pmcid}.json"

        if pmcid in seen_pmcids:
            raise ValueError(
                f"Duplicate PMCID in review CSV: {pmcid}"
            )
        seen_pmcids.add(pmcid)

        if not article_path.exists():
            raise FileNotFoundError(
                f"Article JSON not found: {article_path}"
            )

        article = json.loads(
            article_path.read_text(encoding="utf-8")
        )

        if not article.get("validation", {}).get("passed", False):
            raise ValueError(
                f"{pmcid} has not passed article validation."
            )

        is_selected = decision == "KEEP"

        selection_rows.append({
            "PMCID": pmcid,
            "PMID": article.get("pmid") or "",
            "Title": article.get("title") or "",
            "ManualDecision": decision,
            "Selected": is_selected,
            "JSONPath": str(article_path),
        })

        if is_selected:
            selected.append({
                "pmcid": pmcid,
                "pmid": article.get("pmid"),
                "title": article.get("title"),
                "journal": article.get("journal"),
                "publication_year": article.get(
                    "publication_year"
                ),
                "json_path": str(article_path),
            })

    SELECTION_CSV.parent.mkdir(
        parents=True, exist_ok=True
    )

    with SELECTION_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(selection_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(selection_rows)

    MANIFEST_JSON.write_text(
        json.dumps(selected, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts = {
        decision: sum(
            row["ManualDecision"] == decision for row in rows
        )
        for decision in sorted(ALLOWED_DECISIONS)
    }

    print("=" * 60)
    print("DATASET SELECTION SUMMARY")
    print("=" * 60)
    print(f"Articles reviewed: {len(rows)}")
    print(f"KEEP:              {counts['KEEP']}")
    print(f"REVIEW:            {counts['REVIEW']}")
    print(f"EXCLUDE:           {counts['EXCLUDE']}")
    print(f"Selected articles: {len(selected)}")
    print(f"Selection CSV:     {SELECTION_CSV}")
    print(f"Manifest JSON:     {MANIFEST_JSON}")
    print()
    print("Original article JSON files were not modified or deleted.")


if __name__ == "__main__":
    main()