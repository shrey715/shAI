import os
from typing import Optional

from llm.base import LLMProvider, LLMError
from llm.ollama_provider import OllamaProvider
from llm.mistral_provider import MistralProvider
from llm.openai_compatible_provider import OpenAICompatibleProvider

# Add new providers here to make them available across every agent.
PROVIDERS = {
    "ollama": OllamaProvider,
    "mistral": MistralProvider,
    "openai": OpenAICompatibleProvider,
}


def get_provider(name: Optional[str] = None) -> LLMProvider:
    """
    Instantiate the requested provider, falling back to SHAI_PROVIDER / "ollama".
    """
    name = (name or os.getenv("SHAI_PROVIDER", "ollama")).lower()

    if name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS))
        raise LLMError(f"Unknown provider '{name}'. Available providers: {available}")

    return PROVIDERS[name]()
