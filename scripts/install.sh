#!/usr/bin/env bash
# Installs shai as a global command (available from any directory) using pipx,
# and sets up a global config/secrets file at ~/.config/shai/.env so it works
# regardless of which directory you run it from. Safe to re-run.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v pipx >/dev/null 2>&1; then
    echo "==> pipx not found — installing it (recommended for isolated global CLI installs)"
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    echo
    echo "⚠️  pipx was just installed. Open a new shell (or 'source' your shell rc file) so"
    echo "    the PATH change takes effect, then re-run this script to finish installing shai."
    exit 0
fi

echo "==> Installing shAI globally with pipx"
pipx install --force .

CONFIG_DIR="${SHAI_CONFIG_DIR:-$HOME/.config/shai}"
GLOBAL_ENV="$CONFIG_DIR/.env"
mkdir -p "$CONFIG_DIR"

if [ ! -f "$GLOBAL_ENV" ]; then
    cp .env.example "$GLOBAL_ENV"
    echo "==> Created $GLOBAL_ENV"
fi

echo
echo "Which model provider would you like to use?"
echo "  1) ollama  - local, free, requires https://ollama.ai"
echo "  2) mistral - hosted, requires an API key from https://console.mistral.ai/"
echo "  3) openai  - hosted (or any OpenAI-compatible endpoint), requires an API key"
read -rp "Choice [1/2/3]: " CHOICE

case "$CHOICE" in
    2) PROVIDER_NAME="mistral" ;;
    3) PROVIDER_NAME="openai" ;;
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
    KEY_VAR="MISTRAL_API_KEY"
    [ "$PROVIDER_NAME" = "openai" ] && KEY_VAR="OPENAI_API_KEY"

    read -rsp "Enter your ${PROVIDER_NAME} API key (input hidden, leave blank to skip): " API_KEY
    echo
    if [ -n "$API_KEY" ]; then
        grep -v "^${KEY_VAR}=" "$GLOBAL_ENV" > "$GLOBAL_ENV.tmp" || true
        mv "$GLOBAL_ENV.tmp" "$GLOBAL_ENV"
        echo "${KEY_VAR}=${API_KEY}" >> "$GLOBAL_ENV"
        echo "==> Saved ${KEY_VAR} to $GLOBAL_ENV"
    else
        echo "==> Skipped — set ${KEY_VAR} in $GLOBAL_ENV before using the ${PROVIDER_NAME} provider"
    fi
fi

echo
echo "✅ shai installed: $(command -v shai || echo '(open a new shell if not found on PATH)')"
echo
echo "Try it from any directory:"
echo "   shai ask \"list all files in the current directory\""
echo
echo "Swap providers anytime with: shai config set-provider <ollama|mistral|openai>"
echo "Swap models anytime with:    shai config set-model <model-name>"
echo "Check current config with:   shai config show"
echo "Enable tab-completion with:  shai completion <bash|zsh|fish>"
