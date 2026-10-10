"""Parse PubMed XML records into normalized article metadata."""

from lxml import etree


def _extract_text(element) -> str:
    """Extract text while preserving boundaries between XML text nodes."""
    if element is None:
        return ""

    return " ".join(
        part.strip()
        for part in element.itertext()
        if part and part.strip()
    )


def parse_articles(xml_data: bytes) -> list[dict]:
    root = etree.fromstring(xml_data)
    articles = []

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")

        title = _extract_text(article.find(".//ArticleTitle"))

        abstract_parts = []

        for abstract_text in article.findall(".//Abstract/AbstractText"):
            label = abstract_text.get("Label")
            text = _extract_text(abstract_text)

            if label:
                abstract_parts.append(f"{label}: {text}")
            elif text:
                abstract_parts.append(text)

        abstract = "\n\n".join(abstract_parts)

        journal = article.findtext(".//Journal/Title")
        publication_year = article.findtext(".//PubDate/Year")

        articles.append(
            {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "publication_year": publication_year,
            }
        )

    return articles