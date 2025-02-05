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
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        password TEXT,
        tokens TEXT,
        email_reset TEXT,
        phone TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS tokens (
        user TEXT PRIMARY KEY,
        value TEXT
    )""")
    db.commit()
    db.close()

def register(email, name, phone, password):
    """Registers a new user if they do not already exist."""
    db = opendb()
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
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:  
        print("Error: User does not exist")
        db.close()
        return False

    if not hasher.verify(password, user['password']):
        print("Error: Incorrect password")
        db.close()
        return False

    db.close()
    return True

def getTokens(user):
    """Retrieves all tokens for a given user."""
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT value FROM tokens WHERE user = ?", (user,))
    tokens = cursor.fetchone()
    db.close()
    return tokens['value'] if tokens else None

def setTokens(user, value):
    """Updates a user's token value, inserting a new record if necessary."""
    db = opendb()
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
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    db.close()
    return users

app = Flask(__name__)

@app.teardown_appcontext
def teardown_db(exception):
    """Ensures the database is closed at the end of the request."""
    closedb()

if __name__ == "__main__":
    createdb()  # Ensure database and tables exist before starting the app
    app.run(debug=True)
