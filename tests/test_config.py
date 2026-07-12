import config


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.delenv("SHAI_PROVIDER", raising=False)


def test_load_config_defaults_when_no_file(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    cfg = config.load_config()
    assert cfg == {"provider": "ollama", "models": {}}


def test_set_and_load_provider_roundtrip(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    config.set_provider("mistral")
    assert config.load_config()["provider"] == "mistral"


def test_set_and_load_model_roundtrip(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    config.set_model("ollama", "llama3.2")
    assert config.load_config()["models"]["ollama"] == "llama3.2"


def test_resolve_provider_precedence(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    config.set_provider("mistral")

    # config file wins over built-in default
    assert config.resolve_provider(None) == "mistral"

    # env var wins over config file
    monkeypatch.setenv("SHAI_PROVIDER", "openai")
    assert config.resolve_provider(None) == "openai"

    # explicit CLI value wins over everything
    assert config.resolve_provider("ollama") == "ollama"


def test_resolve_model_precedence(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    config.set_model("mistral", "mistral-small-latest")

    assert config.resolve_model(None, "mistral") == "mistral-small-latest"
    assert config.resolve_model("mistral-large-latest", "mistral") == "mistral-large-latest"
    assert config.resolve_model(None, "ollama") is None
