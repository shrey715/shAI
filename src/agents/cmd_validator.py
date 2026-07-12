"""
Agent to validate if a natural language query is appropriate for shell command generation.
This module checks if the query is conversational or if it can be converted to a shell command.
It uses a set of conversational patterns and a language model to determine the intent of the query.
"""
import re
from typing import Optional

from rich.console import Console

from llm import get_provider, LLMError

console = Console()

def validate_query(query: str, verbose: bool = False, provider: Optional[str] = None, model: Optional[str] = None) -> tuple:
    """
    Validates if the query is appropriate for shell command generation.
    Returns a tuple of (is_valid, reason).

    Parameters:
    query (str): The natural language query to validate
    verbose (bool): Whether to show detailed information
    provider (str): The LLM provider to use (e.g. "ollama", "mistral"). Defaults to SHAI_PROVIDER env var.
    model (str): The model to use. Defaults to the provider's default model.

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

    # shAI is a shell assistant, not a general coding assistant — reject requests to write
    # source code in another language, as opposed to a shell/bash command or script.
    coding_patterns = [
        r"\b(write|create|generate)\s+(a|an|some)?\s*"
        r"(python|javascript|typescript|java|c\+\+|c#|rust|golang?|ruby|php|swift|kotlin|sql)\s+"
        r"(script|program|function|class|code|app|application|snippet)\b",
        r"\bhow (do|would|can) i (code|program) (a|an)\b",
    ]

    for pattern in coding_patterns:
        if re.search(pattern, query.lower()):
            if verbose:
                console.print(f"[yellow]Query detected as a coding request based on pattern: {pattern}[/yellow]")
            return False, "shAI is a shell assistant, not a general coding assistant — it only handles shell/system tasks"

    # Use LLM to evaluate if the query is appropriate for bash command generation
    try:
        if verbose:
            console.print("[yellow]Checking query intent with LLM...[/yellow]")

        prompt = f"""
        ROLE
        You are the query classifier for shAI, a natural-language shell assistant. You decide
        whether a user's request belongs in the "shell task" lane (gets turned into a command) or
        should be rejected before any command is generated.

        TASK
        Decide whether the query below can be satisfied with a shell/bash command or short
        pipeline of standard command-line utilities: file/directory management (mkdir, touch, mv,
        cp, rm), process/system info, search, networking, package management, git, permissions,
        archiving, and similar.

        KEY DISTINCTION
        Creating, renaming, moving, copying, or organizing files IS a valid shell task, even when
        those files have a programming-language extension or name — e.g. "create three empty .py
        files in a new folder" is just mkdir/touch, not coding. Only classify as NO when the query
        asks you to write the actual source code / logic / content of a program in a non-shell
        language, or is general conversation/information-seeking with no shell task in it at all.

        EXAMPLES
        - "list all files larger than 100MB"                          -> YES
        - "create three empty .py files inside a new folder"          -> YES
        - "check how much disk space is free"                         -> YES
        - "compress this folder into a tar.gz archive"                -> YES
        - "write a python script that sorts a list"                   -> NO
        - "what's the capital of France"                               -> NO
        - "explain how git rebase works"                               -> NO

        QUERY
        {query}

        Respond with exactly one word: YES or NO.
        """
        
        llm = get_provider(provider)
        result = llm.chat(prompt, model=model).strip().upper()

        if verbose:
            console.print(f"[yellow]LLM validation result: {result}[/yellow]")

        if "YES" in result:
            return True, "Query is valid for shell command generation"
        else:
            return False, "Query does not appear to be asking for a shell command"

    except LLMError as e:
        if verbose:
            console.print(f"[red]Error during LLM validation: {str(e)}[/red]")
        # If LLM check fails, default to permissive behavior
        return True, "Query validation was inconclusive, proceeding with caution"