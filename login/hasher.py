import bcrypt

def hash(password):
    """Hashes password, and adds salt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed

def verify(password, hashed):
    """Verifies password against hashed password."""
    if bcrypt.checkpw(password.encode(), hashed):
        return True
    else:
        return False
