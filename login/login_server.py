import sqlite3
from flask import Flask, request, render_template, jsonify, g
import html
import hasher

app = Flask(__name__)

DATABASE = "users.db"

def get_db():
    """Get a database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

class LoginSystem:
    def __init__(self):
        self.conn = get_db()
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Create users table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def register(self, username, password):
        """Register a new user with hashed password."""
        username = html.escape(username)  # Sanitize input
        hashed_password = hasher.hash(password)
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            self.conn.commit()
            return "User registered successfully!"
        except sqlite3.IntegrityError:
            return "Username already exists."

    def authenticate(self, username, password):
        """Check if the username and password match (handled via database)."""
        username = html.escape(username)  # Sanitize input
        self.cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        return result and hasher.decode(result[0]) == password

    def login(self, username, password):
        """Attempt to log in a user."""
        if self.authenticate(username, password):
            return "Login successful!"
        else:
            return "Invalid username or password."


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400

    username = data['username']
    password = data['password']
    login_system = LoginSystem()  # Initialize LoginSystem in the request context
    message = login_system.register(username, password)
    if "successfully" in message:
        return jsonify({"message": message}), 200
    return jsonify({"error": message}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400

    username = data['username']
    password = data['password']
    login_system = LoginSystem()  # Initialize LoginSystem in the request context
    message = login_system.login(username, password)
    if "successful" in message:
        return jsonify({"message": message}), 200
        print("YAY")
    return jsonify({"error": message}), 400
    print("Nooo")

@app.before_request
def before_request():
    """Ensure the database connection is set up for each request."""
    get_db()

@app.teardown_appcontext
def teardown_appcontext(error):
    """Close the database connection after each request."""
    close_db()

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
