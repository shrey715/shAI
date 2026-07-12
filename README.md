# shAI - The Intelligent Shell Assistant

shAI turns natural language into shell commands. Describe what you want to do on the command line, and shAI generates the command(s), checks them for safety, shows them to you, and (with your confirmation) runs them.

shAI is a **shell assistant, not a coding assistant** — it only handles things you'd normally do at a terminal (files, processes, disk, network, git, packages...). It will refuse requests to write programs in other languages ("write a Python script to...") — that's out of scope on purpose.

This project is intentionally built without an agent framework (no LangChain, no AutoGen) — every agent is a plain Python function that talks to a small, model-agnostic LLM interface.

## Features

- 🧠 Natural language to shell command translation, including multi-step tasks ("update packages and clean the cache")
- 🔍 Query validation to ensure appropriate use (rejects chit-chat and coding requests)
- 🔒 Command safety validation before execution, plus a confirmation prompt before anything runs (auto-skipped for read-only commands like `ls`/`cat`/`ps`)
- 📋 Detailed execution results and error reporting
- 🕘 Local request history (`shai history`)
- 🔌 Model agnostic — swap providers with one command, no code changes
- 🌐 Runs locally via [Ollama](https://ollama.ai/), or hosted via [Mistral](https://docs.mistral.ai/) or any OpenAI-compatible API (OpenAI, Groq, local llama.cpp/LM Studio servers, ...)
- 🖥️ Installs as a real global command via [pipx](https://pipx.pypa.io/), with tab-completion and a clean uninstall

## Installation

### Prerequisites

- Python 3.8 or higher
- One of: [Ollama](https://ollama.ai/) running locally, a [Mistral API key](https://console.mistral.ai/), or an OpenAI(-compatible) API key

### Option A: Install globally (recommended for everyday use)

```bash
git clone https://github.com/shrey715/shAI.git
cd shAI
./scripts/install.sh
```

This installs `shai` as a real system command via [pipx](https://pipx.pypa.io/) (isolated from your other Python environments, no venv to activate), sets up `~/.config/shai/.env` for secrets, and walks you through picking a provider. Once it's done, you can `cd` anywhere and just run `shai ask "..."` — you no longer need the cloned repo.

To uninstall cleanly:

```bash
./scripts/uninstall.sh            # removes the shai command
./scripts/uninstall.sh --purge    # also deletes config, history, and saved API keys
```

### Option B: Local dev setup (venv)

```bash
git clone https://github.com/shrey715/shAI.git
cd shAI
./scripts/setup.sh
source .venv/bin/activate
```

Creates a `.venv`, installs shAI into it, copies `.env.example` to `.env`, and walks you through picking a provider (and, for Ollama, pulling the default model). Use this if you're developing shAI itself.

### Manual install

```bash
pip install -e .
cp .env.example .env   # then fill in an API key if you're using Mistral/OpenAI
shai config set-provider ollama   # or mistral / openai
```

`.env` is gitignored — never commit real API keys. It's only for secrets and machine-specific settings (`MISTRAL_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_HOST`); your provider/model *preference* lives in a separate config file (see below), not `.env`. For a global install, secrets go in `~/.config/shai/.env` instead of a repo-local `.env`, so `shai` finds them no matter which directory you run it from.

## Usage

```bash
shai ask "show me all pdf files in the current directory"
shai ask "find large files created in the last week"
shai ask "update package lists and show what's upgradable"   # multi-step, runs as an ordered plan
```

Each request goes through four steps: query validation → command generation → safety check → confirm & execute. You'll see a spinner during each model call, the generated command(s) in a syntax-highlighted panel, and a `Run this command? [y/n]` prompt before anything executes — skipped automatically when every command in the plan is read-only (`ls`, `cat`, `ps`, `df`, ...).

Useful flags:

```bash
shai ask "..." --no-execute          # just show the command(s), don't run them
shai ask "..." -y                    # skip the confirmation prompt
shai ask "..." --verbose             # print each step's reasoning instead of a spinner
shai ask "..." --provider mistral --model mistral-large-latest   # one-off override
```

### Swapping models / providers

Your active provider and per-provider model are persisted in a small config file (`~/.config/shai/config.json`, override the location with `$SHAI_CONFIG_DIR`) — set them once and every `shai ask` uses them:

```bash
shai config show                             # see the active provider/model and where each is set
shai config set-provider mistral             # switch the default provider (ollama / mistral / openai)
shai config set-model mistral-large-latest   # set the model for the active provider
shai config set-model llama3.2 --provider ollama   # set a model for a specific provider
shai config path                             # print the config file location
```

A `--provider`/`--model` flag on `shai ask` always wins for that one call; otherwise shAI falls back to this config file, then to each provider's built-in default (`llama3.1:8b` for Ollama, `mistral-small-latest` for Mistral, `gpt-4o-mini` for OpenAI-compatible).

### History

Every `shai ask` is logged locally (`~/.local/share/shai/history.jsonl`, override with `$SHAI_DATA_DIR`):

```bash
shai history show               # most recent 20 requests
shai history show --limit 100
shai history clear
```

### Tab-completion

```bash
shai completion bash   # or zsh / fish
```

prints the exact line to add to your shell rc file to enable tab-completion for `shai` and its subcommands.

## Adding a new model provider

Providers implement a single interface: `llm.base.LLMProvider`, with one method, `chat(prompt, model=None) -> str`. To add one:

1. Create `src/llm/<name>_provider.py` implementing `LLMProvider`.
2. Register it in `PROVIDERS` in `src/llm/factory.py`.

No changes are needed in `src/agents/*` or the CLI — every agent calls `llm.get_provider(...)` and is unaware of which backend is in use, and `shai config set-provider <name>` picks up new entries in `PROVIDERS` automatically. The built-in `openai` provider already covers any OpenAI-compatible endpoint (Groq, Together, OpenRouter, local llama.cpp/LM Studio) via `$OPENAI_BASE_URL` — you may not need a new provider at all.

## Development

### Project Structure

- `src/llm/`: Model-agnostic provider interface (`base.py`), the `ollama`, `mistral`, and `openai`-compatible implementations, and the `factory.py` that selects one at runtime
- `src/config.py`: Persisted provider/model preference (`~/.config/shai/config.json`) and its precedence resolution
- `src/history.py`: Append-only local request history (`~/.local/share/shai/history.jsonl`)
- `src/agents/cmd_validator.py`: Validates if queries are appropriate for a shell assistant (rejects chit-chat and coding requests)
- `src/agents/cmd_safety.py`: Validates commands for safety, and flags read-only commands for auto-confirmation
- `src/agents/cmd_executor.py`: Executes validated commands
- `src/agents/cmd_generator.py`: Generates one or more shell commands from a query, aware of OS/shell/cwd
- `src/main.py`: CLI entry point (`shai ask`, `shai config ...`, `shai history ...`, `shai completion ...`) and terminal UI
- `scripts/setup.sh`: Local dev setup (venv)
- `scripts/install.sh` / `scripts/uninstall.sh`: Global install/uninstall (pipx)
- `tests/`: pytest suite (offline — LLM calls are mocked)

### Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
