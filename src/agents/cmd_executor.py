"""
This agent takes a list of commands to execute and executes them in order.
Upon successful execution, it returns a success statement else it returns a failure statement.
"""
import sys
import subprocess
from typing import Dict, List, Union

def execute_commands(commands: List[str], verbose: bool = False) -> Dict[str, Union[bool, List[Dict[str, Union[str, int]]]]]:
    """
    Executes a list of shell commands and returns the output.

    Args:
        commands (list): The list of commands to execute.
        verbose (bool): If True, prints the command before executing it.

    Returns:
        dict: A dictionary containing success status and detailed results for each command
    """
    if verbose:
        print(f"Executing commands: {commands}")
    
    results = []
    success = True
    
    try:
        for command in commands:
            if verbose:
                print(f"Executing command: {command}")
            
            process = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True
            )
            
            cmd_result = {
                "command": command,
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr
            }
            
            results.append(cmd_result)
            
            if process.returncode != 0:
                if verbose:
                    print(f"Command failed with exit code {process.returncode}")
                    print(f"Error: {process.stderr}")
                success = False
                # Continue executing the remaining commands even if one fails
    
    except Exception as e:
        if verbose:
            print(f"Error executing command: {str(e)}", file=sys.stderr)
        success = False
        results.append({
            "command": command if 'command' in locals() else "unknown",
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e)
        })
    
    return {
        "success": success,
        "results": results
    }

def format_results(execution_results: Dict) -> str:
    """
    Format the execution results into a readable string.
    
    Args:
        execution_results (dict): The execution results dictionary
        
    Returns:
        str: A formatted string with the results
    """
    if execution_results["success"]:
        output = "All commands executed successfully.\n\n"
    else:
        output = "Some commands failed during execution.\n\n"
    
    for i, result in enumerate(execution_results["results"]):
        output += f"Command {i+1}: {result['command']}\n"
        output += f"Exit code: {result['exit_code']}\n"
        
        if result["stdout"]:
            output += f"Output:\n{result['stdout']}\n"
        
        if result["stderr"]:
            output += f"Errors:\n{result['stderr']}\n"
        
        output += "-" * 50 + "\n"
    
    return output

if __name__ == "__main__":
    commands = ["echo 'Hello World'", "ls -la", "cat non_existent_file"]  # Example commands to execute
    print(f"Commands: {commands}")
    execution_results = execute_commands(commands, verbose=True)
    print(format_results(execution_results))