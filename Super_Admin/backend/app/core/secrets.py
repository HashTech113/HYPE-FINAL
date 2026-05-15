"""Symmetric encryption-at-rest for sensitive column values.

Currently used for camera RTSP passwords. The cipher is keyed by the
`CAMERA_SECRET_KEY` env var (a Fernet key — 32 random bytes,
base64-encoded). Generate one with:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Rollout / back-compat:
  When `CAMERA_SECRET_KEY` is unset OR invalid, the cipher operates in
  PASSTHROUGH mode: encrypt() returns the input unchanged, decrypt()
  returns the input unchanged. The startup logs a loud WARNING so a
  production operator notices. This keeps existing deployments
  working without a key while letting them opt in by setting one.

  When the key IS set, encrypt() produces Fernet tokens (always start
  with "gAAAA"). decrypt() detects the prefix — values that don't
  look like a Fernet token are treated as legacy plaintext and
  returned as-is. This lets existing plaintext rows be read transparently
  while new writes get encrypted; the database migrates row-by-row as
  records are updated.

Limitation worth knowing:
  This protects the `cameras.password` column. The `cameras.rtsp_url`
  column still contains the password embedded in the URL string —
  protecting that requires reconstructing the URL from decomposed
  components on every worker start. Tracked as a follow-up; encrypting
  `password` here is defense-in-depth, not a sole layer of protection.
"""

from __future__ import annotations

import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

log = logging.getLogger(__name__)

# Fernet tokens always begin with these 5 base64-encoded characters
# (version byte 0x80 → "gAAAA"). Used to distinguish ciphertext from
# legacy plaintext during the migration window.
_FERNET_PREFIX = "gAAAA"


class SecretCipher:
    """Fernet wrapper with passthrough fallback.

    `encrypt`/`decrypt` are total: they never raise, never lose data.
    On any cipher failure the input is returned unchanged and a
    warning is logged — invalid keys must not crash the app.
    """

    def __init__(self, key: str | None) -> None:
        self._fernet: Fernet | None = None
        if key:
            try:
                self._fernet = Fernet(key.encode("ascii"))
            except (ValueError, TypeError) as exc:
                log.error(
                    "CAMERA_SECRET_KEY is set but invalid (%s); "
                    "encryption is DISABLED. Generate a valid key with "
                    "`python -c 'from cryptography.fernet import Fernet; "
                    "print(Fernet.generate_key().decode())'`",
                    exc,
                )
                self._fernet = None
        if self._fernet is None:
            log.warning(
                "CAMERA_SECRET_KEY not set — sensitive columns will be "
                "stored in PLAINTEXT. To enable encryption, generate a "
                "Fernet key and set the CAMERA_SECRET_KEY env var."
            )

    @property
    def enabled(self) -> bool:
        return self._fernet is not None

    def encrypt(self, plaintext: str) -> str:
        if self._fernet is None:
            return plaintext
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        if self._fernet is None:
            return value
        # Heuristic: if the stored value doesn't look like a Fernet
        # token, assume it predates encryption and return as-is.
        # Avoids spamming InvalidToken warnings for every legacy row.
        if not value.startswith(_FERNET_PREFIX):
            return value
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken:
            # The value looks like Fernet but won't decrypt — likely
            # encrypted under a previous key that's no longer in env,
            # or genuinely corrupt. Don't lose the bytes; surface a
            # warning + return what we have so the caller can decide.
            log.warning(
                "Failed to decrypt encrypted column value (wrong key or "
                "corrupt). Returning ciphertext to avoid data loss; the "
                "next write will re-encrypt under the current key."
            )
            return value


_cipher: SecretCipher | None = None


def get_cipher() -> SecretCipher:
    """Lazy global. Created on first use so test code can monkeypatch
    the env without us reading it at import time."""
    global _cipher
    if _cipher is None:
        # Imported here (not at module top) to keep this module free
        # of any FastAPI / pydantic import side-effects.
        from app.config import get_settings

        _cipher = SecretCipher(get_settings().CAMERA_SECRET_KEY)
    return _cipher


# --- SQLAlchemy adapter --------------------------------------------------


class EncryptedString(TypeDecorator):
    """SQLAlchemy `String` column whose values are transparently
    encrypted on write and decrypted on read.

    `length` sizes the underlying VARCHAR. Pick at least
    `(plaintext_max_len * 1.4) + 64` to leave room for Fernet's
    base64 overhead and the 32-byte header — for a 256-char plaintext
    cap, 512 chars on disk is comfortable.
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(length, *args, **kwargs)

    def process_bind_param(  # type: ignore[override]
        self, value: str | None, dialect: Any
    ) -> str | None:
        if value is None:
            return None
        return get_cipher().encrypt(value)

    def process_result_value(  # type: ignore[override]
        self, value: str | None, dialect: Any
    ) -> str | None:
        if value is None:
            return None
        return get_cipher().decrypt(value)
