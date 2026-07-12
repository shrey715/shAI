import os
from typing import Optional

import requests

from llm.base import LLMProvider, LLMError


class OpenAICompatibleProvider(LLMProvider):
    """
    Any backend that speaks the OpenAI chat-completions schema: OpenAI itself, Groq,
    Together, OpenRouter, or a local server (llama.cpp, LM Studio, vLLM, ...).

    Point it elsewhere with $OPENAI_BASE_URL, e.g.:
      https://api.groq.com/openai/v1
      http://localhost:1234/v1   (LM Studio)
    """

    @property
    def default_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        if not self.api_key:
            raise LLMError(
                "OPENAI_API_KEY is not set. Add it to your .env file or export it in your shell "
                "to use the openai provider (also set OPENAI_BASE_URL if targeting a non-OpenAI "
                "OpenAI-compatible endpoint)."
            )

    def chat(self, prompt: str, model: Optional[str] = None) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except requests.RequestException as e:
            raise LLMError(f"OpenAI-compatible request failed: {e}") from e
        except (KeyError, IndexError) as e:
            raise LLMError(f"Unexpected OpenAI-compatible response format: {e}") from e
