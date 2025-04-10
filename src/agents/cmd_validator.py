"""
Agent to validate if a natural language query is appropriate for shell command generation.
This module checks if the query is conversational or if it can be converted to a shell command.
It uses a set of conversational patterns and a language model to determine the intent of the query.
"""
import re
import ollama
from rich.console import Console

console = Console()

def validate_query(query: str, verbose=False)-> tuple:
    """
    Validates if the query is appropriate for shell command generation.
    Returns a tuple of (is_valid, reason).
    
    Parameters:
    query (str): The natural language query to validate
    verbose (bool): Whether to show detailed information
    
    Returns:
    tuple: (is_valid, reason)
    """
    if not query or query.strip() == "":
        return False, "Empty query"
    
    # Check for conversational patterns that indicate chatbot usage
    conversational_patterns = [
        r"^(hi|hello|hey|greetings)",
        r"how are you",
        r"what's your name",
        r"who (are|created) you",
        r"tell me (about|a) joke",
        r"can you help me with (.+\?)",
        r"what do you think about",
        r"explain \w+ to me"
    ]
    
    for pattern in conversational_patterns:
        if re.search(pattern, query.lower()):
            if verbose:
                console.print(f"[yellow]Query detected as conversational based on pattern: {pattern}[/yellow]")
            return False, "This appears to be a conversational query rather than a shell command request"
    
    # Use LLM to evaluate if the query is appropriate for bash command generation
    try:
        if verbose:
            console.print("[yellow]Checking query intent with LLM...[/yellow]")
        
        prompt = f"""
        Determine if the following query is asking for a bash command or shell operation.
        ONLY respond with "YES" if the query is asking for a bash command or shell operation.
        Respond with "NO" if the query is seeking general information, conversation, or anything not suitable for bash command generation.
        
        Query: {query}
        
        Response (YES/NO):
        """
        
        response = ollama.chat(model='codellama', messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        result = response['message']['content'].strip().upper()
        
        if verbose:
            console.print(f"[yellow]LLM validation result: {result}[/yellow]")
        
        if "YES" in result:
            return True, "Query is valid for shell command generation"
        else:
            return False, "Query does not appear to be asking for a shell command"
            
    except Exception as e:
        if verbose:
            console.print(f"[red]Error during LLM validation: {str(e)}[/red]")
        # If LLM check fails, default to permissive behavior
        return True, "Query validation was inconclusive, proceeding with caution"