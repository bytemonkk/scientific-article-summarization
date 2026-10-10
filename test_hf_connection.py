
from app.llm_client import MODEL, generate_response


def main():
    print(f"Testing model: {MODEL}")

    result = generate_response(
        "In two sentences, explain why validation data matters "
        "when evaluating a machine learning model."
    )

    print("\nMODEL RESPONSE\n")
    print(result)
    print("\nHugging Face inference test completed.")


if __name__ == "__main__":
    main()
