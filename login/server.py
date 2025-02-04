import sqlite3
from flask import Flask, request, render_template, jsonify, g
import html
import hasher
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.cfg')
db_prefix = config.get('Database', 'database_prefix')

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
    
def register(email, password):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email, ))
    user = cursor.fetchone()
    if user:
        return False
    else:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hasher.hash(password)))
        db.commit()
        return True
        if config[TOKEN_LIMIT]["join_reward_enable"].strip('"') == "True":
            cursor.execute("INSERT INTO tokens (user,value) VALUES (?, ?)", (email,config[TOKEN_LIMIT]["join_reward"]))
            db.commit()
            return True
    
    
def login(email, password):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user and hasher.hash(password) == user['password']:
        return True
    else:
        return False

def getTokens(user):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tokens WHERE user = ?", (user, ))
    tokens = cursor.fetchall()
    return tokens

def setTokens(user, value):
    db = opendb()
    cursor = db.cursor()
    cursor.execute("UPDATE tokens SET value = ? WHERE user = ?", (value,user))
    db.commit()
    return True
