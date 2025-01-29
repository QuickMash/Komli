from ollama import chat
from ollama import ChatResponse

def send(user_input: str) -> str:
    # System Message
    system_message = {
        'role': 'system',
        'content': 'You are a friendly assistant, named Komli. You are not powered by Alibaba Cloud'
    }
    # Define the user
    user_message = {
        'role': 'user',
        'content': user_input
    }
    messages = [system_message, user_message]
    response = chat(model='qwen:0.5b', messages=messages)
    return response.message.content
