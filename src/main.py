from datetime import datetime, timezone

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

import config
import history
from agents.cmd_generator import generate_commands
from agents.cmd_safety import validate_command, explain_command_risk, is_read_only_command
from agents.cmd_executor import execute_commands
from agents.cmd_validator import validate_query
from llm import PROVIDERS

THEME = Theme({
    "shai.title": "bold cyan",
    "shai.subtitle": "italic dim",
    "shai.label": "bold",
    "shai.muted": "dim",
    "shai.success": "bold green",
    "shai.error": "bold red",
    "shai.warning": "bold yellow",
})

console = Console(theme=THEME)

TOTAL_STEPS = 4


def step(n: int, label: str) -> None:
    console.print(f"\n[shai.label][{n}/{TOTAL_STEPS}][/shai.label] {label}")


def run_step(label: str, show_spinner: bool, fn, *args, **kwargs):
    """Runs fn with a spinner, unless verbose mode is already printing its own progress."""
    if not show_spinner:
        return fn(*args, **kwargs)
    with console.status(f"[shai.muted]{label}[/shai.muted]", spinner="dots"):
        return fn(*args, **kwargs)


@click.group()
def cli():
    """shAI - a natural-language shell assistant (not a coding assistant)."""


@cli.command()
@click.argument("query")
@click.option("--execute/--no-execute", default=True, help="Execute the command(s) or just show them")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip the confirmation prompt before executing")
@click.option("--verbose/--no-verbose", default=False, help="Show verbose output")
@click.option(
    "--provider",
    default=None,
    type=click.Choice(sorted(PROVIDERS), case_sensitive=False),
    help="LLM provider to use. Defaults to the configured provider (see 'shai config show').",
)
@click.option("--model", default=None, help="Model to use (defaults to the provider's configured/default model)")
@click.option("--safety-threshold", default=0.75, type=float, help="Safety confidence threshold (0-1)")
def ask(query, execute, yes, verbose, provider, model, safety_threshold):
    """
    Convert a natural language QUERY into one or more shell commands and (optionally) run them.
    """
    provider = config.resolve_provider(provider)
    model = config.resolve_model(model, provider)

    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "provider": provider,
        "model": model,
        "status": "unknown",
    }

    try:
        console.print(Panel("[shai.title]shAI[/shai.title] [shai.subtitle]- turning your words into shell commands[/shai.subtitle]"))
        console.print(f"Query: [yellow]{query}[/yellow]")
        console.print(f"Provider: [cyan]{provider}[/cyan]" + (f"  Model: [cyan]{model}[/cyan]" if model else "  Model: [shai.muted](provider default)[/shai.muted]"))

        # Step 1: Validate the query is appropriate for command generation
        step(1, "Validating query...")
        is_valid, reason = run_step(
            "Validating query...", not verbose, validate_query, query, verbose=verbose, provider=provider, model=model
        )

        if not is_valid:
            record["status"] = "invalid_query"
            console.print(f"[shai.error]⚠ Invalid query:[/shai.error] {reason}")
            console.print("[shai.subtitle]shAI only handles shell/system tasks — try describing a file, process, or system operation.[/shai.subtitle]")
            return

        console.print("[shai.success]✓ Query is valid for command generation[/shai.success]")

        # Step 2: Generate the command(s)
        step(2, "Generating command...")
        commands = run_step(
            "Generating command...", not verbose, generate_commands, query, verbose=verbose, provider=provider, model=model
        )
        record["commands"] = commands

        title = "Generated command" if len(commands) == 1 else f"Generated commands ({len(commands)} steps)"
        console.print(Panel(Syntax("\n".join(commands), "bash", theme="monokai", word_wrap=True), title=title, title_align="left", border_style="cyan"))

        # Step 3: Validate every command for safety, stop at the first unsafe one
        step(3, "Validating command safety...")

        def validate_all():
            results = []
            for cmd in commands:
                result = validate_command(
                    cmd, verbose=verbose, provider=provider, model=model,
                    get_explanation=True, confidence_threshold=safety_threshold,
                )
                results.append(result)
                if not result["is_safe"]:
                    break
            return results

        safety_results = run_step("Validating command safety...", not verbose, validate_all)

        unsafe_index = next((i for i, r in enumerate(safety_results) if not r["is_safe"]), None)
        if unsafe_index is not None:
            bad_command = commands[unsafe_index]
            result = safety_results[unsafe_index]
            record["status"] = "unsafe"
            console.print("[shai.error]⚠ Command may be unsafe! Execution aborted.[/shai.error]")
            console.print(f"[shai.muted]Command:[/shai.muted] {bad_command}")
            if result.get("explanation"):
                console.print(f"[shai.warning]Reason:[/shai.warning] {result['explanation']}")

            if verbose:
                console.print("\n[shai.label]Detailed risk analysis:[/shai.label]")
                risk_details = explain_command_risk(bad_command, provider=provider, model=model)
                console.print(Panel(risk_details, title="Risk analysis", border_style="red"))
            else:
                console.print("[shai.subtitle]Use --verbose for detailed risk analysis[/shai.subtitle]")
            return

        avg_confidence = sum(r["confidence"] for r in safety_results) / len(safety_results)
        console.print(f"[shai.success]✓ Command{'s' if len(commands) > 1 else ''} passed safety check[/shai.success] [shai.muted](confidence: {avg_confidence:.2f})[/shai.muted]")

        # Step 4: Execute if requested
        if not execute:
            record["status"] = "not_executed"
            console.print("\n[shai.subtitle]Command not executed (--no-execute flag was used)[/shai.subtitle]")
            return

        all_read_only = all(is_read_only_command(c) for c in commands)
        if not yes:
            if all_read_only:
                console.print("\n[shai.muted]All commands are read-only — running automatically.[/shai.muted]")
            elif not Confirm.ask("\n[shai.label]Run this command?[/shai.label]" if len(commands) == 1 else "\n[shai.label]Run these commands?[/shai.label]", default=True, console=console):
                record["status"] = "aborted"
                console.print("[shai.subtitle]Aborted — command not executed.[/shai.subtitle]")
                return

        step(4, "Executing command..." if len(commands) == 1 else "Executing commands...")
        execution_results = execute_commands(commands, verbose=verbose)

        record["status"] = "executed"
        record["success"] = execution_results["success"]
        record["exit_codes"] = [r["exit_code"] for r in execution_results["results"]]

        if execution_results["success"]:
            console.print("[shai.success]✓ Command executed successfully[/shai.success]" if len(commands) == 1 else "[shai.success]✓ All commands executed successfully[/shai.success]")
        else:
            console.print("[shai.error]✗ Command execution failed[/shai.error]" if len(commands) == 1 else "[shai.error]✗ One or more commands failed[/shai.error]")

        for result in execution_results["results"]:
            if result["stdout"]:
                console.print(Panel(result["stdout"].rstrip(), title=f"Output — {result['command']}", title_align="left", border_style="green"))
            if result["stderr"]:
                console.print(Panel(result["stderr"].rstrip(), title=f"Errors — {result['command']}", title_align="left", border_style="red"))
    finally:
        history.append(record)


