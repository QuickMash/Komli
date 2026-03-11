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

# Import Plugins
for plugin in os.listdir('plugins'):
    if plugin.endswith('.py'): # Only import .py files
        # TODO: Add a warning prompt for untrusted plugins
        __import__(f'plugins.{plugin[:-3]}')

config = configparser.ConfigParser()
config.read("config.cfg")

web_dir = config['Web']['webdir'].strip('"')
web_port = int(config['Web']['port'].strip('"'))
debug_mode = bool(config["SYSTEM"]["debug"].strip('"'))

# Flask App Setup
app = Flask(__name__)
stop_event = threading.Event()

def get_authenticated_user():
    """Resolve the authenticated user from cookie, preferring internal user id."""
    user_id = request.cookies.get('user_id')
    if user_id:
        try:
            user_id_int = int(user_id)
            user_data = server.get_user_data_by_id(user_id_int)
            if user_data:
                return user_data
        except (TypeError, ValueError):
            pass

    # Backward compatibility for existing sessions that still store email.
    legacy_user_email = request.cookies.get('user')
    if legacy_user_email:
        return server.get_user_data(legacy_user_email)

    return None

# Initialize database on startup
server.createdb()

def handle_signal(_signum, _frame):
    stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def random_image_path():
    img_dir = os.path.join(os.getcwd(), "templates", "img")
    
    if not os.path.exists(img_dir):
        return None
    
    image_files = [file_name for file_name in os.listdir(img_dir) if file_name.endswith(".jpg")]
    
    if not image_files:
        return None
    
    random_image = random.choice(image_files)
    return os.path.join(img_dir, random_image)

# Flask Routing
@app.route(web_dir)
def home():
    # Send user data to page so it can be used for things like login status or username
    user_data = get_authenticated_user()
    
    # Get conversation_id from URL parameters if provided
    conversation_id = request.args.get('conversation_id')
    
    return render_template('index.html', user=user_data, conversation_id=conversation_id)

@app.route(f'{web_dir}/login')
def login_page():
    return render_template('login.html')

@app.route(f'{web_dir}/reset')
def reset_pass():
    return render_template('reset.html')

