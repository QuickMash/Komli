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
        id INTEGER UNIQUE AUTOINCREMENT,
        name TEXT,
        password TEXT,
        tokens TEXT,
        email_reset TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS tokens (
        i
        used TEXT,
        max TEXT
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
    cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        db.close()
        return False

    stored_password = user[0]
    if hasher.verify(password, stored_password):
        db.close()
        return True
    else:
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

def listUserIds():
    """Lists all user IDs in the database."""
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    return user_ids

def get_user_data(email):
    """Retrieves user data for a given email."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT id, email, name, phone FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    db.close()
    
    if user:
        return {
            'id': user[0],
            'email': user[1],
            'name': user[2], 
            'phone': user[3]
        }
    return None

def get_user_data_by_id(user_id):
    """Retrieves user data for a given internal user id."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT id, email, name, phone FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    db.close()

    if user:
        return {
            'id': user[0],
            'email': user[1],
            'name': user[2],
            'phone': user[3]
        }
    return None

def get_user_id(email):
    """Gets internal user id for an email."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    db.close()
    return row[0] if row else None

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
    return hasher.hash(password)

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

def get_conversation(conversation_id, user_email):
    """Gets a specific conversation if it belongs to the user."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT id, title, created_at, updated_at
            FROM conversations 
            WHERE id = ? AND user_email = ?
        """, (conversation_id, user_email))
        result = cursor.fetchone()
        db.close()
        
        if result:
            return {
                'id': result[0],
                'title': result[1],
                'created_at': result[2],
                'updated_at': result[3]
            }
        return None
    except Exception as e:
        db.close()
        return None

def get_conversation_messages(conversation_id):
    """Gets all messages for a specific conversation."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT id, message_type, content, created_at
            FROM messages 
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conversation_id,))
        messages = cursor.fetchall()
        db.close()
        
        return [{
            'id': msg[0],
            'message_type': msg[1],
            'content': msg[2],
            'created_at': msg[3]
        } for msg in messages]
    except Exception as e:
        db.close()
        return []

def search_conversations(user_email, query):
    """Searches conversations and messages for a given user by keyword."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    try:
        # Escape LIKE wildcards so user input is treated as a literal string
        escaped = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        like_query = f'%{escaped}%'
        cursor.execute("""
            SELECT DISTINCT c.id, c.title, c.updated_at,
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_email = ?
              AND (c.title LIKE ? ESCAPE '\\' OR m.content LIKE ? ESCAPE '\\')
            ORDER BY c.updated_at DESC
            LIMIT 20
        """, (user_email, like_query, like_query))
        results = cursor.fetchall()
        db.close()
        return [{
            'id': r[0],
            'title': r[1],
            'updated_at': r[2],
            'message_count': r[3]
        } for r in results]
    except Exception:
        db.close()
        return []

app = Flask(__name__)

@app.teardown_appcontext
def teardown_db(exception):
    """Ensures the database is closed at the end of the request."""
    closedb()

if __name__ == "__main__":
    createdb()  # Ensure database and tables exist before starting the app
    app.run(debug=True)
