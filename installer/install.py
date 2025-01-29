import os
import requests
import time

name = os.name
install_ollama = None
config = {}
version = "0.1.0"

def ollama_getValue():
    global install_ollama
    install_ollama = input("Do you want to install Ollama? [Yes]/No ").strip().lower()
    if install_ollama in ["yes", ""]:
        install_ollama = True
    elif install_ollama == "no":
        print("Ollama is required to run, make sure it is installed before running Komli")
        install_ollama = False
    else:
        print("Unknown Input, try again")
        ollama_getValue()

def askconfig():
    global config
    print("Config")
    config['webdir'] = input("Enter the web directory you want to host from? Default is [/] ").strip() or '/'
    config['ai_name'] = input("Enter the name for your assistant? Default is [Komli] ").strip() or 'Komli'
    config['model'] = input("Enter the name of the model you want to use? Default is [qwen:0.5b] ").strip() or 'qwen:0.5b'
    config['sys_prompt'] = input("Enter the system prompt? Default is [You are a friendly assistant] ").strip() or 'You are a friendly assistant'
    ollama_getValue()
    if input("Save Config? [Yes]/No ").strip().lower() in ["yes", ""]:
        setConfig()

def setConfig():
    global config
    config_file = 'config.cfg'
    with open(config_file, 'w') as f:
        f.write(f'name = "{config["ai_name"]}" # Assistant Name\n')
        f.write(f'webdir = "{config["webdir"]}" # The Web Directory\n')
        f.write(f'model = "{config["model"]}" # AI Model to use\n')
        f.write(f'system_prompt = "{config["sys_prompt"]}" # System Prompt\n')
        f.write(f'version = "{version}" # Do not Change\n')
    print(f'Configuration saved to {config_file}')

if name == "nt":
    os.system("cls")
    print("Welcome to the Windows Komli Installer!")
    askconfig()
    if install_ollama:
        file_path = "OllamaSetup.exe"
        response = requests.get("https://ollama.com/download/OllamaSetup.exe")
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print('File downloaded successfully')
            time.sleep(0.5)
            print("Installing...")
            os.system("OllamaSetup.exe")
            setConfig()
        else:
            print('Failed to download file, try again later...')
            quit()
else:
    os.system("clear")
    print("Welcome to the Unix/Linux/Mac Komli Installer!")
    askconfig()
    if install_ollama:
        print("Installing Ollama")
        os.system("curl -fsSL https://ollama.com/install.sh | sh")
