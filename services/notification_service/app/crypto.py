from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _cipher() -> Fernet:
    if os.getenv('ENVIRONMENT', 'development') == 'production':
        raise RuntimeError('Production outbound-email credential encryption must use KMS/HSM envelope encryption')
    secret = os.getenv('NOTIFICATION_VAULT_DEV_KEY', 'development-only-change-me').encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_credential(value: str) -> bytes:
    return _cipher().encrypt(value.encode('utf-8'))


def decrypt_credential(value: bytes) -> str:
    return _cipher().decrypt(value).decode('utf-8')