@app.route(f'{web_dir}/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if server.login(email, password):
        # Create response and set cookie
        response = make_response(redirect(url_for('home')))
        user_id = server.get_user_id(email)
        response.set_cookie('user_id', str(user_id), max_age=60*60*24*30, httponly=True, samesite='Lax')
        response.set_cookie('user', '', expires=0)
        return response
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route(f'{web_dir}/register')
def register_page():
    return render_template('register.html')

@app.route(f'{web_dir}/register', methods=['POST'])
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

@app.route(f'{web_dir}/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('user', '', expires=0)
    response.set_cookie('user_id', '', expires=0)
    return response

@app.route(f'{web_dir}/settings')
def settings():
    # Check if user is logged in
    user_data = get_authenticated_user()
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    return render_template('settings.html', user=user_data)

@app.route(f'{web_dir}/settings', methods=['POST'])
def update_settings():
    # Check if user is logged in
    user_data = get_authenticated_user()
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    # Handle settings updates here
    # For now, just redirect back to settings with a success message
    return render_template('settings.html', user=user_data, message="Settings updated successfully!")

@app.route(f'{web_dir}/profile')
def profile():
    # Check if user is logged in
    user_data = get_authenticated_user()
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    # Get user statistics
    user_stats = server.get_user_stats(user_data['email'])
    
    return render_template('profile.html', user=user_data, stats=user_stats)

@app.route(f'{web_dir}/history')
def chat_history():
    # Check if user is logged in
    user_data = get_authenticated_user()
    
    if not user_data:
        return redirect(url_for('login_page'))
    
    # Get recent conversations
    conversations = server.get_recent_conversations(user_data['email'], limit=20)
    
    return render_template('history.html', user=user_data, conversations=conversations)

# Route to start a new chat (redirects to home with new conversation)
@app.route(f'{web_dir}/new_chat')
def new_chat():
    user_data = get_authenticated_user()
    if not user_data:
        return redirect(url_for('login_page'))
    conversation_id = server.create_conversation(user_data['email'])
    return redirect(url_for('home') + f'?conversation_id={conversation_id}')

# Route to view a specific chat/conversation (redirects to home with conversation)
@app.route(f'{web_dir}/chat/<int:conversation_id>')
def chat(conversation_id):
    user_data = get_authenticated_user()
    if not user_data:
        return redirect(url_for('login_page'))
    conversation = server.get_conversation(conversation_id, user_data['email'])
    if not conversation:
        return render_template('404.html'), 404
    return redirect(url_for('home') + f'?conversation_id={conversation_id}')

@app.route(f'{web_dir}/profile/<email>')
def public_profile(email):
    # Get user data for the requested profile
    user_data = server.get_user_data(email)
    
    if not user_data:
        return render_template('404.html'), 404
    
    # Get user statistics
    user_stats = server.get_user_stats(email)
    
    return render_template('public_profile.html', profile_user=user_data, stats=user_stats)

@app.route(f'{web_dir}/profile', methods=['POST'])
def update_profile():
    # Check if user is logged in
    user_data = get_authenticated_user()
    
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
        
    except Exception:
        return render_template('profile.html', user=user_data, error="Failed to update profile. Please try again.")        

@app.route(f'{web_dir}/respond', methods=['POST'])
def respond():
    user_input = request.form.get('user_input')
    conversation_id = request.form.get('conversation_id')  # Optional conversation ID
    
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    
    # Get user data if logged in
    user_data = get_authenticated_user()
    user_email = user_data['email'] if user_data else None
    user_id = user_data['id'] if user_data else None
    
    try:
        ai.modTokens(str(user_id) if user_id else "guest", user_input)
        system_response = ai.send(user_input)
        markdown_response = md.convert(system_response)
        
        # Log the conversation if user is logged in
        if user_email:
            try:
                # Use provided conversation_id or get/create active conversation
                if conversation_id:
                    # Verify the conversation belongs to the user
                    conversation_record = server.get_conversation(int(conversation_id), user_email)
                    if conversation_record:
                        target_conversation_id = int(conversation_id)
                    else:
                        target_conversation_id = server.get_or_create_active_conversation(user_email)
                else:
                    target_conversation_id = server.get_or_create_active_conversation(user_email)
                
                # Add user message
                server.add_message(target_conversation_id, user_email, 'user', user_input)
                
                # Add assistant response
                server.add_message(target_conversation_id, user_email, 'assistant', system_response)
                
            except Exception:
                pass
        
        return Markup(markdown_response)
    except Exception as error:
        return jsonify({"error": f"Failed: {error}"}), 500

# API endpoint for fetching conversations
@app.route(f'{web_dir}/api/conversations')
def api_conversations():
    # Check if user is logged in
    user_data = get_authenticated_user()
    
    if not user_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Get recent conversations
    conversations = server.get_recent_conversations(user_data['email'], limit=10)
    
    return jsonify({"conversations": conversations})

# API endpoint for creating new conversation
@app.route(f'{web_dir}/api/new-conversation', methods=['POST'])
def api_new_conversation():
    # Check if user is logged in
    user_data = get_authenticated_user()
    
    if not user_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Create new conversation
    conversation_id = server.create_conversation(user_data['email'])
    
    if conversation_id:
        return jsonify({"conversation_id": conversation_id})
    else:
        return jsonify({"error": "Failed to create conversation"}), 500

# API endpoint for fetching conversation messages
@app.route(f'{web_dir}/api/conversation/<int:conversation_id>/messages')
def api_conversation_messages(conversation_id):
    # Check if user is logged in
    user_data = get_authenticated_user()
    
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
@app.route(f'{web_dir}/background.jpg')
def background():
    time.sleep(5)
    return send_file(random_image_path(), mimetype='image/png')

if __name__ == '__main__':
    if config['DEFAULT'].get('clean_console', 'False').strip('"') == "True":
        os.system('cls' if os.name == 'nt' else 'clear')
    time.sleep(0.5)
    def start_app():
        try:
            app.run(debug=debug_mode, use_reloader=False, host='0.0.0.0', port=web_port)
        except Exception as error:
            stop_event.set()
            time.sleep(1)
            quit(error)
    app_thread = threading.Thread(target=start_app)
    app_thread.start()
    try:
        os.system("ollama serve")
    finally:
        stop_event.set()
        app_thread.join()
