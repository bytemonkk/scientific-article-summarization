from Bio import Entrez


def find_pmc_ids(pmids: list[str]) -> dict[str, str | None]:
    """Map PubMed IDs to available PMC IDs."""
    if not pmids:
        return {}

    handle = Entrez.elink(
        dbfrom="pubmed",
        db="pmc",
        id=pmids,
        linkname="pubmed_pmc",
    )

    records = Entrez.read(handle)
    handle.close()

    results = {pmid: None for pmid in pmids}

    for record in records:
        pubmed_ids = record.get("IdList", [])
        links = record.get("LinkSetDb", [])

        if not pubmed_ids or not links:
            continue

        pmid = str(pubmed_ids[0])

        for link_group in links:
            if link_group.get("LinkName") == "pubmed_pmc":
                linked_ids = link_group.get("Link", [])

                if linked_ids:
                    results[pmid] = str(linked_ids[0]["Id"])
                    break

    return results


def fetch_pmc_xml(pmc_id: str) -> bytes:
    """Fetch full-text XML for an eligible PMC article."""
    handle = Entrez.efetch(
        db="pmc",
        id=pmc_id,
        rettype="full",
        retmode="xml",
    )

    try:
        return handle.read()
    finally:
        handle.close()
