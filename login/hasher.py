import bcrypt

def hash(password):
    """Hashes password, and adds salt."""
    print("Adding Salt...")
    salt = bcrypt.gensalt()
    print("Hashing...")
    hashed = bcrypt.hashpw(password.encode(), salt)
    print("Hashed!")
    return hashed

def verify(password, hashed):
    """Verifies password against hashed password."""
    print("Checking password...")
    if bcrypt.checkpw(password.encode(), hashed):
        print("Password is correct")
        return True
    else:
        print("Password is incorrect")
        return False
