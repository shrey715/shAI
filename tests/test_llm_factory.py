import pytest

from llm import get_provider, LLMError
from llm.ollama_provider import OllamaProvider


def test_unknown_provider_raises():
    with pytest.raises(LLMError):
        get_provider("not-a-real-provider")


def test_mistral_without_api_key_raises(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(LLMError):
        get_provider("mistral")


def test_openai_without_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMError):
        get_provider("openai")


def test_ollama_default_model_reads_env_lazily(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    provider = OllamaProvider.__new__(OllamaProvider)  # skip __init__'s ollama import
    assert provider.default_model == "llama3.1:8b"

    monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
    assert provider.default_model == "custom-model"
