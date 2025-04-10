import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from agents.cmd_generator import generate_command
from agents.cmd_safety import validate_command, explain_command_risk
from agents.cmd_executor import execute_commands, format_results
from agents.cmd_validator import validate_query

console = Console()

@click.command()
@click.argument("query")
@click.option("--execute/--no-execute", default=True, help="Execute the command or just show it")
@click.option("--verbose/--no-verbose", default=False, help="Show verbose output")
@click.option("--model", default="codellama:latest", help="Model to use for validation")
@click.option("--safety-threshold", default=0.75, type=float, help="Safety confidence threshold (0-1)")
def main(query, execute, verbose, model, safety_threshold):
    """
    shAI - Convert natural language to bash commands and execute them.
    
    QUERY is the natural language query to convert to a bash command.
    """
    console.print(Panel(f"[bold blue]shAI[/bold blue] - [italic]Converting your query to bash[/italic]"))
    console.print(f"Query: [yellow]{query}[/yellow]")
    
    # Step 1: Validate the query is appropriate for command generation
    console.print("\n[bold]Validating query...[/bold]")
    is_valid, reason = validate_query(query, verbose=verbose)
    
    if not is_valid:
        console.print(f"[bold red]⚠️  Invalid query: {reason}[/bold red]")
        console.print("[italic]Please provide a query related to shell operations or commands.[/italic]")
        return
    
    console.print("[bold green]✓ Query is valid for command generation[/bold green]")
    
    # Step 2: Generate the command
    console.print("\n[bold]Generating command...[/bold]")
    command = generate_command(query, verbose=verbose)
    syntax = Syntax(command, "bash", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    # Step 3: Validate the command for safety
    console.print("\n[bold]Validating command safety...[/bold]")
    safety_result = validate_command(
        command, 
        verbose=verbose, 
        model=model, 
        get_explanation=True,
        confidence_threshold=safety_threshold
    )
    
    if not safety_result['is_safe']:
        console.print(f"[bold red]⚠️  Command may be unsafe! Execution aborted.[/bold red]")
        if 'explanation' in safety_result and safety_result['explanation']:
            console.print(f"[bold yellow]Reason:[/bold yellow] {safety_result['explanation']}")
            
        if verbose:
            console.print("\n[bold]Detailed risk analysis:[/bold]")
            risk_details = explain_command_risk(command, model=model)
            console.print(Panel(risk_details, title="Risk Analysis", border_style="red"))
        else:
            console.print("[italic]Use --verbose for detailed risk analysis[/italic]")
        return
    
    console.print(f"[bold green]✓ Command passed safety check (confidence: {safety_result['confidence']:.2f})[/bold green]")
    
    # Step 4: Execute the command if requested
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
