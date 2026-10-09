import csv
import json

import pytest

import sys
from pathlib import Path

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import select_dataset as selector

def create_review_csv(path, rows):
    fieldnames = ["PMCID", "ManualDecision"]

    with path.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_article(dataset_dir, pmcid, passed=True):
    dataset_dir.mkdir(parents=True, exist_ok=True)

    article = {
        "pmcid": pmcid,
        "pmid": "12345678",
        "title": f"Test article {pmcid}",
        "journal": "Test Journal",
        "publication_year": 2025,
        "validation": {
            "passed": passed,
            "section_count": 3,
            "body_characters": 2000,
        },
    }

    path = dataset_dir / f"{pmcid}.json"
    path.write_text(
        json.dumps(article),
        encoding="utf-8",
    )


@pytest.fixture
def project_paths(tmp_path, monkeypatch):
    dataset_dir = tmp_path / "articles"
    review_csv = tmp_path / "article_review.csv"
    selection_csv = tmp_path / "dataset_selection.csv"
    manifest_json = tmp_path / "selected_articles.json"

    monkeypatch.setattr(selector, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(selector, "REVIEW_CSV", review_csv)
    monkeypatch.setattr(selector, "SELECTION_CSV", selection_csv)
    monkeypatch.setattr(selector, "MANIFEST_JSON", manifest_json)

    return {
        "dataset": dataset_dir,
        "review": review_csv,
        "selection": selection_csv,
        "manifest": manifest_json,
    }


def test_selects_only_keep_articles(project_paths):
    paths = project_paths

    create_review_csv(paths["review"], [
        {"PMCID": "PMC1000001", "ManualDecision": "KEEP"},
        {"PMCID": "PMC1000002", "ManualDecision": "REVIEW"},
        {"PMCID": "PMC1000003", "ManualDecision": "EXCLUDE"},
    ])

    for pmcid in ("PMC1000001", "PMC1000002", "PMC1000003"):
        create_article(paths["dataset"], pmcid)

    selector.main()

    manifest = json.loads(
        paths["manifest"].read_text(encoding="utf-8")
    )

    assert len(manifest) == 1
    assert manifest[0]["pmcid"] == "PMC1000001"

    with paths["selection"].open(
        newline="", encoding="utf-8-sig"
    ) as file:
        selection_rows = list(csv.DictReader(file))

    assert len(selection_rows) == 3
    assert sum(row["Selected"] == "True" for row in selection_rows) == 1


def test_undecided_article_defaults_to_review(project_paths):
    paths = project_paths

    create_review_csv(paths["review"], [
        {"PMCID": "PMC9990001", "ManualDecision": ""},
    ])

    rows = selector.load_review_rows()

    assert rows[0]["ManualDecision"] == "REVIEW"


def test_invalid_decision_is_rejected(project_paths):
    paths = project_paths

    create_review_csv(paths["review"], [
        {"PMCID": "PMC1000001", "ManualDecision": "MAYBE"},
    ])

    with pytest.raises(ValueError, match="Invalid decision"):
        selector.load_review_rows()


def test_duplicate_pmcid_is_rejected(project_paths):
    paths = project_paths

    create_review_csv(paths["review"], [
        {"PMCID": "PMC1000001", "ManualDecision": "KEEP"},
        {"PMCID": "PMC1000001", "ManualDecision": "KEEP"},
    ])

    create_article(paths["dataset"], "PMC1000001")

    with pytest.raises(ValueError, match="Duplicate PMCID"):
        selector.main()


def test_unvalidated_article_is_rejected(project_paths):
    paths = project_paths

    create_review_csv(paths["review"], [
        {"PMCID": "PMC1000001", "ManualDecision": "KEEP"},
    ])

    create_article(
        paths["dataset"],
        "PMC1000001",
        passed=False,
    )

    with pytest.raises(ValueError, match="has not passed"):
        selector.main()