from flask import Flask, request, render_template, jsonify
import os
import systemz

config = {}

# Read the config file
with open('config.cfg') as f:
    for line in f:
        # Ignore empty lines and comments
        if line.strip() and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.split('#', 1)[0].strip().strip('"')
            config[key] = value

# Ensure all required config values are present
required_keys = ['name', 'webdir', 'model', 'system_prompt', 'version']
for key in required_keys:
    if key not in config:
        raise ValueError(f"Missing required config key: {key}")

systemz.configure(config['name'], config['webdir'], config['model'], config['system_prompt'], config['version'])

app = Flask(__name__)

@app.route(config["webdir"])
def home():
    return render_template('index.html')

@app.route('/respond', methods=['POST'])
def respond():
    user_input = request.form.get('user_input')  # Get user input from the form
    print(f'User sent: {user_input}')  # Print user input to the console
    system_response = systemz.send(user_input, config['name'], config['system_prompt'], config['version'])  # Pass the required arguments
    return f'Komli: {system_response}'

if __name__ == '__main__':
    os.system("clear")
    app.run(debug=True, use_reloader=True)
