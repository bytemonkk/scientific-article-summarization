
from app.summarizer import summarize_article_file


def main():
    result = summarize_article_file(
        json_path="data/articles/PMC10025752.json",
        output_path="outputs/PMC10025752_summary.json",
    )

    print(f"Article: {result['title']}")
    print(f"Model: {result['model']}")
    print(f"Chunks summarized: {result['chunk_count']}")
    print("\nFINAL SUMMARY\n")
    print(result["final_summary"])
    print("\nSaved to outputs/PMC10025752_summary.json")


if __name__ == "__main__":
    main()
