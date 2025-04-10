import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from agents.cmd_generator import generate_command
from agents.cmd_safety import validate_command
from agents.cmd_executor import execute_commands, format_results

console = Console()

@click.command()
@click.argument("query")
@click.option("--execute/--no-execute", default=True, help="Execute the command or just show it")
@click.option("--verbose/--no-verbose", default=False, help="Show verbose output")
def main(query, execute, verbose):
    """
    shAI - Convert natural language to bash commands and execute them.
    
    QUERY is the natural language query to convert to a bash command.
    """
    console.print(Panel(f"[bold blue]shAI[/bold blue] - [italic]Converting your query to bash[/italic]"))
    console.print(f"Query: [yellow]{query}[/yellow]")
    
    # Step 1: Generate the command
    console.print("\n[bold]Generating command...[/bold]")
    command = generate_command(query, verbose=verbose)
    syntax = Syntax(command, "bash", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    # Step 2: Validate the command for safety
    console.print("\n[bold]Validating command safety...[/bold]")
    is_safe = validate_command(command, verbose=verbose)
    
    if not is_safe:
        console.print("[bold red]⚠️  Command may be unsafe! Execution aborted.[/bold red]")
        return
    
    console.print("[bold green]✓ Command passed safety check[/bold green]")
    
    # Step 3: Execute the command if requested
    if execute:
        console.print("\n[bold]Executing command...[/bold]")
        execution_results = execute_commands([command], verbose=verbose)
        
        if execution_results["success"]:
            console.print("[bold green]✓ Command executed successfully[/bold green]")
        else:
            console.print("[bold red]✗ Command execution failed[/bold red]")
        
        # Show output
        for result in execution_results["results"]:
            if result["stdout"]:
                console.print("\n[bold]Output:[/bold]")
                console.print(result["stdout"])
            
            if result["stderr"]:
                console.print("\n[bold red]Errors:[/bold red]")
                console.print(result["stderr"])
    else:
        console.print("\n[italic]Command not executed (--no-execute flag was used)[/italic]")

if __name__ == "__main__":
    main()
