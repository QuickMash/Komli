from flask import Flask, request, render_template
import random
import os
import systemz

os.system("clear")

app = Flask(__name__)

# Sample responses for Komli
komli_responses = [
    "Hello, human! How can I assist you today?",
    "I'm here to help! What do you need?",
    "Komli at your service! How can I make your day better?",
    "Hey there! What's on your mind?"
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/respond', methods=['POST'])
def respond():
    user_input = request.form.get('user_input')  # Get user input from the form
    print(f'User sent: {user_input}')  # Print user input to the console
    system_response = systemz.send(user_input)  # Use systemz to handle the response
    return f'Komli: {system_response}'

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
