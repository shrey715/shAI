#!/usr/bin/env bash
# Removes shai however it was installed (pipx or pip), plus the local dev venv if
# present. Config, history, and any global .env are left in place unless --purge
# is passed, since they may hold API keys or data you'd want to keep.
set -euo pipefail

PURGE=false
for arg in "$@"; do
    case "$arg" in
        --purge) PURGE=true ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v pipx >/dev/null 2>&1 && pipx list --short 2>/dev/null | grep -q '^shai '; then
    echo "==> Removing pipx install"
    pipx uninstall shai
elif python3 -m pip show shai >/dev/null 2>&1; then
    echo "==> Removing pip install"
    python3 -m pip uninstall -y shai
else
    echo "shai does not appear to be installed via pipx or pip (nothing to remove there)."
fi

if [ -d "$ROOT_DIR/.venv" ]; then
    echo "==> Removing local dev virtualenv ($ROOT_DIR/.venv)"
    rm -rf "$ROOT_DIR/.venv"
fi

CONFIG_DIR="${SHAI_CONFIG_DIR:-$HOME/.config/shai}"
DATA_DIR="${SHAI_DATA_DIR:-$HOME/.local/share/shai}"

if [ "$PURGE" = true ]; then
    echo "==> Purging config, secrets, and history ($CONFIG_DIR, $DATA_DIR)"
    rm -rf "$CONFIG_DIR" "$DATA_DIR"
else
    echo "Config/secrets and history left in place ($CONFIG_DIR, $DATA_DIR)."
    echo "Re-run with --purge to remove those too."
fi

echo "✅ shai uninstalled."
