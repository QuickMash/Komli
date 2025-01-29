from flask import Flask, request, render_template, jsonify
import threading
import os
import signal
import ai
import time

config = {}

with open('config.cfg') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.split('#', 1)[0].strip().strip('"')
            config[key] = value

required_keys = ['name', 'webdir', 'model', 'system_prompt', 'version']
for key in required_keys:
    if key not in config:
        raise ValueError(f"Missing required config key: {key}")

ai.configure(config['name'], config['webdir'], config['model'], config['system_prompt'], config['version'])

app = Flask(__name__)

stop_event = threading.Event()

def serve_function():
    while not stop_event.is_set():
        os.system("ollama serve")
        stop_event.wait(1)

def handle_signal(signum, frame):
    stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

@app.route(config["webdir"])
def home():
    return render_template('index.html')

@app.route('/respond', methods=['POST'])
def respond():
    user_input = request.form.get('user_input')
    system_response = ai.send(user_input, config['name'], config['system_prompt'], config['version'])
    return f'Komli: {system_response}'

if __name__ == '__main__':
    os.system("clear")
    time.sleep(0.5)
    def start_app():
        app.run(debug=True, use_reloader=False)

    app_thread = threading.Thread(target=start_app)
    app_thread.start()

    try:
        print("Starting Ollama...")
        os.system("ollama serve")
    finally:
        stop_event.set()
        app_thread.join()