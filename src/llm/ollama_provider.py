import os
from typing import Optional

from llm.base import LLMProvider, LLMError


class OllamaProvider(LLMProvider):
    """Local inference via Ollama (https://ollama.ai)."""

    @property
    def default_model(self) -> str:
        # Read lazily (not at import time) so .env is honored regardless of import order.
        return os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def __init__(self, host: Optional[str] = None):
        try:
            import ollama
        except ImportError as e:
            raise LLMError(
                "The 'ollama' package is required for the ollama provider. Install it with "
                "'pip install ollama'."
            ) from e

        host = host or os.getenv("OLLAMA_HOST")
        self._client = ollama.Client(host=host) if host else ollama

    def chat(self, prompt: str, model: Optional[str] = None) -> str:
        try:
            response = self._client.chat(
                model=model or self.default_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"].strip()
        except Exception as e:
            raise LLMError(f"Ollama request failed: {e}") from e
