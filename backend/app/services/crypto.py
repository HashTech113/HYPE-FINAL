"""Symmetric encryption for camera credentials at rest.

Uses Fernet (AES-128-CBC + HMAC-SHA256) with a key derived from the
CAMERA_SECRET_KEY env var via SHA-256, so the operator can supply any
sufficiently random string instead of needing to generate a 32-byte
url-safe base64 token.

Fails loudly if the env var is missing — we never silently fall back to
plaintext for camera credentials.
"""

from __future__ import annotations

import base64
import hashlib
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


class CryptoConfigError(RuntimeError):
    """CAMERA_SECRET_KEY is missing or unusable. Surfaced to the operator
    instead of silently degrading to plaintext."""


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    secret = os.getenv("CAMERA_SECRET_KEY", "").strip()
    if not secret:
        raise CryptoConfigError(
            "CAMERA_SECRET_KEY env var is required for camera credential "
            "encryption. Generate one with: "
            "python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    if len(secret) < 16:
        raise CryptoConfigError("CAMERA_SECRET_KEY must be at least 16 characters")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> str:
    if plaintext == "":
        return ""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    if ciphertext == "":
        return ""
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise CryptoConfigError(
            "Could not decrypt camera credential — CAMERA_SECRET_KEY likely "
            "rotated or wrong"
        ) from exc
