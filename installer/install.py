import os
import requests
import time

name = os.name
install_ollama = None

def ollama_getValue():
    global install_ollama
    install_ollama = input("Do you want to install ollama? [Yes]/No ").rstrip()
    if install_ollama.lower() == "yes":
        install_ollama = True
    elif install_ollama.lower() == "no":
        print("Ollama is required to run, make sure it is installed before running Komli")
        install_ollama = False
    elif install_ollama == "":
        install_ollama = True
    else:
        print("Unknown Input, try again")
        ollama_getValue()

def askconfig():
    print("Config")
    webroot = input("Enter the webroot you want to host from? Default is [/] ").rstrip()
    ai_name = input("Enter the name for your assistant? Default is [Komli] ").rstrip()
    sys_prompt = input("Enter the system prompt? Default is [You are a friendly assistant] ").rstrip()
    ollama_getValue()

if name == "nt":
    os.system("cls")
    print("Welcome to the Windows Komli Installer!")
    askconfig()
    if install_ollama:
        file_path = "OllamaSetup.exe"  # Define the file path
        response = requests.get("https://ollama.com/download/OllamaSetup.exe")
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print('File downloaded successfully')
            time.sleep(.5)
            print("Installing...")
            os.system("OllamaSetup.exe")
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
