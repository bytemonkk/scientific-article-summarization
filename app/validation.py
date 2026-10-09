from lxml import etree


EXCLUDED_HEADINGS = {
    "author contributions",
    "funding",
    "conflict of interest",
    "conflict of interest statement",
    "publisher's note",
    "acknowledgments",
    "acknowledgements",
    "references",
}


def _extract_text(element) -> str:
    """Extract normalized text from an XML element."""
    if element is None:
        return ""

    return " ".join(
        text.strip()
        for text in element.xpath(".//text()[normalize-space()]")
        if text.strip()
    )


def _extract_publication_year(article) -> int | None:
    """Extract the publication year from available JATS XML date fields."""
    year_paths = [
        "./front/article-meta/pub-date/year",
        "./front/article-meta/epub-date/year",
        "./front/article-meta/history/date[@date-type='accepted']/year",
        "./front/article-meta/history/date[@date-type='received']/year",
    ]

    for path in year_paths:
        values = article.xpath(path + "/text()")

        for value in values:
            value = value.strip()

            if value.isdigit() and len(value) == 4:
                return int(value)

    return None


def validate_pmc_xml(xml_data: bytes) -> dict:
    """
    Parse and validate a PubMed Central JATS XML article.

    An article is eligible when it has:
    - A title
    - An abstract containing at least 200 characters
    - At least two substantive body sections
    - At least 1,000 characters of extracted body text
    """

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        recover=False,
        huge_tree=False,
    )

    root = etree.fromstring(xml_data, parser=parser)

    # PMC responses may contain either an article or an article set.
    if etree.QName(root).localname == "article":
        article = root
    else:
        articles = root.xpath(
            ".//*[local-name()='article']"
        )
        article = articles[0] if articles else None

    if article is None:
        raise ValueError("No article element found in PMC XML.")

    # --------------------------------------------------
    # 1. Extract article metadata
    # --------------------------------------------------

    title = _extract_text(
        article.find("./front/article-meta/title-group/article-title")
    )

    abstract = _extract_text(
        article.find("./front/article-meta/abstract")
    )

    pmid_values = article.xpath(
        "./front/article-meta/article-id"
        "[@pub-id-type='pmid']/text()"
    )
    pmid = pmid_values[0].strip() if pmid_values else None

    journal = _extract_text(
        article.find(
            "./front/journal-meta/"
            "journal-title-group/journal-title"
        )
    )

    publication_year = _extract_publication_year(article)

    # --------------------------------------------------
    # 2. Extract substantive body sections
    # --------------------------------------------------

    sections = []

    for section in article.xpath("./body//sec"):
        heading = _extract_text(section.find("./title"))
        normalized_heading = heading.casefold().strip()

        if normalized_heading in EXCLUDED_HEADINGS:
            continue

        # Collect text belonging to this section, excluding
        # nested subsections so their content is not duplicated.
        text_parts = section.xpath(
            "./node()[not(self::sec)]"
            "//text()[normalize-space()]"
        )

        section_text = " ".join(
            part.strip()
            for part in text_parts
            if part.strip()
        )

        if len(section_text) < 100:
            continue

        # Avoid repeating the heading when it is already the
        # opening text of the extracted section.
        if heading and section_text.casefold().startswith(
            heading.casefold()
        ):
            section_text = section_text[len(heading):].strip(
                " :-\n\t"
            )

        sections.append(
            {
                "heading": heading or "Untitled section",
                "text": section_text,
            }
        )

    # --------------------------------------------------
    # 3. Calculate validation metrics
    # --------------------------------------------------

    body_characters = sum(
        len(section["text"]) for section in sections
    )

    checks = {
        "has_title": bool(title),
        "has_abstract": len(abstract) >= 200,
        "has_enough_sections": len(sections) >= 2,
        "has_enough_body_text": body_characters >= 1000,
    }

    passed = all(checks.values())

    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "journal": journal or None,
        "publication_year": publication_year,
        "sections": sections,
        "section_count": len(sections),
        "body_characters": body_characters,
        "checks": checks,
        "passed": passed,
    }