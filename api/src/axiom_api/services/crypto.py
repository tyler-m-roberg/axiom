import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from axiom_api.config import settings


def _key() -> bytes:
    raw = settings.session_encryption_key
    if not raw:
        raise RuntimeError("SESSION_ENCRYPTION_KEY is not set")
    try:
        key = base64.urlsafe_b64decode(raw)
    except Exception as exc:
        raise RuntimeError("SESSION_ENCRYPTION_KEY must be base64-encoded") from exc
    if len(key) != 32:
        raise RuntimeError("SESSION_ENCRYPTION_KEY must decode to 32 bytes")
    return key


def encrypt(plaintext: str | None) -> bytes | None:
    if plaintext is None:
        return None
    aesgcm = AESGCM(_key())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return nonce + ct


def decrypt(blob: bytes | None) -> str | None:
    if blob is None:
        return None
    aesgcm = AESGCM(_key())
    nonce, ct = blob[:12], blob[12:]
    return aesgcm.decrypt(nonce, ct, associated_data=None).decode("utf-8")
