import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)
model = os.getenv("OLLAMA_MODEL", "qwen3:4b")

response = requests.post(
    f"{base_url.rstrip('/')}/api/chat",
    json={
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a scientific writing assistant. "
                    "Return only the requested answer. "
                    "Do not include planning or commentary."
                    "\n/no_think"
                ),
            },
            {
                "role": "user",
                "content": (
                    "Explain scientific article summarization "
                    "in exactly two sentences.\n/no_think"
                ),
            },
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 150,
        },
    },
    timeout=(10, 600),
)

response.raise_for_status()
result = response.json()
message = result.get("message", {})

print("Model:", model)
print("Message fields:", list(message.keys()))
print("\nThinking field:")
print(message.get("thinking", "<not present>"))
print("\nContent field:")
print(message.get("content", "<not present>"))