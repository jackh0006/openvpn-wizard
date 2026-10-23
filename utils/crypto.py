"""
Crypto Utilities - Password hashing, key generation.
"""

import crypt
import secrets
import hashlib
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization
from core.logger import get_logger


def generate_password_hash(password: str, method: str = "sha512") -> str:
    """Generate password hash using crypt."""
    salt = crypt.mksalt(crypt.METHOD_SHA512)
    return crypt.crypt(password, salt)


def verify_password(password: str, hash_: str) -> bool:
    """Verify password against hash."""
    return crypt.crypt(password, hash_) == hash_


def generate_x25519_key() -> tuple[str, str]:
    """Generate X25519 key pair. Returns (private_key_hex, public_key_hex)."""
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return priv_bytes.hex(), pub_bytes.hex()


def generate_short_id(length: int = 8) -> str:
    """Generate a random short ID for Reality."""
    return secrets.token_hex(length // 2)


def generate_uuid() -> str:
    """Generate a random UUID."""
    return secrets.token_hex(16)


def hash_data(data: str, algorithm: str = "sha256") -> str:
    """Hash data with specified algorithm."""
    h = hashlib.new(algorithm)
    h.update(data.encode())
    return h.hexdigest()