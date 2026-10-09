## PubMed Central Ingestion and Article Validation

Implemented an initial ingestion pipeline for retrieving full-text scientific articles from PubMed Central and converting them into structured JSON records.

### Features
- Fetches full-text articles in JATS XML format.
- Extracts article metadata, including PMID, PMCID, title, journal, and publication year where available.
- Extracts abstracts and substantive body sections.
- Filters selected non-research sections.
- Validates article eligibility using title, abstract length, section count, and body-text length.
- Saves validated articles as UTF-8 JSON files under `data/articles/`.

### Validation Criteria
- Non-empty article title.
- Abstract containing at least 200 characters.
- At least two substantive body sections.
- At least 1,000 characters of extracted body text.

### Initial Validation Result

Successfully validated and saved the following article:

- **Title:** Machine Learning for Lung Cancer Diagnosis, Treatment, and Prognosis
- **PMID:** 36462630
- **PMCID:** PMC10025752
- **Journal:** Genomics, Proteomics & Bioinformatics
- **Publication year:** 2022
- **Substantive sections:** 17
- **Extracted body text:** 53,785 characters

This is an initial ingestion milestone, not yet a finalized evaluation dataset. Batch ingestion, duplicate handling, and further content-quality checks remain future work.
