# shAI - The Intelligent Shell Assistant

shAI is a command line tool that allows you to use natural language to execute bash commands. Simply describe what you want to do, and shAI will generate and safely execute the appropriate commands.

## Features

- 🧠 Natural language to bash command translation
- 🔒 Command safety validation before execution
- 📋 Detailed execution results and error reporting
- 🌐 Runs locally using Ollama models

## Installation

### Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) with the `codellama` model

### Install from source

```bash
# Clone the repository
git clone https://github.com/your-username/shAI.git
cd shAI

# Install the package
pip install -e .
```

## Usage

Basic usage:

```bash
shai "your natural language query"
```

Examples:

```bash
shai "show me all pdf files in the current directory"
shai "find large files created in the last week"
shai "check memory and cpu usage"
```

## Development

### Project Structure

- `src/agents/cmd_safety.py`: Validates commands for safety
- `src/agents/cmd_executor.py`: Executes validated commands
- `src/main.py`: Entry point for the CLI

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License