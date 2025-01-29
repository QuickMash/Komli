from ollama import chat
from ollama import ChatResponse
import json

aimodel = "qwen:0.5b"

def configure(name, webdir, aimodel, sys_prompt, version):
    print(name, webdir, aimodel, sys_prompt, version)

def send(user_input: str, name: str, sys_prompt: str, version: str) -> str:
    # System Message
    system_message = {
        'role': 'system',
        'content': 'You are a friendly assistant, named {}. {}. You are powered by Komni {}.'.format(name, sys_prompt, version)
    }
    # Define the user
    user_message = {
        'role': 'user',
        'content': user_input
    }
    messages = [system_message, user_message]
    response = chat(model=aimodel, messages=messages)
    
    # Ensure the response is in JSON forma
    
    return response.message.content
