import bcrypt
import base64


def generate_password_hash(password, salt_rounds=10):
    """convert pass to store in hash in db"""
    password_bin = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bin, bcrypt.gensalt(salt_rounds))
    encoded = base64.b64encode(hashed)
    return encoded.decode('utf-8')


def check_password_hash(encoded, password):
    """check if hash in db is equal to user login password"""
    password = password.encode('utf-8')
    encoded = encoded.encode('utf-8')
    hashed = base64.b64decode(encoded)
    is_correct = bcrypt.hashpw(password, hashed) == hashed
    return is_correct
