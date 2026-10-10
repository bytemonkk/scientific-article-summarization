
"""Local LLM client using Ollama, instrumented with Langfuse."""

import os

import requests
from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()

BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

langfuse = get_client()


def generate_response(
    prompt: str,
    system_prompt: str = "You are a careful scientific writing assistant.",
    max_tokens: int = 300,
) -> str:
    """Generate a response from Ollama and record the call in Langfuse."""

    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="ollama-generate-response",
        model=MODEL,
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
        response = requests.post(
            f"{BASE_URL.rstrip('/')}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            system_prompt
                            + "\n/no_think\n"
                            + "Return only the requested answer. "
                            + "Do not include planning, internal reasoning, "
                            + "or commentary about the user or the prompt."
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

        if not content or not content.strip():
            raise RuntimeError(
                "Ollama returned no visible text. "
                f"Response keys: {list(result.keys())}"
            )

        # Ollama reports token counts and timing in its API response.
        # Record token usage only when the corresponding values exist.
        usage = {}
        if isinstance(result.get("prompt_eval_count"), int):
            usage["input_tokens"] = result["prompt_eval_count"]
        if isinstance(result.get("eval_count"), int):
            usage["output_tokens"] = result["eval_count"]

        metadata = {
            "ollama_total_duration_ms": (
                result["total_duration"] / 1_000_000
                if isinstance(result.get("total_duration"), (int, float))
                else None
            ),
            "ollama_load_duration_ms": (
                result["load_duration"] / 1_000_000
                if isinstance(result.get("load_duration"), (int, float))
                else None
            ),
            "ollama_prompt_eval_duration_ms": (
                result["prompt_eval_duration"] / 1_000_000
                if isinstance(result.get("prompt_eval_duration"), (int, float))
                else None
            ),
            "ollama_eval_duration_ms": (
                result["eval_duration"] / 1_000_000
                if isinstance(result.get("eval_duration"), (int, float))
                else None
            ),
        }
        metadata = {
            key: value for key, value in metadata.items()
            if value is not None
        }

        generation.update(
            output=content.strip(),
            usage_details=usage or None,
            metadata=metadata,
        )

        return content.strip()