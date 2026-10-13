"""Local Ollama LLM client with optional Langfuse instrumentation."""

import os

import requests
from dotenv import load_dotenv

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LANGFUSE_ENABLED = (
    os.getenv("LANGFUSE_ENABLED", "true").strip().lower()
    in {"1", "true", "yes", "on"}
)

# Retained for compatibility with existing imports.
# The actual model is resolved dynamically for every request.
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

langfuse = None
if LANGFUSE_ENABLED:
    from langfuse import get_client

    langfuse = get_client()


def get_model_name() -> str:
    """Return the model configured for the current request."""
    return os.getenv("OLLAMA_MODEL", "qwen3:4b")


def _request_ollama(
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    model: str,
) -> tuple[str, dict]:
    """Call Ollama and return its text and response metadata."""

    response = requests.post(
        f"{BASE_URL.rstrip('/')}/api/chat",
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        system_prompt
                        + "\n/no_think\n"
                        + "Return only the requested answer. "
                        + "Do not include planning, internal reasoning, "
                        + "or commentary about the user or prompt."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt + "\n\n/no_think",
                },
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.2,
                "num_predict": max_tokens,
            },
        },
        timeout=(10, 600),
    )

    response.raise_for_status()
    result = response.json()
    content = result.get("message", {}).get("content", "")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "Ollama returned no visible text. "
            f"Response keys: {list(result.keys())}"
        )

    return content.strip(), result


def generate_response(
    prompt: str,
    system_prompt: str = "You are a careful scientific writing assistant.",
    max_tokens: int = 300,
) -> str:
    """Generate a response using the currently configured Ollama model."""

    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    # Resolve the model at call time, not module-import time.
    model = get_model_name()

    if langfuse is None:
        content, _ = _request_ollama(
            prompt, system_prompt, max_tokens, model
        )
        return content

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="ollama-generate-response",
        model=model,
        input={
            "system_prompt": system_prompt,
            "prompt": prompt,
            "max_tokens": max_tokens,
        },
        metadata={
            "provider": "ollama",
            "endpoint": "/api/chat",
        },
    ) as generation:
        content, result = _request_ollama(
            prompt, system_prompt, max_tokens, model
        )

        usage = {}
        if isinstance(result.get("prompt_eval_count"), int):
            usage["input_tokens"] = result["prompt_eval_count"]
        if isinstance(result.get("eval_count"), int):
            usage["output_tokens"] = result["eval_count"]

        timing_fields = {
            "ollama_total_duration_ms": "total_duration",
            "ollama_load_duration_ms": "load_duration",
            "ollama_prompt_eval_duration_ms": "prompt_eval_duration",
            "ollama_eval_duration_ms": "eval_duration",
        }

        metadata = {}
        for output_key, input_key in timing_fields.items():
            value = result.get(input_key)
            if isinstance(value, (int, float)):
                metadata[output_key] = value / 1_000_000

        generation.update(
            output=content,
            usage_details=usage or None,
            metadata=metadata or None,
        )

        return content