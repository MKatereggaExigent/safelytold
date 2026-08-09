from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _development_cipher() -> Fernet:
    if os.getenv('ENVIRONMENT', 'development') == 'production':
        raise RuntimeError('Production identity encryption must use KMS/HSM envelope encryption')
    secret = os.getenv('REPORTER_VAULT_DEV_KEY', 'development-only-change-me').encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_identity(value: bytes) -> bytes:
    return _development_cipher().encrypt(value)


def decrypt_identity(value: bytes) -> bytes:
    return _development_cipher().decrypt(value)
