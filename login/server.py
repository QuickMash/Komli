import os
import sqlite3
from flask import Flask, request, jsonify, g
import configparser
import login.hasher as hasher

# Load configuration
config = configparser.ConfigParser()
config.read('config.cfg')
db_prefix = config.get('DEFAULT', 'database_prefix').strip('"')

DATABASE = f'login/db/{db_prefix}users.db'

def opendb():
    """Opens a connection to the SQLite database, creating it if necessary."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        with db:
            createdb()  # Ensure tables exist
    return db

def closedb():
    """Closes the database connection."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        g._database = None
        return True
    return False

def createdb():
    """Creates the required tables in the database if they do not exist."""
    # Ensure the database directory exists
    db_dir = os.path.dirname(DATABASE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        password TEXT,
        tokens TEXT,
        email_reset TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS tokens (
        user TEXT PRIMARY KEY,
        value TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_email) REFERENCES users (email)
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        user_email TEXT,
        message_type TEXT CHECK(message_type IN ('user', 'assistant')),
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id),
        FOREIGN KEY (user_email) REFERENCES users (email)
    )""")
    db.commit()
    db.close()

def register(email, name, phone, password):
    """Registers a new user if they do not already exist."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if user:
        db.close()
        return False

    hashed_password = hasher.hash(password)
    cursor.execute("INSERT INTO users (email, name, password, tokens, email_reset, phone) VALUES (?, ?, ?, ?, ?, ?)", 
                   (email, name, hashed_password, "", "", phone))
    print("created user")
    db.commit()

    if config.has_section('TOKEN_LIMIT') and config['TOKEN_LIMIT'].getboolean('join_reward_enable'):
        cursor.execute("INSERT INTO tokens (user, value) VALUES (?, ?)", (email, config['TOKEN_LIMIT']['join_reward']))
        db.commit()

    db.close()
    return True

def login(email, password):
    """Authenticates a user. Returns False if the user does not exist or password is incorrect."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:  
        print("Error: User does not exist")
        db.close()
        return False

    # user is a tuple, so access by index
    if not hasher.verify(password, user[2]):  # password is at index 2
        print("Error: Incorrect password")
        db.close()
        return False

    db.close()
    return True

def getTokens(user):
    """Retrieves all tokens for a given user."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT value FROM tokens WHERE user = ?", (user,))
    tokens = cursor.fetchone()
    db.close()
    return tokens[0] if tokens else None

def setTokens(user, value):
    """Updates a user's token value, inserting a new record if necessary."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tokens WHERE user = ?", (user,))
    if cursor.fetchone():
        cursor.execute("UPDATE tokens SET value = ? WHERE user = ?", (value, user))
    else:
        cursor.execute("INSERT INTO tokens (user, value) VALUES (?, ?)", (user, value))
    db.commit()
    db.close()
    return True

def listUsers():
    """Lists all users in the database."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    db.close()
    return users

def get_user_data(email):
    """Retrieves user data for a given email."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT email, name, phone FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    db.close()
    
    if user:
        return {
            'email': user[0],
            'name': user[1], 
            'phone': user[2]
        }
    return None

def update_user_field(email, field, value):
    """Updates a specific field for a user."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    # Validate field name to prevent SQL injection
    allowed_fields = ['name', 'phone', 'password', 'email_reset']
    if field not in allowed_fields:
        db.close()
        return False
    
    try:
        cursor.execute(f"UPDATE users SET {field} = ? WHERE email = ?", (value, email))
        db.commit()
        success = cursor.rowcount > 0
        db.close()
        return success
    except Exception as e:
        db.close()
        return False

def hash_password(password):
    """Hashes a password using the hasher module."""
    return hasher.hash_password(password)

def create_conversation(user_email, title="New Chat"):
    """Creates a new conversation for a user."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO conversations (user_email, title) VALUES (?, ?)", (user_email, title))
        conversation_id = cursor.lastrowid
        db.commit()
        db.close()
        return conversation_id
    except Exception as e:
        db.close()
        return None

def add_message(conversation_id, user_email, message_type, content):
    """Adds a message to a conversation."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO messages (conversation_id, user_email, message_type, content) 
            VALUES (?, ?, ?, ?)
        """, (conversation_id, user_email, message_type, content))
        
        # Update conversation timestamp
        cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
        
        db.commit()
        message_id = cursor.lastrowid
        db.close()
        return message_id
    except Exception as e:
        db.close()
        return None

def get_user_stats(user_email):
    """Gets user statistics including message count, conversation count, and days active."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    try:
        # Get total message count
        cursor.execute("SELECT COUNT(*) FROM messages WHERE user_email = ?", (user_email,))
        message_count = cursor.fetchone()[0]
        
        # Get conversation count
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_email = ?", (user_email,))
        conversation_count = cursor.fetchone()[0]
        
        # Get days active (days since first message)
        cursor.execute("""
            SELECT julianday('now') - julianday(MIN(created_at)) as days_active 
            FROM messages WHERE user_email = ?
        """, (user_email,))
        result = cursor.fetchone()
        days_active = int(result[0]) if result[0] else 0
        
        # Get user creation date
        cursor.execute("SELECT created_at FROM users WHERE email = ?", (user_email,))
        user_created = cursor.fetchone()
        
        # If no messages yet, calculate days since user registration
        if days_active == 0 and user_created:
            cursor.execute("SELECT julianday('now') - julianday(?) as days_since_registration", (user_created[0],))
            result = cursor.fetchone()
            days_active = int(result[0]) if result[0] else 0
        
        db.close()
        return {
            'message_count': message_count,
            'conversation_count': conversation_count,
            'days_active': max(days_active, 0)
        }
    except Exception as e:
        db.close()
        return {
            'message_count': 0,
            'conversation_count': 0,
            'days_active': 0
        }

def get_recent_conversations(user_email, limit=10):
    """Gets recent conversations for a user."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT id, title, created_at, updated_at,
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
            FROM conversations 
            WHERE user_email = ? 
            ORDER BY updated_at DESC 
            LIMIT ?
        """, (user_email, limit))
        conversations = cursor.fetchall()
        db.close()
        
        return [{
            'id': conv[0],
            'title': conv[1],
            'created_at': conv[2],
            'updated_at': conv[3],
            'message_count': conv[4]
        } for conv in conversations]
    except Exception as e:
        db.close()
        return []

def get_or_create_active_conversation(user_email):
    """Gets the most recent conversation or creates a new one."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    try:
        # Get the most recent conversation
        cursor.execute("""
            SELECT id FROM conversations 
            WHERE user_email = ? 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, (user_email,))
        result = cursor.fetchone()
        db.close()
        
        if result:
            return result[0]
        else:
            # Create a new conversation
            return create_conversation(user_email)
    except Exception as e:
        db.close()
        return create_conversation(user_email)

app = Flask(__name__)

@app.teardown_appcontext
def teardown_db(exception):
    """Ensures the database is closed at the end of the request."""
    closedb()

if __name__ == "__main__":
    createdb()  # Ensure database and tables exist before starting the app
    app.run(debug=True)
