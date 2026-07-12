"""
Common interface every model provider implements.
Agents talk to this interface only, never to a specific SDK/API directly.
"""
from abc import ABC, abstractmethod
from typing import Optional


class LLMError(Exception):
    """Raised when a provider fails to produce a response."""


class LLMProvider(ABC):
    #: model used when the caller doesn't request a specific one. Subclasses should expose
    #: this as a property that reads its env var lazily, so .env loading order doesn't matter.
    default_model: str = ""

    @abstractmethod
    def chat(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Send a single-turn prompt to the model and return its raw text reply.

        Args:
            prompt: The user prompt to send.
            model: Override for the provider's default_model.

        Returns:
            The model's text response.

        Raises:
            LLMError: If the request fails for any reason.
        """
        raise NotImplementedError
