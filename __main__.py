import os
import signal
import time
import threading
import configparser
from flask import Flask, request, render_template, jsonify, send_file
from markupsafe import Markup
import processing.ai as ai
import processing.mdprocessor as md
import login.server as server  # Now we import the server module
import random

config = configparser.ConfigParser()
config.read("config.cfg")

webdir = config['Web']['webdir'].strip('"')
webport = int(config['Web']['port'].strip('"'))
debug = bool(config["SYSTEM"]["debug"].strip('"'))

# Flask App Setup
app = Flask(__name__)
stop_event = threading.Event()

def handle_signal(signum, frame):
    stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def randIMG():
    img_dir = os.path.join(os.getcwd(), "templates", "img")
    
    if not os.path.exists(img_dir):
        return None
    
    imgs = [f for f in os.listdir(img_dir) if f.endswith(".jpg")]
    
    if not imgs:
        return None
    
    randomimg = random.choice(imgs)
    return os.path.join(img_dir, randomimg)

# Flask Routing
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
    password_confirm = request.form.get('confirm_password')
    phone = request.form.get('phone')
    name = request.form.get('name')

    if password == password_confirm:
        if debug:
            print("Failed")
        if server.register(email, name, phone, password):
            if debug:
                print("User Registered!")
            return render_template('login.html', message="Registration successful! Please log in.")
        else:
            if debug:
                print("Failed to register")
            return render_template('register.html', message="Registration failed, please try again later") 
    else:
        if debug:
                print("Passwords don't match")
                print(password,"=", password_confirm)
        return render_template('register.html', message="Passwords do not match")        

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
    print(server.listUsers())
    time.sleep(5)
    return send_file(randIMG(), mimetype='image/png')

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