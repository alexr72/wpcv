# modules/dispatcher/conversation_dispatcher.py

from modules.logger.logger import log_conversation

def dispatch_conversation(agent_name, prompt, context=None):
    """
    Routes a prompt to the appropriate agent and logs the exchange.
    
    Args:
        agent_name (str): Identifier for the agent (e.g., 'validator', 'summarizer').
        prompt (str): The input string to process.
        context (dict, optional): Additional context or metadata.
    
    Returns:
        dict: Response object with timestamp, agent, and output.
    """
    # Placeholder response logic
    response = {
        "timestamp": "2025-08-15T15:22:00Z",
        "agent": agent_name,
        "prompt": prompt,
        "response": f"[{agent_name}] received: {prompt}"
    }

    # Log the conversation
    log_conversation(response)

    return response
