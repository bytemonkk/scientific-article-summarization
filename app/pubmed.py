from Bio import Entrez


class PubMedClient:
    def __init__(self, email: str):
        Entrez.email = email

    def search(self, query: str, max_results: int = 5) -> list[str]:
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results,
            sort="relevance",
        )

        record = Entrez.read(handle)
        handle.close()

        return record["IdList"]

    def fetch_articles(self, pmids: list[str]) -> bytes:
        if not pmids:
            raise ValueError("No PubMed IDs were provided.")

        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="xml",
            retmode="xml",
        )

        data = handle.read()
        handle.close()

        return data