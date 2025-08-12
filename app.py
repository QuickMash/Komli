import os
import signal
import time
import threading
import configparser
from flask import Flask, request, render_template, jsonify, send_file, make_response, redirect, url_for
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

# Initialize database on startup
server.createdb()

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
    # Send user data to page so it can be used for things like login status or username
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    # Get conversation_id from URL parameters if provided
    conversation_id = request.args.get('conversation_id')
    
    return render_template('index.html', user=user_data, conversation_id=conversation_id)

@app.route(f'{webdir}/login')
def login_page():
    return render_template('login.html')

@app.route(f'{webdir}/reset')
def reset_pass():
    return render_template('reset.html')

@app.route(f'{webdir}/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if server.login(email, password):
        # Create response and set cookie
        response = make_response(redirect(url_for('home')))
        response.set_cookie('user', email, max_age=60*60*24*30)  # 30 days
        return response
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
        if server.register(email, name, phone, password):
            return render_template('login.html', message="Registration successful! Please log in.")
        else:
            return render_template('register.html', message="Registration failed, please try again later") 
    else:
        return render_template('register.html', message="Passwords do not match")

@app.route(f'{webdir}/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('user', '', expires=0)
    return response

@app.route(f'{webdir}/settings')
def settings():
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    return render_template('settings.html', user=user_data)

@app.route(f'{webdir}/settings', methods=['POST'])
def update_settings():
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    # Handle settings updates here
    # For now, just redirect back to settings with a success message
    return render_template('settings.html', user=user_data, message="Settings updated successfully!")

@app.route(f'{webdir}/profile')
def profile():
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    # Get user statistics
    user_stats = server.get_user_stats(user_data['email'])
    
    return render_template('profile.html', user=user_data, stats=user_stats)

@app.route(f'{webdir}/history')
def chat_history():
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    # Get recent conversations
    conversations = server.get_recent_conversations(user_data['email'], limit=20)
    
    return render_template('history.html', user=user_data, conversations=conversations)

# Route to start a new chat (redirects to home with new conversation)
@app.route(f'{webdir}/new_chat')
def new_chat():
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    if not user_data:
        return redirect(url_for('login_page'))
    conversation_id = server.create_conversation(user_data['email'])
    return redirect(url_for('home') + f'?conversation_id={conversation_id}')

# Route to view a specific chat/conversation (redirects to home with conversation)
@app.route(f'{webdir}/chat/<int:conversation_id>')
def chat(conversation_id):
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    if not user_data:
        return redirect(url_for('login_page'))
    conversation = server.get_conversation(conversation_id, user_data['email'])
    if not conversation:
        return render_template('404.html'), 404
    return redirect(url_for('home') + f'?conversation_id={conversation_id}')

@app.route(f'{webdir}/profile/<email>')
def public_profile(email):
    # Get user data for the requested profile
    user_data = server.get_user_data(email)
    
    if not user_data:
        return render_template('404.html'), 404
    
    # Get user statistics
    user_stats = server.get_user_stats(email)
    
    return render_template('public_profile.html', profile_user=user_data, stats=user_stats)

@app.route(f'{webdir}/profile', methods=['POST'])
def update_profile():
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    # Get form data
    name = request.form.get('name')
    phone = request.form.get('phone')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    # Update profile logic here
    try:
        if name and name != user_data['name']:
            # Update name in database
            server.update_user_field(user_data['email'], 'name', name)
            
        if phone and phone != user_data['phone']:
            # Update phone in database
            server.update_user_field(user_data['email'], 'phone', phone)
            
        if current_password and new_password:
            # Verify current password and update if correct
            if server.login(user_data['email'], current_password):
                server.update_user_field(user_data['email'], 'password', server.hash_password(new_password))
            else:
                # Get updated user data
                updated_user_data = server.get_user_data(user_data['email'])
                return render_template('profile.html', user=updated_user_data, error="Current password is incorrect")
        
        # Get updated user data
        updated_user_data = server.get_user_data(user_data['email'])
        return render_template('profile.html', user=updated_user_data, message="Profile updated successfully!")
        
    except Exception as e:
        return render_template('profile.html', user=user_data, error="Failed to update profile. Please try again.")        

@app.route(f'{webdir}/respond', methods=['POST'])
def respond():
    user_input = request.form.get('user_input')
    conversation_id = request.form.get('conversation_id')  # Optional conversation ID
    
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    
    # Get user data if logged in
    user_email = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
        if not user_data:
            user_email = None  # Invalid cookie
    
    try:
        ai.modTokens("user", user_input)
        system_response = ai.send(user_input)
        markdown_response = md.convert(system_response)
        
        # Log the conversation if user is logged in
        if user_email:
            try:
                # Use provided conversation_id or get/create active conversation
                if conversation_id:
                    # Verify the conversation belongs to the user
                    conv = server.get_conversation(int(conversation_id), user_email)
                    if conv:
                        target_conversation_id = int(conversation_id)
                    else:
                        target_conversation_id = server.get_or_create_active_conversation(user_email)
                else:
                    target_conversation_id = server.get_or_create_active_conversation(user_email)
                
                # Add user message
                server.add_message(target_conversation_id, user_email, 'user', user_input)
                
                # Add assistant response
                server.add_message(target_conversation_id, user_email, 'assistant', system_response)
                
            except Exception as e:
                pass
        
        return Markup(markdown_response)
    except Exception as e:
        return jsonify({"error": f"Failed: {e}"}), 500

# API endpoint for fetching conversations
@app.route(f'{webdir}/api/conversations')
def api_conversations():
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Get recent conversations
    conversations = server.get_recent_conversations(user_data['email'], limit=10)
    
    return jsonify({"conversations": conversations})

# API endpoint for creating new conversation
@app.route(f'{webdir}/api/new-conversation', methods=['POST'])
def api_new_conversation():
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Create new conversation
    conversation_id = server.create_conversation(user_data['email'])
    
    if conversation_id:
        return jsonify({"conversation_id": conversation_id})
    else:
        return jsonify({"error": "Failed to create conversation"}), 500

# API endpoint for fetching conversation messages
@app.route(f'{webdir}/api/conversation/<int:conversation_id>/messages')
def api_conversation_messages(conversation_id):
    # Check if user is logged in
    user_data = None
    if 'user' in request.cookies:
        user_email = request.cookies.get('user')
        user_data = server.get_user_data(user_email)
    
    if not user_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Verify the conversation belongs to the user
    conversation = server.get_conversation(conversation_id, user_data['email'])
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    # Get conversation messages
    messages = server.get_conversation_messages(conversation_id)
    
    return jsonify({"messages": messages})

# For a random background
@app.route(f'{webdir}/background.jpg')
def background():
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
