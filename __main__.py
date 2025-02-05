import os
import signal
import time
import threading
import configparser
from flask import Flask, request, render_template, jsonify, send_file
from markupsafe import Markup
import processing.ai as ai
import processing.mdprocessor as md
import random


# Load configuration
config = configparser.ConfigParser()
config.read("config.cfg")

# Extract settings
webdir = config['Web']['webdir'].strip('"')
webport = int(config['Web']['port'].strip('"'))

# Flask app setup
app = Flask(__name__)
stop_event = threading.Event()

# Signal handling
def handle_signal(signum, frame):
    stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# RAND IMG
def randIMG():
    imgs = [f for f in os.listdir() if f.endswith(".jpg")]
    table = [[i + 1, img] for i, img in enumerate(imgs)]
    random_img = random.choice(imgs) if imgs else None
    

# Flask Routes
@app.route(webdir)
def home():
    return render_template('index.html')

@app.route(f'{webdir}/login')
def login_page():
    return render_template('login.html')

@app.route(f'{webdir}/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if server.login(email, password):
        return render_template('index.html')
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route(f'{webdir}/register')
def register_page():
    return render_template('register.html')

@app.route(f'{webdir}/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        return render_template('register.html', error="Passwords do not match")
    else:
        if server.register(email, password):
            return render_template('login.html')
        else:
            return render_template('register.html', error="Registration failed, please try again later")

@app.route(f'{webdir}/respond', methods=['POST'])
def respond():
    user_input = request.form.get('user_input')
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    try:
        ai.modTokens("user", user_input)
        system_response = ai.send(user_input)
        markdown_response = md.convert(system_response)
        return Markup(markdown_response)
    except Exception as e:
        return jsonify({"error": f"Failed: {e}"}), 500
    
@app.route(f'{webdir}/background.jpg')
def background():
    return send_file(randIMG(), mimetype='image/png')

# Server Start
if __name__ == '__main__':
    if config['DEFAULT'].get('clean_console', 'False').strip('"') == "True":
        os.system('cls' if os.name == 'nt' else 'clear')

    time.sleep(0.5)

    def start_app():
        try:
            app.run(debug=True, use_reloader=False, host='0.0.0.0', port=webport)
        except Exception as e:
            print(f"Failed to start app: {e}")
            stop_event.set()
            time.sleep(1)
            quit(e)

    app_thread = threading.Thread(target=start_app)
    app_thread.start()

    try:
        os.system("ollama serve")
    finally:
        stop_event.set()
        app_thread.join()
