import json
from cryptography.fernet import Fernet
from shared_key import SECRET_KEY

fernet = Fernet(SECRET_KEY)


def encrypt_data(data_bytes: bytes) -> bytes:
    """Encrypt raw bytes → encrypted bytes"""
    return fernet.encrypt(data_bytes)


def decrypt_data(data_bytes: bytes) -> bytes:
    """Decrypt encrypted bytes → raw bytes"""
    return fernet.decrypt(data_bytes)


def encrypt_message(obj: dict) -> bytes:
    """Convert dict → JSON → encrypt → return cipher"""
    raw = json.dumps(obj).encode()
    return encrypt_data(raw)


def decrypt_message(cipher: bytes) -> dict:
    """Decrypt → JSON-decode → return dict"""
    raw = decrypt_data(cipher)
    return json.loads(raw.decode())
