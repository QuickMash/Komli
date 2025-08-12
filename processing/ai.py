import configparser
import ollama

# Load configuration
config = configparser.ConfigParser()
config.read('config.cfg')

aimodel = config.get('DEFAULT', 'model').strip('"')
name = config.get('DEFAULT', 'name').strip('"')
sys_prompt = config.get('DEFAULT', 'sys_prompt').strip('"')
version = config.get('SYSTEM', 'ver').strip('"')
token_limit = config.get('TOKEN_LIMIT', 'limit_user').strip('"')

# Get how many tokens were used
def modTokens(user: str, user_input: str) -> None:
    if user_input:
        try:
            # Get token estimation - create simple messages for token counting
            messages = [{'role': 'user', 'content': user_input}]
            response = ollama.chat(model=config.get('DEFAULT', 'model'), messages=messages, options={"num_predict": 1})
            tokens = response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
            
            if config.getboolean('TOKEN_LIMIT', 'limit_user'):
                if tokens > int(config.get('TOKEN_LIMIT', 'daily_tokens')):
                    if config.getboolean('TOKEN_LIMIT', 'token_reset'):
                        return "You've exceeded your daily token limit."
                    else:
                        return "You don't have enough tokens for this request."
        except Exception as e:
            pass  # Continue without token estimation if it fails

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
        response = ollama.chat(model=aimodel, messages=messages)
        return response['message']['content']
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"
