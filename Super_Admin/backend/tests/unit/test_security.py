"""JWT and password security regression tests.

After migrating from python-jose → PyJWT and adding multi-key
verification, every login depends on this module being correct.
These tests are the contract.
"""

from __future__ import annotations

import time

import jwt as pyjwt
import pytest
from freezegun import freeze_time

from app.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


# --- Round-trip ----------------------------------------------------------


def test_round_trip_returns_subject_and_extras() -> None:
    tok = create_access_token("admin-1", extra={"role": "SUPER_ADMIN"})
    payload = decode_token(tok)
    assert payload["sub"] == "admin-1"
    assert payload["role"] == "SUPER_ADMIN"
    assert payload["type"] == "access"
    # iat & exp are populated and exp is in the future.
    assert payload["iat"] < payload["exp"]


def test_subject_coerced_to_string() -> None:
    """JWT spec: `sub` is a string. Integer subjects must coerce so
    callers don't have to remember to `str()`."""
    tok = create_access_token(42)
    payload = decode_token(tok)
    assert payload["sub"] == "42"
    assert isinstance(payload["sub"], str)


# --- Expiry --------------------------------------------------------------


def test_expired_token_rejected() -> None:
    with freeze_time("2026-05-09 10:00:00"):
        tok = create_access_token("admin-1")
    # Jump well past JWT_ACCESS_TOKEN_EXPIRE_MINUTES (default 1440 = 24h).
    with freeze_time("2026-05-15 10:00:00"), pytest.raises(AuthenticationError):
        decode_token(tok)


def test_token_valid_just_before_expiry() -> None:
    with freeze_time("2026-05-09 10:00:00"):
        tok = create_access_token("admin-1")
    # 23h59 in — still valid.
    with freeze_time("2026-05-10 09:59:00"):
        payload = decode_token(tok)
        assert payload["sub"] == "admin-1"


# --- Tamper / malformed --------------------------------------------------


def test_tampered_signature_rejected() -> None:
    tok = create_access_token("admin-1")
    # Flip a byte in the signature (last segment).
    head, payload, sig = tok.split(".")
    bad = sig[:-1] + ("a" if sig[-1] != "a" else "b")
    bad_tok = f"{head}.{payload}.{bad}"
    with pytest.raises(AuthenticationError):
        decode_token(bad_tok)


def test_garbage_token_rejected() -> None:
    with pytest.raises(AuthenticationError):
        decode_token("not-a-jwt")


def test_alg_none_rejected() -> None:
    """Defense against the classic 'alg=none' attack — ANY decoder
    that accepts unsigned tokens is a critical vuln. PyJWT does the
    right thing as long as we pass `algorithms=[…]` (which we do).
    """
    get_settings()
    # Hand-craft an unsigned token with the user's claims.
    alg_none = pyjwt.encode(
        {"sub": "admin-1", "iat": int(time.time()), "exp": int(time.time()) + 60, "type": "access"},
        key="",
        algorithm="none",
    )
    with pytest.raises(AuthenticationError):
        decode_token(alg_none)


def test_missing_required_claim_rejected() -> None:
    """A signed token that lacks `type` (one of our required claims)
    must be rejected — defends against tokens minted by a broken
    issuer that forgot to set the discriminator."""
    settings = get_settings()
    bad = pyjwt.encode(
        {"sub": "admin-1", "iat": int(time.time()), "exp": int(time.time()) + 60},
        # Missing `type`.
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(AuthenticationError):
        decode_token(bad)


# --- Multi-key fallback --------------------------------------------------


def test_token_signed_with_previous_key_still_verifies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Operator rotated JWT_SECRET_KEY today. Tokens minted under
    yesterday's key (still inside their lifetime) must continue to
    verify until the operator drops the old key from
    JWT_PREVIOUS_KEYS — otherwise rotation = forced logout."""
    settings = get_settings()

    old_key = "old-rotated-secret-9d1e3871a9d3d1eb85e7f0113b3791b5"
    # Simulate token from yesterday's key.
    old_token = pyjwt.encode(
        {
            "sub": "admin-2",
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
            "type": "access",
        },
        old_key,
        algorithm=settings.JWT_ALGORITHM,
    )

    # Without registering it: decode must FAIL (signature mismatch).
    monkeypatch.setattr(settings, "JWT_PREVIOUS_KEYS", [])
    with pytest.raises(AuthenticationError):
        decode_token(old_token)

    # After registering as a previous key: decode must SUCCEED.
    monkeypatch.setattr(settings, "JWT_PREVIOUS_KEYS", [old_key])
    payload = decode_token(old_token)
    assert payload["sub"] == "admin-2"


def test_expired_old_key_token_still_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multi-key fallback must NOT bypass expiry — rotation grace
    only papers over signature mismatches, not expired claims."""
    settings = get_settings()
    old_key = "another-old-key-for-this-test-only-padding-padding"
    expired = pyjwt.encode(
        {
            "sub": "admin-2",
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,  # one hour ago
            "type": "access",
        },
        old_key,
        algorithm=settings.JWT_ALGORITHM,
    )
    monkeypatch.setattr(settings, "JWT_PREVIOUS_KEYS", [old_key])
    with pytest.raises(AuthenticationError):
        decode_token(expired)


# --- Password hashing ----------------------------------------------------


def test_hash_then_verify_round_trip() -> None:
    h = hash_password("CorrectHorseBatteryStaple")
    assert verify_password("CorrectHorseBatteryStaple", h) is True
    assert verify_password("wrong", h) is False


def test_verify_with_malformed_hash_returns_false_no_raise() -> None:
    """Production safety: a manually-edited admin row with a corrupt
    hash must NOT take down the auth path. Old behavior would silently
    fail; new behavior logs + returns False."""
    assert verify_password("anything", "this-is-not-a-bcrypt-hash") is False
