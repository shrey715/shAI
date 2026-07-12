"""
Persisted user preferences (active provider, per-provider model overrides).

Precedence for both provider and model, highest wins:
  1. explicit CLI flag
  2. $SHAI_PROVIDER / $<PROVIDER>_MODEL env var (see llm/*_provider.py for models)
  3. this config file (~/.config/shai/config.json, or $SHAI_CONFIG_DIR)
  4. built-in default
"""
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

CONFIG_DIR = Path(os.getenv("SHAI_CONFIG_DIR", Path.home() / ".config" / "shai"))
CONFIG_FILE = CONFIG_DIR / "config.json"

# Secrets (API keys) resolve in this order: already-exported shell vars, a project-local
# .env (cwd or an ancestor — handy for `pip install -e .` dev use), then a global
# ~/.config/shai/.env — so a system-wide `shai` install still finds your key regardless
# of which directory you run it from. load_dotenv() never overrides an already-set var.
load_dotenv()
load_dotenv(dotenv_path=CONFIG_DIR / ".env")

def _defaults() -> dict:
    # Fresh dict every call — a shared/copied "models" dict would let set_model()
    # on one config accidentally mutate every other config that hits this fallback.
    return {"provider": "ollama", "models": {}}


def load_config() -> dict:
    cfg = _defaults()
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            cfg["provider"] = data.get("provider", cfg["provider"])
            cfg["models"] = data.get("models", cfg["models"])
        except json.JSONDecodeError:
            pass
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")


def set_provider(name: str) -> None:
    cfg = load_config()
    cfg["provider"] = name
    save_config(cfg)


def set_model(provider: str, model: str) -> None:
    cfg = load_config()
    cfg.setdefault("models", {})[provider] = model
    save_config(cfg)


def resolve_provider(cli_value: Optional[str]) -> str:
    return (cli_value or os.getenv("SHAI_PROVIDER") or load_config().get("provider") or "ollama").lower()


def resolve_model(cli_value: Optional[str], provider: str) -> Optional[str]:
    """Returns None if nothing overrides it — callers fall back to the provider's own default."""
    return cli_value or load_config().get("models", {}).get(provider)
