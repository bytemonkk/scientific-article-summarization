from Bio import Entrez

from app.pubmed import PubMedClient
from app.fulltext import find_pmc_ids

Entrez.email = "spideymail.4.71@gmail.com"

client = PubMedClient(email=Entrez.email)

query = (
    '("machine learning"[Title/Abstract]) AND '
    '(diagnosis[Title/Abstract]) AND '
    '"free full text"[Filter]'
)

print(f"Searching PubMed: {query}")

pmids = client.search(query=query, max_results=15)
print(f"Candidate papers found: {len(pmids)}")

pmc_mapping = find_pmc_ids(pmids)

eligible = [
    (pmid, pmc_mapping[pmid])
    for pmid in pmids
    if pmc_mapping.get(pmid)
]

print(f"\nPapers with PMC links: {len(eligible)}")

for pmid, pmc_id in eligible:
    print(f"PMID: {pmid} | PMCID: PMC{pmc_id}")

print("\nSelect the first 3 eligible papers for full-text validation:")

for pmid, pmc_id in eligible[:3]:
    print(f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/")
