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

## Dataset Ingestion and Quality Control

### Objective

Build a reproducible dataset of full-text scientific articles focused on lung cancer and computational methods, suitable for evaluating scientific article summarization.

### Data Sources and Discovery

- **Source:** PubMed and PubMed Central (PMC).
- **Retrieval format:** JATS XML.
- **Search query:**

  ```text
  ("lung cancer"[Title/Abstract]) AND
  ("machine learning"[Title/Abstract] OR
  "deep learning"[Title/Abstract]) AND
  "free full text"[Filter]
  ```

- PubMed discovers candidate publications.
- PubMed-to-PMC links identify articles with available PMC full text.
- XML extraction produces structured JSON records containing article metadata, abstracts, and body sections.

### Article Eligibility

An article passes the current structural validation when it has:

- A non-empty title.
- An abstract containing at least 200 characters.
- At least two substantive body sections.
- At least 1,000 characters of extracted body text.

Selected non-research sections, including acknowledgments, funding, conflicts of interest, and references when represented by matching section headings, are excluded from substantive section extraction.

These rules assess structural suitability; they do not independently establish scientific relevance or factual accuracy.

### Initial Ingestion Results

| Metric | Result |
|---|---:|
| PubMed candidates | 100 |
| Candidates linked to PMC | 95 |
| Candidates without a PMC link | 5 |
| Newly saved articles | 20 |
| Previously existing article files | 1 |
| Total article JSON files | 21 |

Five candidates were reported as rejected or failed during the ingestion run. The current ingestion report combines those outcomes, so they should not be interpreted as five confirmed validation rejections.

### Dataset Review and Selection

The initial keyword audit examined 21 article records. All matched at least one disease-related term and one AI/ML-related term in the title or abstract.

Manual review then produced the following provisional decisions:

| Decision | Articles |
|---|---:|
| KEEP | 16 |
| REVIEW | 4 |
| EXCLUDE | 1 |
| Total reviewed | 21 |

The selected manifest contains 16 unique PMCIDs. Borderline articles remain available for review, and the original article JSON files are preserved.

### Generated Artifacts

- `data/articles/`: original article JSON records.
- `data/article_review.csv`: article metadata and manual decisions.
- `data/dataset_audit.csv`: preliminary keyword-based screening results.
- `data/dataset_selection.csv`: selection decisions and selected status.
- `data/selected_articles.json`: manifest of selected articles.

### Limitations and Future Work

- Keyword matching can produce false positives and does not replace scientific review.
- Manual inclusion decisions should be checked against the article abstracts and research scope.
- Extracted XML text may contain figure captions, tables, mathematical markup, or other formatting noise.
- Metadata availability and XML structure vary between articles.
- The current collection is an initial dataset, not a representative sample of all lung cancer AI research.

Next steps include testing the ingestion and selection pipeline, improving extracted-text quality, and implementing section-aware summarization before comparing hosted language models.
