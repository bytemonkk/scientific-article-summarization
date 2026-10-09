from Bio import Entrez
from lxml import etree

from app.fulltext import fetch_pmc_xml

Entrez.email = "YOUR_EMAIL@example.com"

PMC_IDS = ["10277911", "10025752", "8481582"]


def main():
    for pmc_id in PMC_IDS:
        print(f"\n{'=' * 70}")
        print(f"PMC{pmc_id}")

        xml_data = fetch_pmc_xml(pmc_id)
        root = etree.fromstring(xml_data)

        print("Root tag:", root.tag)
        print("Root attributes:", root.attrib)

        # Inspect only the article's direct front-matter structure.
        for child in root:
            print("Child:", child.tag)

            if etree.QName(child).localname == "front":
                for front_child in child:
                    print("  Front child:", front_child.tag)

                    if etree.QName(front_child).localname == "article-meta":
                        for meta_child in front_child:
                            print("    Meta child:", meta_child.tag)

        # Show the first article-title and abstract paths.
        titles = root.xpath(
            "//*[local-name()='article-title']"
        )
        abstracts = root.xpath(
            "//*[local-name()='abstract']"
        )

        print("Article-title elements:", len(titles))
        for title in titles[:3]:
            print("  Path:", root.getroottree().getpath(title))
            print("  Text:", " ".join(title.itertext())[:200])

        print("Abstract elements:", len(abstracts))
        for abstract in abstracts[:2]:
            print("  Path:", root.getroottree().getpath(abstract))
            print("  Text:", " ".join(abstract.itertext())[:200])


if __name__ == "__main__":
    main()