"""Camera-profile catalog regression tests.

Why these matter: the catalog encodes RTSP path knowledge for ~20
camera brands. A subtle template typo means dozens of customers can't
connect their cameras and the failure is camera-specific (so it
escapes our own dogfooding). Lock the templates with table-driven
tests so any future "oops, I edited the wrong slash" gets caught at
PR time.
"""

from __future__ import annotations

import pytest

from app.services.camera_profiles import (
    build_candidate_urls,
    get_profile,
    list_profiles,
)

pytestmark = pytest.mark.unit


# Stable golden URLs for the most common brands. If any of these
# expectations change, that's a deliberate breaking change to the
# catalog — update the test in the same commit so reviewers see it.
_BRAND_GOLDEN_CASES = [
    (
        "hikvision",
        {
            "host": "10.0.0.5",
            "username": "admin",
            "password": "Pass@1",
            "channel": "1",
            "stream_id": "main",
        },
        # Password "@" → "%40" via URL encoding.
        "rtsp://admin:Pass%401@10.0.0.5:554/Streaming/Channels/101",
    ),
    (
        "hikvision",
        {
            "host": "10.0.0.5",
            "username": "admin",
            "password": "Pass@1",
            "stream_id": "sub",
        },
        "rtsp://admin:Pass%401@10.0.0.5:554/Streaming/Channels/102",
    ),
    (
        "dahua",
        {
            "host": "192.168.1.10",
            "username": "admin",
            "password": "x",
            "stream_id": "main",
        },
        "rtsp://admin:x@192.168.1.10:554/cam/realmonitor?channel=1&subtype=0",
    ),
    (
        "cpplus",
        {"host": "192.168.1.20", "username": "admin", "password": "x"},
        "rtsp://admin:x@192.168.1.20:554/cam/realmonitor?channel=1&subtype=0",
    ),
    (
        "axis",
        {"host": "10.1.1.10", "username": "root", "password": "axisroot"},
        "rtsp://root:axisroot@10.1.1.10:554/axis-media/media.amp",
    ),
    (
        "reolink",
        {"host": "10.0.0.50", "username": "admin", "password": "p"},
        "rtsp://admin:p@10.0.0.50:554/h264Preview_01_main",
    ),
    (
        "tplink_tapo",
        {"host": "192.168.0.50", "username": "cam_acct", "password": "p"},
        "rtsp://cam_acct:p@192.168.0.50:554/stream1",
    ),
    (
        "foscam",
        {"host": "10.0.0.7", "username": "admin", "password": "p"},
        # Foscam default port is 88, not 554 — regression-protected.
        "rtsp://admin:p@10.0.0.7:88/videoMain",
    ),
]


@pytest.mark.parametrize("brand,inputs,expected", _BRAND_GOLDEN_CASES)
def test_first_template_url_matches_golden(brand: str, inputs: dict, expected: str) -> None:
    """The FIRST template per brand must produce the golden URL —
    that's the variant we recommend in the docs and that ~95% of
    that brand's installs will work with on the first probe.
    """
    profile = get_profile(brand)
    assert profile is not None, f"profile {brand!r} missing"
    urls = build_candidate_urls(profile, **inputs)
    assert urls, "expected at least one candidate URL"
    assert urls[0] == expected, (
        f"first {brand} template drifted:\n  got:      {urls[0]}\n  expected: {expected}"
    )


def test_credentials_url_encoded() -> None:
    """`@`, `:`, `/`, and other userinfo-breaking characters in
    username/password MUST be percent-encoded so cv2/FFmpeg can parse
    the URL. A single un-encoded `@` in a password rejects every
    template silently — this is the #1 historical "why won't my
    camera connect" cause."""
    profile = get_profile("hikvision")
    assert profile is not None
    urls = build_candidate_urls(
        profile,
        host="10.0.0.5",
        username="user@corp.com",
        password="p/ass:word@!",
    )
    assert "user@corp.com" not in urls[0]  # raw @ would break parsing
    assert "user%40corp.com" in urls[0]
    assert "p%2Fass%3Aword%40%21" in urls[0]


def test_anonymous_rtsp_emits_no_userinfo() -> None:
    """Some cameras allow anonymous RTSP. With empty username we must
    NOT emit a leading `:@` — that's invalid URI syntax and rejects."""
    profile = get_profile("dahua")
    assert profile is not None
    urls = build_candidate_urls(profile, host="10.0.0.5", username="", password="")
    assert urls[0].startswith("rtsp://10.0.0.5:554/")
    assert "://:" not in urls[0]


def test_default_port_per_brand_used_when_port_unset() -> None:
    """`port=None` should fall through to the brand's default. Foscam
    uniquely uses 88 — proves the default is per-brand, not global."""
    foscam = get_profile("foscam")
    assert foscam is not None
    urls = build_candidate_urls(foscam, host="10.0.0.5", port=None)
    assert ":88/" in urls[0], urls[0]

    hik = get_profile("hikvision")
    assert hik is not None
    urls = build_candidate_urls(hik, host="10.0.0.5", port=None)
    assert ":554/" in urls[0], urls[0]


def test_explicit_port_overrides_default() -> None:
    """A user-supplied port wins over the brand default. Common case:
    NVR remapping RTSP to 8554 to avoid an ISP-blocked 554."""
    profile = get_profile("hikvision")
    assert profile is not None
    urls = build_candidate_urls(profile, host="10.0.0.5", port=8554, username="admin")
    assert ":8554/" in urls[0]


def test_get_profile_resolves_aliases() -> None:
    """Brand aliases (e.g. CP Plus for "cp", "cpp") let users find the
    right profile via marketing names. Case-insensitive."""
    assert get_profile("CPPLUS") is get_profile("cpplus")
    assert get_profile("cp") is get_profile("cpplus")  # alias
    assert get_profile("hik") is get_profile("hikvision")  # alias
    assert get_profile("nonexistent") is None
    assert get_profile("") is None


def test_generic_onvif_returns_many_templates() -> None:
    """Generic ONVIF is the last-resort fall-through; needs to try
    multiple well-known URL patterns. Lock the count so we don't
    accidentally drop one in a refactor."""
    profile = get_profile("onvif_generic")
    assert profile is not None
    urls = build_candidate_urls(profile, host="10.0.0.5", username="admin", password="x")
    assert len(urls) >= 6, f"Generic ONVIF should try several common paths; only got {len(urls)}"


def test_list_profiles_stable_alphabetical() -> None:
    """The UI dropdown shows brands in this order — must be stable
    across requests, not influenced by dict iteration order."""
    names = [p.name for p in list_profiles()]
    assert names == sorted(names, key=str.lower)
    # Known-present essentials.
    assert "Hikvision" in names
    assert "Dahua" in names
    assert "Generic ONVIF" in names
