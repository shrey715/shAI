import os
from typing import Optional

import requests

from llm.base import LLMProvider, LLMError

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralProvider(LLMProvider):
    """Hosted inference via the Mistral API (https://docs.mistral.ai)."""

    @property
    def default_model(self) -> str:
        # Read lazily (not at import time) so .env is honored regardless of import order.
        return os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise LLMError(
                "MISTRAL_API_KEY is not set. Add it to your .env file or export it "
                "in your shell to use the mistral provider."
            )

    def chat(self, prompt: str, model: Optional[str] = None) -> str:
        try:
            response = requests.post(
                MISTRAL_API_URL,
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
            raise LLMError(f"Mistral request failed: {e}") from e
        except (KeyError, IndexError) as e:
            raise LLMError(f"Unexpected Mistral response format: {e}") from e
