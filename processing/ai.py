import configparser
from ollama import chat

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
            response = chat(model=aimodel, messages=[{"role": "user", "content": user_input}])
            tokens = response.get('eval_count', 0)
            
            print(f"Tokens used: {tokens}")

            if token_limit.strip('"') == 'True':
                import login.server as logins
                current_tokens = logins.getTokens(user)  # Get user tokens
                if int(current_tokens) >= 1:
                    logins.setTokens(user, max(0, current_tokens - tokens))  # Prevent negative tokens
                else:
                    print("Oh Help me, your out of tokens!")
                    return response.get('message', {}).get('content', "Sorry, I can't answer that, it seems you are out of tokens.")


        except Exception as e:
            print(f"Error estimating tokens: {e}")

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
        response = chat(model=aimodel, messages=messages)
        return response.get('message', {}).get('content', 'Error: No response from AI')
    except Exception as e:
        print(f"Error in AI response: {e}")
        return "Error: AI failed to respond."
