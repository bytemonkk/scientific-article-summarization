from Bio import Entrez

from app.dataset import save_article

Entrez.email = "YOUR_EMAIL@example.com"

# PMC10025752 is our first validated full-text candidate.
PMC_IDS = ["10025752"]


def main():
    for pmc_id in PMC_IDS:
        try:
            path = save_article(pmc_id)
            print(f"Saved: {path}")
        except Exception as exc:
            print(
                f"Failed to save PMC{pmc_id}: "
                f"{type(exc).__name__}: {exc}"
            )


if __name__ == "__main__":
    main()
