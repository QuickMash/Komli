from smtplib import SMTP
from email.mime.text import MIMEText
import secrets
import sqlite3


reset_password_html_message = """
<html>
    <head></head>
    <body>
    <h1>Reset Password</h1>
    <a href="https://example.com/reset?id={code}">Reset Password</a>
    <p>Someone has requested a reset password, if this was not you, you can safely ignore this message</p>
    </body>
</html>
"""

def reset_password(email)
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