import sqlite3
from flask import Flask, request, render_template, jsonify, g
import html
import configparser
import login.hasher as hasher

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.cfg')
db_prefix = config.get('DEFAULT', 'database_prefix')

DATABASE = 'login/db/' + db_prefix + 'users.db'

def opendb():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def closedb():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        return True
    else:
        print("No database to close")
        return False
    
def createdb():
    db = opendb()
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, tokens TEXT, email_reset TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS tokens (user TEXT, value TEXT)")
    db.commit()
    db.close()

def register(email, password):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email, ))
    user = cursor.fetchone()
    if user:
        db.close()
        return False
    else:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hasher.hash(password)))
        db.commit()
        if config.has_section('TOKEN_LIMIT') and config['TOKEN_LIMIT'].getboolean('join_reward_enable'):
            cursor.execute("INSERT INTO tokens (user, value) VALUES (?, ?)", (email, config['TOKEN_LIMIT']['join_reward']))
            db.commit()
        db.close()
        return True

def login(email, password):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    result = user and hasher.hash(password) == user['password']
    db.close()
    return result

def getTokens(user):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tokens WHERE user = ?", (user, ))
    tokens = cursor.fetchall()
    db.close()
    return tokens

def setTokens(user, value):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("UPDATE tokens SET value = ? WHERE user = ?", (value, user))
    db.commit()
    db.close()
    return True
