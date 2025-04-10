"""
This agent takes the bash command as input and verifies the safety of the command.
It checks if the command contains any dangerous or potentially harmful operations.
It also checks if the command is a valid bash command.
"""
import ollama 
import sys

def validate_command(command: str, verbose: bool = False) -> bool:
    """
    Validates the bash command to check if it is safe to execute.
    
    Args:
        command (str): The bash command to validate.
        
    Returns:
        bool: True if the command is safe, False otherwise.
    """
    prompt = f"""
    You are a command safety agent. Your task is to validate the bash command for safety and you return True or False for Safety being True and Not Safe being False.
    The command is: {command}
    IMPORTANT: Respond ONLY with True or False, without any explanations, markdown formatting, or backticks.
    """   
    
    try:
        if verbose:
            print("Sending request to ollama model for command validation...")
        
        response = ollama.chat(
            model="codellama:latest", 
            messages=[{"role": "user", "content": prompt}]
        )
        safety_response = response['message']['content'].strip()
        
        if verbose:
            print("Response received from model for command validation: ", safety_response)
        
        # Clean up the response
        if safety_response.startswith("```bash") or safety_response.startswith("```shell") or safety_response.startswith("```"):
            lines = safety_response.split("\n")
            safety_response = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
        
        safety_response = safety_response.strip('`"\'')
        
        return safety_response.lower() == 'true'
    except Exception as e:
        print(f"Error validating command: {str(e)}", file=sys.stderr)
        return False
    
if __name__ == "__main__":
    commands = [
        "rm -rf /",
        "ls -l",
        "echo 'Hello, World!'",
        "cat /etc/passwd",
        "curl http://example.com"
    ]
    
    for command in commands:
        is_safe = validate_command(command, verbose=True)
        print(f"Command: {command} - Safe: {is_safe}")