"""Password hashing and JWT issue/verify.

Migrated from `python-jose` (unmaintained, last release 2022, two
unpatched CVEs) to `PyJWT` 2.x — actively maintained, narrower
attack surface, drop-in API differences confined to this module.

Intentional design points:

* `verify_password` logs unexpected exceptions instead of swallowing.
  The previous `try/except ValueError: return False` would mask the
  passlib-vs-bcrypt-4.1 attribute drift that locks every admin out
  with no signal at all. Now the failure mode is loud.

* Token decode is tight on which exception types it accepts; PyJWT
  raises a hierarchy under `InvalidTokenError`, so a single
  `except InvalidTokenError` catches expired / bad-signature /
  malformed-payload uniformly.

* `algorithms=[…]` is a list (PyJWT requires it). Never accept "none".
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from app.config import get_settings
from app.core.exceptions import AuthenticationError

log = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time password compare.

    Returns False on any verification failure — but unlike the previous
    implementation, every unexpected exception is LOGGED rather than
    silently swallowed. The previous swallow-and-return-False masked
    the bcrypt-4.1 / passlib AttributeError class of bugs, where every
    login silently fails with no log line and no observable difference
    between "wrong password" and "library broken".
    """
    try:
        return _pwd_context.verify(password, hashed)
    except ValueError:
        # Malformed hash on the row — could be from a manually-edited
        # admin row or a corrupted backup restore. Log so an operator
        # can spot the offending account.
        log.warning("verify_password: malformed stored hash (treated as mismatch)")
        return False
    except Exception:
        # Library-level breakage (passlib/bcrypt version drift,
        # missing native dep, etc.). Log loudly — without this you
        # get a silent platform-wide auth outage.
        log.exception(
            "verify_password: unexpected exception from passlib/bcrypt; "
            "if this fires repeatedly, every login is failing silently "
            "and the underlying library is broken"
        )
        return False


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(tz=UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Verify signature + standard claims (exp, iat) and return the
    payload. Raises `AuthenticationError` on any failure — never leaks
    the underlying jwt exception class to the caller.

    Multi-key verification:
      The current `JWT_SECRET_KEY` always tries first (>99% hit rate).
      On signature mismatch we walk `JWT_PREVIOUS_KEYS` so tokens
      minted under a recently-rotated key still verify for their
      remaining lifetime. ONLY the signature failure mode falls
      through — every other failure (expired, malformed, missing
      claim) is conclusive on the first key and re-raises immediately.
    """
    settings = get_settings()
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "require": ["sub", "exp", "iat", "type"],
    }

    # Tuple of keys to try, in priority order: current first, then
    # any rotated-out keys still inside the token-lifetime grace window.
    keys: tuple[str, ...] = (
        settings.JWT_SECRET_KEY,
        *settings.JWT_PREVIOUS_KEYS,
    )

    last_error: InvalidTokenError | None = None
    for key in keys:
        try:
            return jwt.decode(
                token,
                key,
                algorithms=[settings.JWT_ALGORITHM],
                options=options,
            )
        except jwt.exceptions.InvalidSignatureError as exc:
            # Try the next key. Capture the error so if every key
            # rejects we raise the LAST one (most-recent) for clarity.
            last_error = exc
            continue
        except InvalidTokenError as exc:
            # Expired / malformed / missing claim — wrong-key won't
            # change those outcomes, so don't waste time iterating.
            raise AuthenticationError("Invalid or expired token") from exc

    raise AuthenticationError("Invalid or expired token") from last_error
