import bcrypt

def hash(password):
    """Hashes password, and adds salt."""
    print("Adding Salt...")
    salt = bcrypt.gensalt()
    print("Hashing...")
    hashed = bcrypt.hashpw(password.encode(), salt)
    print("Hashed!")
    return hashed
