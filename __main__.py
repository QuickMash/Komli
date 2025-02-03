import os
import signal
import time
import threading
from flask import Flask, request, render_template, jsonify
from markupsafe import Markup  # For safe HTML rendering
import processing.ai as ai
import processing.mdprocessor as md

# Load configuration from 'config.cfg'
config = {}
with open('config.cfg') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):  # Skip empty or comment lines
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.split('#', 1)[0].strip().strip('"')
            config[key] = value

# Validate required configuration keys
required_keys = ['name', 'webdir', 'model', 'system_prompt', 'version', 'markdown']
for key in required_keys:
    if key not in config:
        raise ValueError(f"Missing required config key: {key}")

# Configure AI based on the loaded settings
ai.configure(config['name'], config['webdir'], config['model'], config['system_prompt'], config['version'])

# Initialize Flask app
app = Flask(__name__)

# Event to stop the application gracefully
stop_event = threading.Event()

# Signal handler for clean shutdown
def handle_signal(signum, frame):
    stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# Home route
@app.route(config["webdir"])
def home():
    return render_template('index.html')

# Response route for processing user input
@app.route('/respond', methods=['POST'])
def respond():
    user_input = request.form.get('user_input')
    
    # Get AI's response to the user's input
    system_response = ai.send(user_input, config['name'], config['system_prompt'], config['version'])
    
    # Convert the AI's Markdown response to HTML
    markdown_response = md.convert(system_response)
    
    # Safely render the converted HTML in the template
    return Markup(f'Komli: {markdown_response}')

# Start the Flask app and Ollama server in separate threads
if __name__ == '__main__':
    os.system("clear")
    time.sleep(0.5)

    # Function to start Flask app
    def start_app():
        app.run(debug=True, use_reloader=False)

    # Run Flask app in a separate thread to avoid blocking
    app_thread = threading.Thread(target=start_app)
    app_thread.start()

    try:
        # Start the Ollama server
        print("Starting Ollama...")
        os.system("ollama serve")
    finally:
        # Ensure proper shutdown of Flask app and Ollama server
        stop_event.set()
        app_thread.join()
