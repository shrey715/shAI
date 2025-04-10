"""
This agent takes the input as a string which is the Natural Language command and then outputs bash command/s.
"""
import ollama
import sys

def generate_command(input: str, verbose: bool = False) -> str:
    """
    Generates bash command/s from the input string.
    
    Args:
        input (str): The input string.
        
    Returns:
        str: The generated bash command.
    """
    prompt = f"""
    You are a command generator agent. Your task is to generate a bash command based on the input string.
    The input string is: {input}
    
    IMPORTANT: Respond ONLY with the raw bash command, without any explanations, markdown formatting, or backticks.
    Do not include any other text in your response, just the executable command.
    """
    
    try:
        if verbose:
            print("Sending request to ollama model...")
        response = ollama.chat(
            model="codellama:latest", 
            messages=[{"role": "user", "content": prompt}]
        )
        
        if verbose:
            print("Response received from model.")
        command = response['message']['content'].strip()
        
        # Clean up the response
        if command.startswith("```bash") or command.startswith("```shell") or command.startswith("```"):
            lines = command.split("\n")
            command = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
        
        command = command.strip('`"\'')
        
        return command
    except Exception as e:
        print(f"Error generating command: {str(e)}", file=sys.stderr)
        return "echo 'Command generation failed'"

if __name__ == "__main__":
    input_string = "List all files in the current directory"
    print(f"Input: '{input_string}'")
    command = generate_command(input_string)
    print(f"Generated command: {command}")