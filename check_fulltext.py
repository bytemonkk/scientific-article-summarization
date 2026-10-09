from Bio import Entrez

from app.fulltext import find_pmc_ids

Entrez.email = "spideymail.4.71@gmail.com"

pmids = [
    "36905928",
    "39342281",
    "38636146",
]

results = find_pmc_ids(pmids)

for pmid, pmc_id in results.items():
    if pmc_id:
        print(f"PMID: {pmid} | PMCID: PMC{pmc_id}")
    else:
        print(f"PMID: {pmid} | No PMC link found")
