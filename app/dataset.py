import json
from pathlib import Path

from app.fulltext import fetch_pmc_xml
from app.validation import validate_pmc_xml


DATASET_DIR = Path("data/articles")


def save_article(pmc_id: str) -> Path:
    """
    Fetch, validate, and save a PubMed Central article as JSON.

    Args:
        pmc_id: PMC identifier without the 'PMC' prefix.

    Returns:
        Path to the saved JSON file.

    Raises:
        ValueError: If the article fails validation.
    """

    # 1. Fetch the full-text JATS XML
    xml_data = fetch_pmc_xml(pmc_id)

    # 2. Validate the XML and extract article information
    result = validate_pmc_xml(xml_data)

    if not result["passed"]:
        raise ValueError(
            f"PMC{pmc_id} failed validation; refusing to save."
        )

    # 3. Construct the article record
    article = {
        "pmid": result["pmid"],
        "pmcid": f"PMC{pmc_id}",
        "title": result["title"],
        "abstract": result["abstract"],
        "journal": result["journal"],
        "publication_year": result["publication_year"],
        "sections": result["sections"],
        "validation": {
            "passed": result["passed"],
            "section_count": result["section_count"],
            "body_characters": result["body_characters"],
            "checks": result["checks"],
        },
        "source": {
            "database": "PubMed Central",
            "format": "JATS XML",
        },
    }

    # 4. Create the output directory if necessary
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    # 5. Save the article as UTF-8 JSON
    output_path = DATASET_DIR / f"PMC{pmc_id}.json"

    output_path.write_text(
        json.dumps(article, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    pmc_id = "10025752"
    saved_path = save_article(pmc_id)
    print(f"Saved: {saved_path}")