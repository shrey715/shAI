import agents.cmd_validator as cmd_validator


class FakeProvider:
    def __init__(self, reply):
        self.reply = reply

    def chat(self, prompt, model=None):
        return self.reply


def test_empty_query_rejected_without_calling_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("LLM should not be called for an empty query")
    monkeypatch.setattr(cmd_validator, "get_provider", boom)

    is_valid, _ = cmd_validator.validate_query("")
    assert is_valid is False


def test_conversational_query_rejected_without_calling_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("LLM should not be called for a conversational query")
    monkeypatch.setattr(cmd_validator, "get_provider", boom)

    is_valid, reason = cmd_validator.validate_query("hello there, how are you")
    assert is_valid is False
    assert "conversational" in reason.lower()


def test_coding_request_rejected_without_calling_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("LLM should not be called for a coding request")
    monkeypatch.setattr(cmd_validator, "get_provider", boom)

    is_valid, reason = cmd_validator.validate_query("write a python script to sort a list")
    assert is_valid is False
    assert "shell assistant" in reason.lower()


def test_shell_query_passes_via_llm(monkeypatch):
    monkeypatch.setattr(cmd_validator, "get_provider", lambda provider: FakeProvider("YES"))

    is_valid, _ = cmd_validator.validate_query("list all pdf files in this directory")
    assert is_valid is True


def test_non_shell_query_rejected_via_llm(monkeypatch):
    monkeypatch.setattr(cmd_validator, "get_provider", lambda provider: FakeProvider("NO"))

    is_valid, _ = cmd_validator.validate_query("what is the capital of France")
    assert is_valid is False
