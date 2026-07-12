#!/usr/bin/env bash
# Interactive setup for shAI: creates a venv, installs the package, and configures
# a model provider (Ollama or Mistral). Safe to re-run.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

echo "==> Using $($PYTHON_BIN --version)"

if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment in $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "==> Installing shAI and dependencies"
pip install --quiet --upgrade pip
pip install --quiet -e .

if [ ! -f .env ]; then
    cp .env.example .env
    echo "==> Created .env from .env.example"
fi

echo
echo "Which model provider would you like to use?"
echo "  1) ollama  - local, free, requires https://ollama.ai"
echo "  2) mistral - hosted, requires an API key from https://console.mistral.ai/"
read -rp "Choice [1/2]: " CHOICE

case "$CHOICE" in
    2) PROVIDER_NAME="mistral" ;;
    *) PROVIDER_NAME="ollama" ;;
esac

shai config set-provider "$PROVIDER_NAME"

if [ "$PROVIDER_NAME" = "ollama" ]; then
    if ! command -v ollama >/dev/null 2>&1; then
        echo "⚠️  Ollama is not installed. Install it from https://ollama.ai and re-run this script."
    else
        read -rp "Pull the default model (llama3.1:8b)? [Y/n] " PULL
        if [[ ! "$PULL" =~ ^[Nn]$ ]]; then
            ollama pull llama3.1:8b
        fi
    fi
else
    read -rsp "Enter your Mistral API key (input hidden, leave blank to skip): " MISTRAL_KEY
    echo
    if [ -n "$MISTRAL_KEY" ]; then
        # Rewrite .env without any existing MISTRAL_API_KEY line, then append the new one.
        grep -v '^MISTRAL_API_KEY=' .env > .env.tmp || true
        mv .env.tmp .env
        echo "MISTRAL_API_KEY=$MISTRAL_KEY" >> .env
        echo "==> Saved Mistral API key to .env"
    else
        echo "==> Skipped — set MISTRAL_API_KEY in .env before using the mistral provider"
    fi
fi

echo
echo "✅ Setup complete. Try it out:"
echo "   source $VENV_DIR/bin/activate"
echo "   shai ask \"list all files in the current directory\""
echo
echo "Swap providers anytime with: shai config set-provider <ollama|mistral>"
echo "Swap models anytime with:    shai config set-model <model-name>"
echo "Check current config with:   shai config show"
