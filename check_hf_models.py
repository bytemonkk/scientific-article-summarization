
import os

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HF_TOKEN")
if not token:
    raise RuntimeError("HF_TOKEN is missing from .env")

response = requests.get(
    "https://router.huggingface.co/v1/models",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,
)
response.raise_for_status()

models = response.json().get("data", [])

print(f"Models returned by the inference router: {len(models)}\n")

shown = 0

for model in models:
    providers = model.get("providers", [])
    live_providers = [
        item.get("provider", "unknown")
        for item in providers
        if item.get("status") == "live"
    ]

    if live_providers:
        print(f"Model: {model.get('id')}")
        print(f"Providers: {', '.join(live_providers)}")
        print()
        shown += 1

    if shown >= 20:
        break

if shown == 0:
    print("No live-provider models were listed. Check the account and token permissions.")
