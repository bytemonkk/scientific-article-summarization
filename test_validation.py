from Bio import Entrez

from app.fulltext import fetch_pmc_xml
from app.validation import validate_pmc_xml

Entrez.email = "spideymail.4.71@gmail.com"

PMC_IDS = [
    "10277911",
    "10025752",
    "8481582",
]


def main():
    for pmc_id in PMC_IDS:
        print(f"\n{'=' * 70}")
        print(f"PMC{pmc_id}")

        try:
            xml_data = fetch_pmc_xml(pmc_id)
            result = validate_pmc_xml(xml_data)

            print(f"Title: {result['title']}")
            print(f"Abstract characters: {len(result['abstract'])}")
            print(f"Substantive sections: {result['section_count']}")
            print(f"Body characters: {result['body_characters']}")
            print(f"Eligible: {result['passed']}")

            for section in result["sections"][:5]:
                print(f"  - {section['heading']}")

        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()