import configparser
import ollama
import tokens.counter as counter

# Load configuration
config = configparser.ConfigParser()
config.read('config.cfg')

ai_model = config.get('DEFAULT', 'model').strip('"')
name = config.get('DEFAULT', 'name').strip('"')
sys_prompt = config.get('DEFAULT', 'sys_prompt').strip('"')
version = config.get('SYSTEM', 'ver').strip('"')
_token_limit_enabled = config.get('TOKEN_LIMIT', 'limit_user').strip('"')

# Get how many tokens were used
def mod_tokens(_user_identifier: str, user_input: str) -> None:
    if user_input:
        try:
            # Get token estimation - create simple messages for token counting
            messages = [{'role': 'user', 'content': user_input}]
            response = ollama.chat(model=config.get('DEFAULT', 'model'), messages=messages, options={"num_predict": 1})
            total_tokens = response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
            
            if _token_limit_enabled.lower() == "true":
                counter.add_tokens(_user_identifier, total_tokens)

def modTokens(user: str, user_input: str) -> None:
    """Backward-compatible alias for mod_tokens."""
    return mod_tokens(user, user_input)

def send(user_input: str) -> str:
    system_message = {
        'role': 'system',
        'content': f'You are {name}. {sys_prompt} Version: {version}. You are only allowed to speak with markdown formatting. Begin normal messages with ` and end them with `'
    }
    
    user_message = {
        'role': 'user',
        'content': user_input
    }
    
    messages = [system_message, user_message]
    
    try:
        response = ollama.chat(model=ai_model, messages=messages)
        return response['message']['content']
    except Exception as error:
        return f"Sorry, I encountered an error: {str(error)}"
