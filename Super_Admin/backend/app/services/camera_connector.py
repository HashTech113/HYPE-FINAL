"""Smart RTSP connector — turns a brand+IP+credentials tuple into a
working RTSP URL by probing every candidate template the brand profile
knows about, in priority order, and stopping at the first that succeeds.

Returns rich diagnostics (every URL attempted with its individual
outcome) so the UI can show "we tried these 3 templates, the second one
worked" — invaluable when supporting non-technical users on first
install.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.core.logger import get_logger
from app.services.camera_profiles import (
    CameraProfile,
    build_candidate_urls,
    get_profile,
)
from app.workers.rtsp_probe import ProbeOutcome, probe_rtsp

log = get_logger(__name__)


@dataclass
class CandidateAttempt:
    """One URL attempt during a connect — used both for telemetry and
    surfaced to the UI so users can see which template variant worked.

    `redacted_url` is the same URL with the password masked out — never
    log the unredacted form.
    """

    template_index: int
    url: str
    redacted_url: str
    outcome: ProbeOutcome


@dataclass
class ConnectResult:
    """Outcome of a smart-connect attempt. `success_url` is the first
    template that returned a frame; `attempts` lists every URL we tried
    in order so the UI can render diagnostic detail on failure.
    """

    ok: bool
    profile_id: str
    success_url: str | None
    success_template_index: int | None
    width: int | None
    height: int | None
    elapsed_ms: int
    attempts: list[CandidateAttempt]
    error: str | None


# Per-attempt timeout. The connector tries up to N templates in series,
# so this needs to be small enough that a 9-template "Generic ONVIF"
# fall-through still completes in reasonable wall time. 3s × 9 = 27s
# worst case — paired with a 90s axios timeout on the client, that
# leaves comfortable headroom even on slow networks. A successful probe
# typically returns in <500ms, so this only matters when probing a
# wrong/unreachable URL.
_PER_ATTEMPT_TIMEOUT_MS: Final[int] = 3000

# Hard cap on total connector time. Defends against pathological inputs
# (e.g. a custom profile that ever ships with too many templates) that
# could otherwise blow past the client's request timeout. We bail out
# early after this many ms even if untried templates remain.
_TOTAL_BUDGET_MS: Final[int] = 60_000


def _redact_url(url: str) -> str:
    """Mask the password in `rtsp://user:pass@host/...` → `rtsp://user:***@host/...`.
    Used everywhere the URL gets logged or returned to the API client.
    """
    try:
        scheme_end = url.find("://")
        if scheme_end == -1:
            return url
        rest_start = scheme_end + 3
        at = url.find("@", rest_start)
        if at == -1:
            return url
        userinfo = url[rest_start:at]
        colon = userinfo.find(":")
        if colon == -1:
            return url
        masked = f"{userinfo[:colon]}:***"
        return url[:rest_start] + masked + url[at:]
    except Exception:
        return url


def smart_connect(
    *,
    profile_id: str,
    host: str,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    channel: str | None = None,
    stream_id: str = "main",
    per_attempt_timeout_ms: int = _PER_ATTEMPT_TIMEOUT_MS,
) -> ConnectResult:
    """Resolve a working RTSP URL for `profile_id` against the supplied
    inputs. Probes every URL the brand profile generates, in order, and
    stops at the first that returns a frame.

    Returns a `ConnectResult` whether or not any candidate worked —
    callers should check `.ok`. Never raises for connectivity failures
    (only for invalid inputs).
    """
    profile: CameraProfile | None = get_profile(profile_id)
    if profile is None:
        return ConnectResult(
            ok=False,
            profile_id=profile_id,
            success_url=None,
            success_template_index=None,
            width=None,
            height=None,
            elapsed_ms=0,
            attempts=[],
            error=f"Unknown camera profile '{profile_id}'",
        )

    urls = build_candidate_urls(
        profile,
        host=host,
        port=port,
        username=username,
        password=password,
        channel=channel,
        stream_id=stream_id,
    )
    if not urls:
        return ConnectResult(
            ok=False,
            profile_id=profile.id,
            success_url=None,
            success_template_index=None,
            width=None,
            height=None,
            elapsed_ms=0,
            attempts=[],
            error="Profile produced no candidate URLs (input is incomplete)",
        )

    attempts: list[CandidateAttempt] = []
    total_elapsed = 0
    for idx, url in enumerate(urls):
        if total_elapsed >= _TOTAL_BUDGET_MS:
            log.warning(
                "Connect [%s] hit total budget (%d ms) after %d/%d attempts",
                profile.name,
                _TOTAL_BUDGET_MS,
                idx,
                len(urls),
            )
            break
        outcome = probe_rtsp(url, timeout_ms=per_attempt_timeout_ms)
        total_elapsed += outcome.elapsed_ms
        attempt = CandidateAttempt(
            template_index=idx,
            url=url,
            redacted_url=_redact_url(url),
            outcome=outcome,
        )
        attempts.append(attempt)
        log.info(
            "Connect attempt [%s/%d] %s → ok=%s elapsed=%dms err=%s",
            profile.name,
            idx + 1,
            attempt.redacted_url,
            outcome.ok,
            outcome.elapsed_ms,
            outcome.error,
        )
        if outcome.ok:
            return ConnectResult(
                ok=True,
                profile_id=profile.id,
                success_url=url,
                success_template_index=idx,
                width=outcome.width,
                height=outcome.height,
                elapsed_ms=total_elapsed,
                attempts=attempts,
                error=None,
            )

    return ConnectResult(
        ok=False,
        profile_id=profile.id,
        success_url=None,
        success_template_index=None,
        width=None,
        height=None,
        elapsed_ms=total_elapsed,
        attempts=attempts,
        error=_diagnose_failure(attempts),
    )


def _diagnose_failure(attempts: list[CandidateAttempt]) -> str:
    """Turn a list of probe failures into a human-friendly hint about
    *why* nothing worked. Beats the generic "tried N patterns" message
    because the user usually wants the next-action.

    Heuristics (in priority order):
      * Every error matched "could not open stream" → host/port issue.
        Likely wrong IP, wrong port, firewall, or camera offline.
      * At least one "opened but no frame" + the rest "could not open"
        → host reachable, RTSP path wrong. Likely brand mis-pick.
      * Errors mention 401/403/auth → bad username/password.
      * Anything else → fall back to last error.
    """
    if not attempts:
        return "No candidates were probed (connector produced 0 URLs)"

    errors = [a.outcome.error or "" for a in attempts]
    n = len(attempts)

    auth_hits = sum(
        1
        for e in errors
        if any(k in e.lower() for k in ("401", "unauthorized", "forbidden", "403"))
    )
    if auth_hits > 0:
        return (
            f"Authentication failed on {auth_hits}/{n} URL pattern(s). "
            "Double-check the username and password. "
            "Some cameras require a separate 'Camera Account' or RTSP-only password."
        )

    open_failures = sum(1 for e in errors if "could not open" in e.lower())
    no_frame = sum(1 for e in errors if "no frame" in e.lower())

    if open_failures == n:
        return (
            f"Could not reach the camera on any of the {n} URL pattern(s) tried. "
            "Likely causes: wrong IP/hostname, wrong port, firewall blocking RTSP, "
            "or the camera is offline / not on the same network."
        )

    if no_frame > 0 and open_failures + no_frame == n:
        return (
            f"Connected to the host, but none of the {n} URL pattern(s) returned a frame. "
            "Likely the brand pick is wrong, or the channel/stream values don't match this model. "
            "Try the 'Custom RTSP URL' tab if you know the exact path."
        )

    last = errors[-1] or "unknown"
    return f"Tried {n} URL pattern(s); none returned a frame. Last error: {last}"
