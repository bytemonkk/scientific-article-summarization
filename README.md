# Scientific Article Summarization

A local-first scientific literature summarization application that retrieves research articles from PubMed and PubMed Central (PMC), processes article text using section-aware chunking, and generates summaries with locally hosted Ollama language models. The Streamlit interface supports a curated research library, live PubMed search, and PDF uploads.

# ACKNOWLEDGMENT

I would like to express my sincere gratitude to **D. NAGA JYOTHI, Assistant Professor, Chaitanya Bharathi Institute of Technology (CBIT)**, for her academic guidance and support. Her encouragement has been valuable throughout the development and experimentation undertaken for this project. I am grateful for the opportunity to carry out this work as part of my academic learning.


> **Project Status:** Working prototype with an initial curated dataset and preliminary model-evaluation results. The results are exploratory, not a definitive model ranking.

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Features](#features)
- [Architecture and Workflow](#architecture-and-workflow)
- [Technology Stack](#technology-stack)
- [Data Sources and Dataset](#data-sources-and-dataset)
- [Models](#models)
- [Evaluation Methodology](#evaluation-methodology)
- [Current Results](#current-results)
- [Installation and Setup](#installation-and-setup)
- [Project Structure](#project-structure)
- [Limitations](#limitations)
- [Future Work](#future-work)

## Overview

Scientific research papers contain detailed findings, methodologies, and conclusions that can take considerable time to review. This project aims to simplify literature exploration by generating concise, evidence-oriented summaries of scientific articles.

The system integrates PubMed for literature discovery, PubMed Central for available full-text articles, and Ollama for local language-model inference. It provides a user interface for searching research articles, summarizing curated publications, and processing uploaded PDFs.

The application is designed to operate without paid LLM API credits by using locally hosted models.

## Problem Statement

To develop a scientific article summarization system that retrieves relevant research publications and generates readable summaries while retaining the original article as the evidence source.

The main objectives are:

1. Retrieve relevant scientific publications from PubMed.
2. Obtain PMC full text when available and fall back to abstracts when necessary.
3. Process long articles using section-aware chunking.
4. Generate summaries using locally hosted language models.
5. Provide a simple interface for literature search, curated articles, and PDF uploads.
6. Evaluate generated summaries using quantitative metrics and document the limitations of the evaluation.

## Features

- **Curated Research Library:** Access the selected collection of scientific articles.
- **PubMed Search:** Search scientific publications using research topics or queries.
- **PMC Full-Text Retrieval:** Retrieve full-text XML for articles available through PMC.
- **Abstract Fallback:** Use available abstract content when full text cannot be retrieved.
- **PDF Upload:** Extract text from uploaded research papers and generate summaries.
- **Section-Aware Chunking:** Divide long articles into manageable chunks.
- **Local LLM Inference:** Generate summaries through Ollama without paid hosted-model API calls.
- **Model Selection:** Select supported local models from the interface.
- **Summary Export:** Download generated summaries in Markdown or JSON.
- **Evaluation Pipeline:** Produce per-article metrics, model comparisons, missing-output records, and batch execution logs.

**Note:** Scanned PDFs may require OCR. OCR is not currently included in the default PDF processing workflow.

## Architecture and Workflow

```text
Research Topic / Curated Library / PDF Upload
                     |
                     v
             Article Discovery
                     |
                     v
          PubMed Metadata Retrieval
                     |
                     v
             PMC Full-Text Lookup
                     |
          +----------+----------+
          |                     |
          v                     v
      PMC XML              PubMed Abstract
          |                     |
          +----------+----------+
                     |
                     v
          Parsing and Preprocessing
                     |
                     v
          Section-Aware Chunking
                     |
                     v
          Local Ollama Language Model
                     |
                     v
             Chunk Summarization
                     |
                     v
          Final Summary Consolidation
                     |
                     v
              Streamlit Interface
                     |
                     v
          Evaluation and Export
```

### Processing Pipeline

1. **Article Discovery:** Search PubMed using a research topic or query.
2. **Article Retrieval:** Retrieve publication metadata and identify available PMC full text.
3. **Parsing:** Parse PubMed XML, PMC XML, or extract text from uploaded PDFs.
4. **Preprocessing:** Prepare article sections and split long content into manageable chunks.
5. **Chunk Summarization:** Generate summaries for individual chunks using the selected local model.
6. **Summary Consolidation:** Combine chunk summaries into a final article summary.
7. **Presentation:** Display results in Streamlit and allow Markdown or JSON export.
8. **Evaluation:** Compare available summaries against article abstracts using ROUGE metrics.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.11 |
| Environment and Dependency Management | uv |
| User Interface | Streamlit |
| Literature Discovery | PubMed Entrez API |
| Article Metadata Retrieval | Biopython |
| Full-Text Source | PubMed Central |
| XML Processing | lxml |
| PDF Text Extraction | pypdf |
| Local LLM Runtime | Ollama |
| Models Evaluated | Phi-4 Mini and Qwen 2.5 3B |
| Evaluation Metrics | ROUGE-1, ROUGE-2, ROUGE-L |
| Data Processing | pandas, JSON, CSV |
| Optional Evaluation Metric | BERTScore (not run for the reported baseline) |

## Data Sources and Dataset

### Data Sources

**PubMed**

Used to discover relevant publications and retrieve metadata, identifiers, and abstracts.

**PubMed Central (PMC)**

Used to retrieve full-text XML for publications with accessible PMC content.

**PDF Documents**

Users can upload text-based research papers for text extraction and summarization.

### Dataset Curation

The initial dataset-selection workflow produced the following results:

| Dataset Stage | Count |
|---|---:|
| PubMed candidates found | 100 |
| Candidates with PMC full-text links | 95 |
| Candidates without PMC links | 5 |
| Article files discovered and audited | 21 |
| Audit errors | 0 |
| Selected articles (KEEP) | 16 |
| Articles requiring review (REVIEW) | 4 |
| Excluded articles (EXCLUDE) | 1 |

The selected articles are referenced in `data/selected_articles.json`, with article data stored under `data/articles/`.

These figures describe the initial dataset curation run.

## Models

The initial model comparison uses two locally hosted Ollama models.

### Phi-4 Mini

A compact language model evaluated for generating summaries from scientific article content.

### Qwen 2.5 3B

A compact language model evaluated using the same general article-summarization pipeline.

The comparison focuses on summary quality, output availability, and execution behavior.

Both models run locally through Ollama. Their exact installed model tags should be verified using:

```powershell
ollama list
```

## Evaluation Methodology

The current evaluation compares generated summaries with the corresponding scientific article abstracts.

### ROUGE-1

Measures unigram overlap between a generated summary and its reference text. Precision, recall, and F1 are reported.

### ROUGE-2

Measures bigram overlap between the generated summary and its reference text. ROUGE-2 F1 is included in the model comparison.

### ROUGE-L

Measures overlap based on the longest common subsequence between the generated summary and its reference text.

### Reference Text

The source article abstract is used as a reference proxy. It is not a gold-standard human-written summary. Consequently, ROUGE scores indicate textual overlap rather than directly measuring factual correctness, scientific reliability, or clinical usefulness.

BERTScore was not run for the reported baseline. Although execution time is recorded in the batch-run logs where available, a controlled aggregate latency comparison has not yet been completed.

### Evaluation Artifacts

The evaluation workflow stores its outputs under `outputs/evaluation/`.

| File | Purpose |
|---|---|
| `per_article_metrics.csv` | Per-article and per-model evaluation metrics |
| `model_comparison.csv` | Aggregated model-level metrics |
| `missing_summaries.csv` | Expected model outputs that were unavailable |
| `evaluation_summary.json` | Evaluation counts and summary statistics |
| `batch_run_log.jsonl` | Execution status, elapsed time, chunk counts, output paths, and recorded errors |

Batch-generated summaries are stored under `outputs/batch/`.

## Current Results

The current evaluation covers 16 selected articles and 25 available article-model summary pairs. Nine articles have summaries from both models.

| Metric | Phi-4 Mini | Qwen 2.5 3B |
|---|---:|---:|
| Available summaries | 10 | 15 |
| ROUGE-1 Precision | 0.3144 | 0.3617 |
| ROUGE-1 Recall | 0.6150 | 0.5765 |
| ROUGE-1 F1 | 0.4075 | 0.4333 |
| ROUGE-2 F1 | 0.1477 | 0.1504 |
| ROUGE-L F1 | 0.2069 | 0.2038 |
| Average Summary Length (words) | 386.10 | 336.87 |

### Results Interpretation

- Qwen 2.5 3B achieved higher aggregate ROUGE-1 F1 and ROUGE-2 F1 scores.
- Phi-4 Mini achieved higher aggregate ROUGE-1 recall and slightly higher ROUGE-L F1.
- Qwen 2.5 3B produced 15 available summaries, compared with 10 for Phi-4 Mini.
- Seven expected article-model outputs were unavailable: six for Phi-4 Mini and one for Qwen 2.5 3B.
- Only nine articles have outputs from both models, making these articles the appropriate subset for a controlled paired comparison.

Due to local compute and time constraints, the complete batch was not rerun to obtain matching coverage.

**Conclusion:** Qwen 2.5 3B is a provisional candidate based on the current results. The available evidence does not establish that it is definitively superior to Phi-4 Mini because the aggregate scores were calculated over different article sets.

## Installation and Setup

### Prerequisites

- Python 3.11
- uv package manager
- Ollama installed and running
- Sufficient system memory and GPU resources for the chosen model
- Internet access for PubMed and PMC retrieval

### 1. Open the Project

```powershell
cd D:\scientific-article-summarization
```

### 2. Install Dependencies

If the repository contains a valid `pyproject.toml` and lock file, install the project dependencies using:

```powershell
uv sync
```

### 3. Download Local Models

Pull the models you intend to use:

```powershell
ollama pull phi4-mini
ollama pull qwen2.5:3b
```

Verify the installed models:

```powershell
ollama list
```

The application must use model names matching the installed Ollama tags.

### 4. Start the Application

Run Streamlit from the project root:

```powershell
uv run streamlit run streamlit_app.py
```

Open the local URL displayed in the terminal. The default Streamlit address is usually:

```text
http://localhost:8501
```

### 5. Generate a Summary

1. Select the curated research library, PubMed search, or PDF upload.
2. Select an available local Ollama model.
3. Choose an article, submit a PubMed query, or upload a PDF.
4. Generate and review the summary.
5. Download the output in Markdown or JSON format if required.

### 6. Run Evaluation

From the project root, run the existing evaluation script:

```powershell
uv run python app/evaluation/evaluate_summaries.py
```

Review the script's supported arguments before enabling optional metrics or starting compute-intensive operations. The existing baseline can be evaluated from saved outputs without rerunning the complete summarization batch.

## Project Structure

The following is an abbreviated view of the main project files:

```text
scientific-article-summarization/
├── app/
│   ├── evaluation/
│   │   ├── run_batch.py
│   │   └── evaluate_summaries.py
│   ├── fulltext.py
│   ├── llm_client.py
│   ├── parser.py
│   ├── pdf_ingestion.py
│   ├── preprocessing.py
│   ├── pubmed.py
│   └── summarizer.py
├── data/
│   ├── articles/
│   └── selected_articles.json
├── outputs/
│   ├── batch/
│   └── evaluation/
├── streamlit_app.py
└── README.md
```

Other configuration files, tests, dataset-audit scripts, and research documentation may also be present in the repository.

## Limitations

1. **Unequal model coverage:** The models did not successfully summarize the same number of articles.
2. **Abstract-based reference:** ROUGE is calculated against abstracts, which are reference proxies rather than gold-standard summaries.
3. **BERTScore not evaluated:** The reported baseline does not include semantic similarity metrics from BERTScore.
4. **Latency comparison incomplete:** Execution times are recorded where available, but a controlled aggregate comparison has not been completed.
5. **Local resource constraints:** Long documents can take substantial time to process or fail because of context and resource limits.
6. **PDF extraction limitations:** Scanned PDFs may require OCR, which is not currently part of the default workflow.
7. **Full-text availability:** Not every PubMed result has accessible PMC full text.
8. **Potential factual errors:** Generated summaries may omit qualifications or introduce inaccuracies.
9. **No clinical validation:** The application is an educational and research prototype, not a clinical decision-support system.

Generated summaries should always be checked against their source articles before being used for scientific or clinical decisions.

## Future Work

- Evaluate both models on the same nine paired articles.
- Review a sample of summaries for factual consistency, coverage, and unsupported claims.
- Add BERTScore if available compute and time permit.
- Aggregate latency, failure rates, and resource usage from existing logs.
- Improve long-document handling and error recovery.
- Add OCR support for scanned PDFs.
- Expand evaluation using human judgments and appropriate reference summaries.
- Preserve dataset-selection decisions, evaluation procedures, and research