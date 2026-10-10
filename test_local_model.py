
from app.llm_client import MODEL, generate_response


def main():
    print(f"Testing local model: {MODEL}")

    result = generate_response(
        "Explain scientific article summarization in two sentences.",
        max_tokens=200,
    )

    print("\nMODEL RESPONSE\n")
    print(result)
    print("\nLocal model inference completed.")


if __name__ == "__main__":
    main()