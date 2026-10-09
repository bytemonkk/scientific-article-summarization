from Bio import Entrez
from lxml import etree

from app.fulltext import fetch_pmc_xml

Entrez.email = "spideymail.4.71@gmail.com"

# First three candidates from our successful PMC-link search.
pmc_ids = [
    "10277911",
    "10025752",
    "8481582",
]


def main():
    for pmc_id in pmc_ids:
        print(f"\nChecking PMC{pmc_id}")

        try:
            xml_data = fetch_pmc_xml(pmc_id)
            root = etree.fromstring(xml_data)

            title = root.findtext(".//article-title")
            abstract = " ".join(
                text.strip()
                for text in root.xpath(
                    ".//abstract//text()[normalize-space()]"
                )
            )

            sections = root.xpath(
                ".//body//sec"
            )

            headings = [
                " ".join(
                    sec.xpath(
                        "./title//text()"
                    )
                ).strip()
                for sec in sections
            ]

            print(f"XML bytes: {len(xml_data)}")
            print(f"Title: {title}")
            print(f"Abstract characters: {len(abstract)}")
            print(f"Body sections: {len(sections)}")
            print(f"Headings: {headings[:10]}")

            if not title or not sections:
                print("VALIDATION FAILED: missing title or body sections")
            else:
                print("VALIDATION PASSED")

        except Exception as exc:
            print(f"VALIDATION FAILED: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()