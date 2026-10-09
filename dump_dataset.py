import os
from pathlib import Path

from Bio import Entrez

from app.fulltext import find_pmc_ids
from app.dataset import save_article


# --------------------------------------------------
# Configuration
# --------------------------------------------------

QUERY = (
    '("lung cancer"[Title/Abstract]) AND '
    '("machine learning"[Title/Abstract] OR '
    '"deep learning"[Title/Abstract]) AND '
    '"free full text"[Filter]'
)

TARGET_ARTICLES = 20
MAX_CANDIDATES = 100
DATASET_DIR = Path("data/articles")


def main():
    # --------------------------------------------------
    # 1. Configure NCBI Entrez
    # --------------------------------------------------

    email = os.getenv("NCBI_EMAIL")

    if not email:
        raise RuntimeError(
            "NCBI_EMAIL is not configured. "
            "Set it to your email address before running."
        )

    Entrez.email = email

    print("=" * 65)
    print("SCIENTIFIC ARTICLE BATCH INGESTION")
    print("=" * 65)
    print(f"Target eligible articles: {TARGET_ARTICLES}")
    print(f"Maximum PubMed candidates: {MAX_CANDIDATES}")
    print(f"Dataset directory: {DATASET_DIR}")
    print()

    # --------------------------------------------------
    # 2. Discover candidate PubMed articles
    # --------------------------------------------------

    print("[1/4] Searching PubMed...")

    handle = Entrez.esearch(
        db="pubmed",
        term=QUERY,
        retmax=MAX_CANDIDATES,
        sort="relevance",
    )

    try:
        search_results = Entrez.read(handle)
    finally:
        handle.close()

    pmids = [str(pmid) for pmid in search_results["IdList"]]

    print(f"PubMed candidates found: {len(pmids)}")

    if not pmids:
        print("No candidates found. Try broadening the search query.")
        return

    # --------------------------------------------------
    # 3. Find articles linked to PubMed Central
    # --------------------------------------------------

    print("\n[2/4] Discovering PMC full-text links...")

    pmc_mapping = find_pmc_ids(pmids)

    # Preserve candidate order and remove duplicate PMC IDs.
    pmc_ids = []
    seen_pmc_ids = set()
    no_full_text = 0

    for pmid in pmids:
        pmc_id = pmc_mapping.get(pmid)

        if not pmc_id:
            no_full_text += 1
            continue

        if pmc_id not in seen_pmc_ids:
            seen_pmc_ids.add(pmc_id)
            pmc_ids.append(pmc_id)

    print(f"PMC full-text candidates: {len(pmc_ids)}")
    print(f"No PMC link found: {no_full_text}")

    # --------------------------------------------------
    # 4. Validate and save eligible articles
    # --------------------------------------------------

    print("\n[3/4] Validating and saving articles...")

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    saved = 0
    skipped = 0
    failed = 0

    for index, pmc_id in enumerate(pmc_ids, start=1):
        if saved >= TARGET_ARTICLES:
            break

        output_path = DATASET_DIR / f"PMC{pmc_id}.json"

        # Do not overwrite an existing article.
        if output_path.exists():
            print(
                f"[{index}/{len(pmc_ids)}] "
                f"SKIP PMC{pmc_id}: already exists"
            )
            skipped += 1
            continue

        try:
            path = save_article(pmc_id)

            print(
                f"[{index}/{len(pmc_ids)}] "
                f"SAVED PMC{pmc_id}: {path}"
            )
            saved += 1

        except ValueError as exc:
            print(
                f"[{index}/{len(pmc_ids)}] "
                f"REJECTED PMC{pmc_id}: {exc}"
            )
            failed += 1

        except Exception as exc:
            print(
                f"[{index}/{len(pmc_ids)}] "
                f"ERROR PMC{pmc_id}: "
                f"{type(exc).__name__}: {exc}"
            )
            failed += 1

    # --------------------------------------------------
    # 5. Report results
    # --------------------------------------------------

    print("\n[4/4] Ingestion summary")
    print("=" * 65)
    print(f"PubMed candidates:       {len(pmids)}")
    print(f"PMC candidates:          {len(pmc_ids)}")
    print(f"Saved during this run:   {saved}")
    print(f"Already existed:         {skipped}")
    print(f"Rejected or failed:      {failed}")
    print(f"Target:                  {TARGET_ARTICLES}")
    print(f"Target reached:          {saved >= TARGET_ARTICLES}")
    print("=" * 65)


if __name__ == "__main__":
    main()