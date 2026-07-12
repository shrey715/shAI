"""
This agent takes the input as a string which is the Natural Language command and then outputs
one or more bash commands, in order, tailored to the current OS/shell.
"""
import os
import platform
import re
from typing import List, Optional

from rich.console import Console

from llm import get_provider, LLMError

console = Console()
err_console = Console(stderr=True)


def _environment_context() -> str:
    shell = os.path.basename(os.environ.get("SHELL", "sh"))
    return f"OS: {platform.system()} ({platform.machine()}), shell: {shell}, cwd: {os.getcwd()}"


def generate_commands(input: str, verbose: bool = False, provider: Optional[str] = None, model: Optional[str] = None) -> List[str]:
    """
    Generates one or more bash commands from the input string, in execution order.

    Args:
        input (str): The input string.
        verbose (bool): Whether to print verbose output.
        provider (str): The LLM provider to use (e.g. "ollama", "mistral"). Defaults to SHAI_PROVIDER env var.
        model (str): The model to use. Defaults to the provider's default model.

    Returns:
        List[str]: The generated command(s), in the order they should run.
    """
    prompt = f"""
    ROLE
    You are shAI, a shell assistant — not a general-purpose coding assistant. Your only job is to
    translate the request below into shell command(s) that accomplish it.

    ENVIRONMENT
    {_environment_context()}

    RULES
    1. Use standard command-line utilities (ls, find, grep, awk, sed, tar, ps, df, du, systemctl,
       curl, git, package managers, mkdir, touch, mv, cp, etc), tailored to the environment above
       (e.g. prefer GNU-flag syntax on Linux, BSD-flag syntax on macOS).
    2. If the task needs multiple sequential steps, output one command per line, in the order they
       should run. If a single command suffices, output just that one line.
    3. Creating, renaming, moving, or organizing files — including files with a programming-language
       extension (e.g. "create three empty .py files") — is a normal shell task: use mkdir/touch/mv/cp.
    4. If the user explicitly asks for specific file *content*, you may write it inline via shell
       redirection (echo/printf/heredoc), but never design, expand, or add logic beyond exactly what
       was asked.
    5. Never produce a multi-file software project, never add commentary or markdown, and never wrap
       the output in backticks.
    6. If the request truly falls outside a shell assistant's scope (e.g. it asks you to design or
       explain a program rather than run a shell task), respond with exactly:
       echo 'shAI: this request is outside the scope of a shell assistant'

    EXAMPLES
    Request: "list files modified in the last day"
    Output:
    find . -mtime -1

    Request: "create an empty file called notes.py inside a new folder called scratch"
    Output:
    mkdir -p scratch
    touch scratch/notes.py

    Request: "write a python script that sorts a list"
    Output:
    echo 'shAI: this request is outside the scope of a shell assistant'

    REQUEST
    {input}

    IMPORTANT: Respond ONLY with the raw command(s), one per line. No numbering, no markdown
    formatting, no backticks, no explanations.
    """

    try:
        llm = get_provider(provider)
        if verbose:
            console.print(f"[dim]Sending request to {llm.__class__.__name__}...[/dim]")
        response = llm.chat(prompt, model=model)

        if verbose:
            console.print("[dim]Response received from model.[/dim]")

        text = response.strip()

        # Strip an outer ```...``` fence if the whole response is wrapped in one
        if text.startswith("```"):
            lines = text.split("\n")
            closing = len(lines) > 2 and lines[-1].strip().startswith("```")
            text = "\n".join(lines[1:-1] if closing else lines[1:])

        commands = []
        for line in text.split("\n"):
            line = line.strip().strip('`"\'')
            line = re.sub(r"^\d+[\.\)]\s*", "", line)  # drop stray "1. " numbering
            if line:
                commands.append(line)

        return commands or ["echo 'Command generation failed'"]
    except LLMError as e:
        err_console.print(f"[red]Error generating command: {e}[/red]")
        return ["echo 'Command generation failed'"]

if __name__ == "__main__":
    input_string = "List all files in the current directory"
    print(f"Input: '{input_string}'")
    commands = generate_commands(input_string)
    print(f"Generated command(s): {commands}")
