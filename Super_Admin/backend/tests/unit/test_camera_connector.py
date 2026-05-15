"""Camera connector — orchestration, redaction, failure diagnostics.

`probe_rtsp` is mocked so these tests are millisecond-fast and have
no network dependency.
"""

from __future__ import annotations

import pytest

from app.services import camera_connector
from app.services.camera_connector import (
    _diagnose_failure,
    _redact_url,
    smart_connect,
)
from app.workers.rtsp_probe import ProbeOutcome

pytestmark = pytest.mark.unit


# --- Redaction -----------------------------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        # Normal case
        (
            "rtsp://admin:supersecret@10.0.0.5:554/path",
            "rtsp://admin:***@10.0.0.5:554/path",
        ),
        # Encoded password
        (
            "rtsp://user%40corp:p%40ss@10.0.0.5/x",
            "rtsp://user%40corp:***@10.0.0.5/x",
        ),
        # No userinfo — passthrough
        ("rtsp://10.0.0.5/path", "rtsp://10.0.0.5/path"),
        # No colon in userinfo (anonymous user) — passthrough
        ("rtsp://just-user@10.0.0.5/path", "rtsp://just-user@10.0.0.5/path"),
        # Empty input — defensive
        ("", ""),
    ],
)
def test_redact_url(url: str, expected: str) -> None:
    assert _redact_url(url) == expected


# --- Failure diagnostics -------------------------------------------------


def _attempt(err: str | None, ok: bool = False) -> camera_connector.CandidateAttempt:
    return camera_connector.CandidateAttempt(
        template_index=0,
        url="rtsp://u:***@h/x",
        redacted_url="rtsp://u:***@h/x",
        outcome=ProbeOutcome(ok=ok, width=None, height=None, elapsed_ms=10, error=err),
    )


def test_diagnose_all_open_failures_means_unreachable() -> None:
    msg = _diagnose_failure([_attempt("could not open stream")] * 3)
    assert "wrong IP" in msg.lower() or "wrong ip" in msg or "firewall" in msg


def test_diagnose_open_plus_no_frame_means_brand_mismatch() -> None:
    msg = _diagnose_failure(
        [
            _attempt("opened but no frame received"),
            _attempt("could not open stream"),
        ]
    )
    assert "brand" in msg.lower() or "channel" in msg.lower()


def test_diagnose_401_implies_auth() -> None:
    msg = _diagnose_failure([_attempt("401 Unauthorized")])
    assert "auth" in msg.lower() or "password" in msg.lower()


def test_diagnose_empty_attempts() -> None:
    """Defensive: connector said it had URLs to try but ended up with
    none. The diagnoser must not raise."""
    msg = _diagnose_failure([])
    assert isinstance(msg, str)
    assert msg  # non-empty


# --- smart_connect orchestration ----------------------------------------


def test_smart_connect_unknown_profile_returns_clean_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = smart_connect(
        profile_id="this-brand-does-not-exist",
        host="10.0.0.5",
    )
    assert result.ok is False
    assert "Unknown" in (result.error or "")
    assert result.attempts == []


def test_smart_connect_returns_first_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two templates exist for Hikvision — if the FIRST one fails and
    the SECOND one succeeds, smart_connect must stop there and return
    the second URL with template_index=1 in the success result."""
    # Make the first attempt fail, the second succeed.
    call_count = {"n": 0}

    def fake_probe(url: str, *, timeout_ms: int) -> ProbeOutcome:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return ProbeOutcome(False, None, None, 100, "could not open stream")
        return ProbeOutcome(True, 1920, 1080, 250, None)

    monkeypatch.setattr(camera_connector, "probe_rtsp", fake_probe)

    result = smart_connect(
        profile_id="hikvision",
        host="10.0.0.5",
        username="admin",
        password="p",
    )
    assert result.ok is True
    assert result.success_template_index == 1
    assert result.width == 1920 and result.height == 1080
    assert len(result.attempts) == 2
    # First attempt failed, second succeeded.
    assert result.attempts[0].outcome.ok is False
    assert result.attempts[1].outcome.ok is True
    # Returned URL is the SECOND (legacy) Hikvision template — the
    # one that actually returned a frame. Lock the path so a future
    # template reorder doesn't silently break the legacy fallback.
    assert "/h264/ch1/01/av_stream" in (result.success_url or "")


def test_smart_connect_all_failures_returns_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        camera_connector,
        "probe_rtsp",
        lambda url, *, timeout_ms: ProbeOutcome(False, None, None, 100, "could not open stream"),
    )
    result = smart_connect(
        profile_id="hikvision",
        host="10.0.0.5",
        username="admin",
        password="p",
    )
    assert result.ok is False
    assert result.success_url is None
    # Tried both Hikvision templates.
    assert len(result.attempts) == 2
    # Diagnoser produced a useful message.
    assert "URL" in (result.error or "") or "reach" in (result.error or "")


def test_smart_connect_stops_at_total_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If a profile had a pathological 100 templates, the connector
    must NOT spend forever trying — it should stop at the total
    budget and return what it has."""

    # Make each fake attempt take a huge synthetic elapsed_ms so the
    # budget triggers after one call.
    def fake_probe(url: str, *, timeout_ms: int) -> ProbeOutcome:
        return ProbeOutcome(False, None, None, 90_000, "could not open stream")

    monkeypatch.setattr(camera_connector, "probe_rtsp", fake_probe)
    result = smart_connect(
        profile_id="onvif_generic",
        host="10.0.0.5",
        username="admin",
        password="p",
    )
    assert result.ok is False
    # First attempt eats the entire budget; remaining ~8 must NOT run.
    assert len(result.attempts) == 1, (
        f"Connector should bail after total budget — ran {len(result.attempts)} attempts"
    )
