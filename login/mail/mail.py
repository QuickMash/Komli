from smtplib import SMTP
from email.mime.text import MIMEText
import secrets
import sqlite3


# Unfinished file for handling email functionality

# Site will have a page to enter a code from an email to reset password

def reset_password(email):
    """
    Sends a reset password request to email
    """

def generate_reset_code():
    """
    Generates a secure random code for password reset
    Returns a 32 character hex string
    """
    with sqlite3.connect("reset.db") as conn:
        cursor = conn.cursor()
        code = secrets.token_hex(16)
        cursor.execute("INSERT INTO reset_codes VALUES (?, ?)", (code, email))
        conn.commit()