@cli.group(name="config")
def config_group():
    """View or change the active provider/model."""


@config_group.command(name="show")
def config_show():
    """Show the effective provider/model and where they're set."""
    cfg = config.load_config()
    active_provider = config.resolve_provider(None)
    active_model = config.resolve_model(None, active_provider)

    table = Table(title="shAI configuration", show_header=True, header_style="shai.label")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("Active provider", f"[cyan]{active_provider}[/cyan]")
    table.add_row("Active model", active_model or "[shai.muted](provider default)[/shai.muted]")
    table.add_row("Config file", f"{config.CONFIG_FILE}" + ("" if config.CONFIG_FILE.exists() else " [shai.muted](not created yet)[/shai.muted]"))
    for name in sorted(PROVIDERS):
        override = cfg.get("models", {}).get(name)
        table.add_row(f"  {name} model override", override or "[shai.muted]—[/shai.muted]")

    console.print(table)


@config_group.command(name="set-provider")
@click.argument("provider_name", type=click.Choice(sorted(PROVIDERS), case_sensitive=False))
def config_set_provider(provider_name):
    """Set the default provider (e.g. 'ollama' or 'mistral')."""
    provider_name = provider_name.lower()
    config.set_provider(provider_name)
    console.print(f"[shai.success]✓ Default provider set to '{provider_name}'[/shai.success]")


@config_group.command(name="set-model")
@click.argument("model_name")
@click.option(
    "--provider",
    default=None,
    type=click.Choice(sorted(PROVIDERS), case_sensitive=False),
    help="Provider to set the model for (defaults to the active provider)",
)
def config_set_model(model_name, provider):
    """Set the default model for a provider."""
    target = (provider or config.resolve_provider(None)).lower()
    config.set_model(target, model_name)
    console.print(f"[shai.success]✓ Default model for '{target}' set to '{model_name}'[/shai.success]")


@config_group.command(name="path")
def config_path():
    """Print the path to the config file."""
    console.print(str(config.CONFIG_FILE))


@cli.group(name="history")
def history_group():
    """View or clear your shai request history."""


@history_group.command(name="show")
@click.option("--limit", default=20, show_default=True, help="Number of most recent entries to show")
def history_show(limit):
    """Show past shai requests."""
    entries = history.load(limit=limit)
    if not entries:
        console.print("[shai.muted]No history yet.[/shai.muted]")
        return

    table = Table(title="shAI history", show_header=True, header_style="shai.label")
    table.add_column("Time")
    table.add_column("Provider")
    table.add_column("Query")
    table.add_column("Command(s)")
    table.add_column("Status")
    for entry in entries:
        table.add_row(
            (entry.get("time") or "")[:19].replace("T", " "),
            entry.get("provider") or "",
            entry.get("query") or "",
            "; ".join(entry.get("commands") or []),
            entry.get("status") or "",
        )
    console.print(table)


@history_group.command(name="clear")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip the confirmation prompt")
def history_clear(yes):
    """Delete all stored history."""
    if not yes and not Confirm.ask("Clear all shAI history?", default=False, console=console):
        console.print("[shai.subtitle]Aborted.[/shai.subtitle]")
        return
    history.clear()
    console.print("[shai.success]✓ History cleared[/shai.success]")


@cli.command(name="completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell):
    """Print the shell snippet to enable tab-completion for shai."""
    if shell == "fish":
        line = "_SHAI_COMPLETE=fish_source shai | source"
        rc = "~/.config/fish/config.fish"
    else:
        line = f'eval "$(_SHAI_COMPLETE={shell}_source shai)"'
        rc = "~/.bashrc" if shell == "bash" else "~/.zshrc"

    console.print(f"[shai.muted]# Add this line to {rc}, then restart your shell:[/shai.muted]")
    console.print(line)


if __name__ == "__main__":
    cli()
