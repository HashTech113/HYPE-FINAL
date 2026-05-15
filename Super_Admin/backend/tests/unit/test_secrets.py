"""SecretCipher — Fernet wrapper with passthrough fallback.

Critical contract: NEVER lose user data. Every failure mode (no key,
bad key, wrong-key ciphertext, legacy plaintext) must return data
intact, never raise, and log enough to be diagnosable.
"""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.core.secrets import SecretCipher

pytestmark = pytest.mark.unit


# --- Encrypted mode ------------------------------------------------------


def test_encrypt_then_decrypt_round_trip(fernet_key: str) -> None:
    c = SecretCipher(fernet_key)
    assert c.enabled is True
    ct = c.encrypt("hunter2")
    assert ct.startswith("gAAAA"), f"unexpected ciphertext format: {ct[:10]}"
    assert ct != "hunter2"
    assert c.decrypt(ct) == "hunter2"


def test_encrypted_outputs_differ_for_same_input(fernet_key: str) -> None:
    """Fernet is non-deterministic by design (uses a random IV) — two
    encrypts of the same plaintext yield different ciphertexts. This
    is what makes encrypted columns infeasible to attack via known
    plaintext patterns."""
    c = SecretCipher(fernet_key)
    a = c.encrypt("same")
    b = c.encrypt("same")
    assert a != b
    assert c.decrypt(a) == c.decrypt(b) == "same"


def test_unicode_payload_round_trip(fernet_key: str) -> None:
    c = SecretCipher(fernet_key)
    weird = "Pässwørd-🎉-∑日本"
    assert c.decrypt(c.encrypt(weird)) == weird


# --- Legacy plaintext passthrough ----------------------------------------


def test_decrypt_legacy_plaintext_passthrough(fernet_key: str) -> None:
    """Pre-encryption rows in the DB look like normal strings, NOT
    Fernet tokens. Reading them must return them as-is so existing
    deployments keep working during the rollout window."""
    c = SecretCipher(fernet_key)
    legacy = "old-plain-password"
    # The decrypt path detects "doesn't look like Fernet" → passthrough.
    assert c.decrypt(legacy) == legacy


# --- Wrong key (rotation drift) ------------------------------------------


def test_wrong_key_returns_ciphertext_not_raise() -> None:
    """If the operator rotates CAMERA_SECRET_KEY without leaving the
    old one configured anywhere, ciphertext rows can't decrypt. We
    must NOT raise — that would crash every endpoint that reads a
    camera row. Instead return the raw ciphertext + log."""
    k1 = Fernet.generate_key().decode()
    k2 = Fernet.generate_key().decode()
    encrypter = SecretCipher(k1)
    decrypter = SecretCipher(k2)

    ct = encrypter.encrypt("secret")
    out = decrypter.decrypt(ct)
    # Neither raises nor returns the cleartext; returns ciphertext.
    assert out == ct


# --- Disabled mode (no key) ----------------------------------------------


def test_no_key_means_passthrough_both_directions() -> None:
    c = SecretCipher(None)
    assert c.enabled is False
    assert c.encrypt("x") == "x"
    assert c.decrypt("x") == "x"


def test_invalid_key_falls_back_to_disabled() -> None:
    """Operator typos a key (e.g. truncated paste). Cipher must NOT
    raise at construction — it must log + degrade to passthrough so
    the app boots."""
    c = SecretCipher("not-a-fernet-key")
    assert c.enabled is False
    assert c.encrypt("x") == "x"


def test_empty_string_key_treated_as_no_key() -> None:
    c = SecretCipher("")
    assert c.enabled is False
