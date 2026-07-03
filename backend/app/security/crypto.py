import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings


def _key_bytes() -> bytes:
    return base64.b64decode(settings.field_encryption_key)


def encrypt_field(plaintext: str) -> str:
    key = _key_bytes()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_field(token: str) -> str:
    key = _key_bytes()
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
