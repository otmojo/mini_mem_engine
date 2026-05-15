import os
import json
import logging
from openai import OpenAI, APIError
from dotenv import load_dotenv
import sandbox

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Validate API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "sk-your-api-key-here" or api_key == "your_api_key_here":
    logger.warning("OPENAI_API_KEY not configured properly. Agent features will not work.")
    api_key = None

client = OpenAI(api_key=api_key) if api_key else None

# Define the tools available to the agent
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "exec_command",
            "description": "Execute a shell command in the secure sandbox",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run, e.g., 'ls -la' or 'python3 --version'",
                    }
                },
                "required": ["command"],
            },
        },
    }
]

def run_agent(user_prompt: str, container_id: str):
    """Run the AI agent to solve a task using the sandbox."""
    
    if not client:
        return "Error: OPENAI_API_KEY is not configured. Please set it in .env file."
    
    if not user_prompt or len(user_prompt.strip()) == 0:
        return "Error: Prompt cannot be empty."
    
    try:
        logger.info(f"Starting agent with prompt: {user_prompt}")
        
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant that can execute commands in a secure sandbox to help users. "
                          "Always verify the results of your commands and provide clear feedback. "
                          "Be cautious with system commands."
            },
            {"role": "user", "content": user_prompt}
        ]

        # Initial call to get tool usage
        logger.debug("Calling OpenAI API for initial response...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            logger.info(f"Agent will use {len(tool_calls)} tool calls")
            messages.append(response_message)
            
            for i, tool_call in enumerate(tool_calls):
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "exec_command":
                    command = function_args.get('command', '')
                    logger.info(f"[Tool Call {i+1}] Executing: {command}")
                    
                    try:
                        result = sandbox.exec_cmd(container_id, command)
                        logger.debug(f"Command result: {result}")
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(result)
                        })
                    except Exception as e:
                        logger.error(f"Error executing command: {e}")
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps({"error": str(e), "exit_code": 1})
                        })

            # Final call to summarize
            logger.debug("Calling OpenAI API for final response...")
            final_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            final_content = final_response.choices[0].message.content
            logger.info("Agent completed successfully")
            return final_content
        
        # No tool calls needed, return direct response
        content = response_message.content
        logger.info("Agent returned direct response without tool calls")
        return content
        
    except APIError as e:
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error in tool arguments: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error in agent: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    # Example usage (requires API key and running docker)
    # container = sandbox.create_sandbox()
    # print(run_agent("List all files in the current directory", container["id"]))
    # sandbox.destroy_sandbox(container["id"])
    pass
