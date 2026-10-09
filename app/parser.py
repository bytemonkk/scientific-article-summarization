from lxml import etree


def parse_articles(xml_data: bytes) -> list[dict]:
    root = etree.fromstring(xml_data)

    articles = []

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        title = "".join(article.find(".//ArticleTitle").itertext()) \
            if article.find(".//ArticleTitle") is not None else ""

        abstract_parts = []

        for abstract_text in article.findall(".//Abstract/AbstractText"):
            label = abstract_text.get("Label")

            text = "".join(abstract_text.itertext()).strip()

            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)

        abstract = "\n\n".join(abstract_parts)

        journal = article.findtext(".//Journal/Title")
        publication_year = article.findtext(
            ".//PubDate/Year"
        )

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