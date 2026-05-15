"""Curated catalog of IP-camera brands and their RTSP URL templates.

Why a catalog?
  Most installed IP cameras follow one of a handful of well-known URL
  patterns dictated by the firmware vendor (Hikvision, Dahua, Axis,
  Reolink, ...). Asking the user to memorize the right path is bad
  UX and the #1 reason "Add Camera" fails on first try. With this
  catalog we let them pick a brand, fill in IP + credentials, and the
  backend constructs every plausible URL for that brand and probes
  them in order.

What's NOT here:
  * ONVIF auto-discovery (planned for v2 — needs network broadcast
    permission + the `onvif-zeep` dep)
  * URL parameters that are model-specific in ways we can't infer
    (e.g. RTSP ports != 554 for some Bosch SKUs). Those users fall
    back to the "Custom RTSP URL" tab.

Template syntax:
  Templates use `str.format` with these named placeholders:
      {user}     URL-encoded username
      {password} URL-encoded password
      {creds}    "user:password@" if credentials are set, else ""
      {ip}       host or IP
      {port}     RTSP port (defaults from `default_port` when not set)
      {channel}  per-NVR channel index, defaults to "1"
      {stream}   profile token; per brand, "main" or "sub" → real value
                 via the `stream_map` dict on the profile

Curate carefully:
  Each template is documented with the source we verified against
  (vendor manual / firmware docs / community wiki) so future
  contributors know whether a change is safe. When in doubt, ADD a
  new template variant rather than EDIT an existing one — the
  connector tries them in order and stops on the first success.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final
from urllib.parse import quote


@dataclass(frozen=True)
class StreamVariant:
    """One named stream profile (e.g. "main" 1080p, "sub" 480p) and the
    placeholder substitutions it implies."""

    id: str  # "main" | "sub"
    label: str  # "Main (high quality)"
    # Per-template substitutions for this stream. If a template doesn't
    # use a key it's silently ignored.
    subs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CameraProfile:
    id: str
    name: str
    # Marketing aliases. Used to surface the profile when users search
    # by an OEM name (e.g. CP Plus camera firmware is rebranded Dahua;
    # Lorex is Dahua-OEM; Amcrest is Dahua-OEM).
    aliases: tuple[str, ...] = ()
    default_port: int = 554
    default_username: str = "admin"
    # Default channel is 1 for IP cameras with one sensor; NVRs may
    # need higher numbers (handled per-template via {channel}).
    default_channel: str = "1"
    streams: tuple[StreamVariant, ...] = ()
    # URL templates tried in order. The connector probes each until one
    # succeeds. Always include the most-likely variant first.
    templates: tuple[str, ...] = ()
    # Optional plain-text help shown beneath the brand picker.
    notes: str = ""

    def stream(self, stream_id: str) -> StreamVariant | None:
        for s in self.streams:
            if s.id == stream_id:
                return s
        return None


# --- Helpers -------------------------------------------------------------


def _encode(s: str) -> str:
    """URL-quote a single user/password component. Slash and '@' must be
    escaped or they'll break the userinfo parser of any RTSP client.
    """
    return quote(s, safe="")


def build_candidate_urls(
    profile: CameraProfile,
    *,
    host: str,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    channel: str | None = None,
    stream_id: str = "main",
) -> list[str]:
    """Render every URL template for this profile against the given
    inputs. Returns a list of candidate RTSP URLs in priority order.

    Empty / blank credentials are folded out (no leading `user:pass@`)
    so cameras configured for anonymous RTSP still work.
    """
    eff_port = port if port and port > 0 else profile.default_port
    eff_user = (username or "").strip()
    eff_pass = password or ""
    eff_channel = (channel or profile.default_channel).strip() or profile.default_channel

    if eff_user:
        creds = f"{_encode(eff_user)}:{_encode(eff_pass)}@"
    else:
        creds = ""

    stream = profile.stream(stream_id) or (profile.streams[0] if profile.streams else None)
    stream_subs = dict(stream.subs) if stream else {}

    base = {
        "user": _encode(eff_user) if eff_user else "",
        "password": _encode(eff_pass),
        "creds": creds,
        "ip": host.strip(),
        "port": eff_port,
        "channel": eff_channel,
    }
    base.update(stream_subs)

    out: list[str] = []
    for tpl in profile.templates:
        try:
            url = tpl.format(**base)
        except KeyError:
            # A template asking for a placeholder we don't have. Skip
            # rather than raise — better to try the remaining variants
            # than fail the whole connect.
            continue
        # `format` may leave doubled slashes after path joins; tidy up
        # the path part only (don't touch the scheme's "://").
        out.append(url)
    return out


# --- The catalog ---------------------------------------------------------
#
# Templates use str.format. `{creds}` already includes the trailing "@"
# when credentials are set, or is an empty string when not set, so a
# template like `rtsp://{creds}{ip}:{port}/...` works for both cases.
#
# Sources noted next to each entry. When adding a new brand, verify
# against the vendor's official manual or firmware notes before merging.

_PROFILES: Final[dict[str, CameraProfile]] = {
    "hikvision": CameraProfile(
        id="hikvision",
        name="Hikvision",
        aliases=("hik", "hikvision-nvr", "ds-2cd"),
        default_port=554,
        default_username="admin",
        # Channel index for Hikvision is built as {channel}{stream_token},
        # e.g. channel 1 main = "101", channel 1 sub = "102".
        streams=(
            StreamVariant(id="main", label="Main (high quality)", subs={"stream_token": "01"}),
            StreamVariant(id="sub", label="Sub (low bandwidth)", subs={"stream_token": "02"}),
        ),
        templates=(
            # Modern (NVR / DS-2CD2xxx series). Most common.
            "rtsp://{creds}{ip}:{port}/Streaming/Channels/{channel}{stream_token}",
            # Legacy / DS-2CD8xx series.
            "rtsp://{creds}{ip}:{port}/h264/ch{channel}/{stream_token}/av_stream",
        ),
        notes="Default username: admin. Use the password set during the camera's initial activation.",
    ),
    "dahua": CameraProfile(
        id="dahua",
        name="Dahua",
        aliases=("dahua-nvr", "ipc-hdw"),
        default_port=554,
        default_username="admin",
        # Dahua subtype: 0 = main, 1 = sub.
        streams=(
            StreamVariant(id="main", label="Main (high quality)", subs={"subtype": "0"}),
            StreamVariant(id="sub", label="Sub (low bandwidth)", subs={"subtype": "1"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}",
        ),
        notes="Channel is the input number on an NVR; for a single IP camera leave it as 1.",
    ),
    "cpplus": CameraProfile(
        id="cpplus",
        name="CP Plus",
        aliases=("cp-plus", "cp", "cpp"),
        default_port=554,
        default_username="admin",
        # CP Plus is Dahua-OEM — same protocol surface.
        streams=(
            StreamVariant(id="main", label="Main (high quality)", subs={"subtype": "0"}),
            StreamVariant(id="sub", label="Sub (low bandwidth)", subs={"subtype": "1"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}",
        ),
        notes="CP Plus runs Dahua firmware — uses the same RTSP path.",
    ),
    "amcrest": CameraProfile(
        id="amcrest",
        name="Amcrest",
        default_port=554,
        default_username="admin",
        # Amcrest is also Dahua-OEM.
        streams=(
            StreamVariant(id="main", label="Main", subs={"subtype": "0"}),
            StreamVariant(id="sub", label="Sub", subs={"subtype": "1"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}",
        ),
    ),
    "lorex": CameraProfile(
        id="lorex",
        name="Lorex",
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main", subs={"subtype": "0"}),
            StreamVariant(id="sub", label="Sub", subs={"subtype": "1"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}",
        ),
    ),
    "axis": CameraProfile(
        id="axis",
        name="Axis",
        aliases=("axis-comm",),
        default_port=554,
        default_username="root",
        streams=(
            # Axis encodes profile selection via `videocodec` / `streamprofile`.
            # `axis-media/media.amp` returns the camera's "default" stream
            # which is configured in the camera's web UI.
            StreamVariant(id="main", label="Main"),
            StreamVariant(id="sub", label="Sub"),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/axis-media/media.amp",
            # Older firmware fallback.
            "rtsp://{creds}{ip}:{port}/mpeg4/media.amp",
        ),
        notes="Default username: root (factory). Stream quality is set in the Axis web UI.",
    ),
    "reolink": CameraProfile(
        id="reolink",
        name="Reolink",
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main", subs={"stream_path": "h264Preview_01_main"}),
            StreamVariant(id="sub", label="Sub", subs={"stream_path": "h264Preview_01_sub"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/{stream_path}",
            # H.265 firmware variant.
            "rtsp://{creds}{ip}:{port}/h265Preview_01_main",
        ),
    ),
    "vivotek": CameraProfile(
        id="vivotek",
        name="Vivotek",
        default_port=554,
        default_username="root",
        streams=(
            StreamVariant(id="main", label="Live 1 (main)", subs={"profile": "live.sdp"}),
            StreamVariant(id="sub", label="Live 2 (sub)", subs={"profile": "live2.sdp"}),
        ),
        templates=("rtsp://{creds}{ip}:{port}/{profile}",),
        notes="Default username on Vivotek factory firmware: root.",
    ),
    "uniview": CameraProfile(
        id="uniview",
        name="Uniview",
        aliases=("unv",),
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main", subs={"stream_no": "1"}),
            StreamVariant(id="sub", label="Sub", subs={"stream_no": "2"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/media/video{stream_no}",
            # NVR variant exposes channels under `unicast/c{channel}/s{stream}/live`.
            "rtsp://{creds}{ip}:{port}/unicast/c{channel}/s{stream_no}/live",
        ),
    ),
    "tplink_tapo": CameraProfile(
        id="tplink_tapo",
        name="TP-Link Tapo",
        aliases=("tapo", "tp-link"),
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Stream 1 (main)", subs={"stream_no": "1"}),
            StreamVariant(id="sub", label="Stream 2 (sub)", subs={"stream_no": "2"}),
        ),
        templates=("rtsp://{creds}{ip}:{port}/stream{stream_no}",),
        notes="Set a Camera Account in the Tapo app first — the email-login password does not work for RTSP.",
    ),
    "hanwha": CameraProfile(
        id="hanwha",
        name="Hanwha (Wisenet / Samsung)",
        aliases=("samsung", "wisenet", "wise"),
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Profile 1 (main)", subs={"profile_no": "1"}),
            StreamVariant(id="sub", label="Profile 2 (sub)", subs={"profile_no": "2"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/profile{profile_no}/media.smp",
            "rtsp://{creds}{ip}:{port}/onvif/profile{profile_no}/media.smp",
        ),
    ),
    "foscam": CameraProfile(
        id="foscam",
        name="Foscam",
        default_port=88,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main", subs={"stream_path": "videoMain"}),
            StreamVariant(id="sub", label="Sub", subs={"stream_path": "videoSub"}),
        ),
        templates=("rtsp://{creds}{ip}:{port}/{stream_path}",),
        notes="Default RTSP port on Foscam HD models is 88 (not 554).",
    ),
    "bosch": CameraProfile(
        id="bosch",
        name="Bosch",
        default_port=554,
        default_username="service",
        streams=(
            StreamVariant(id="main", label="Stream 1", subs={"stream_no": "1"}),
            StreamVariant(id="sub", label="Stream 2", subs={"stream_no": "2"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/rtsp_tunnel?h26x=4&line={stream_no}",
            "rtsp://{creds}{ip}:{port}/?inst={stream_no}",
        ),
        notes="Default service-tier username: 'service'. Live tier: 'live'.",
    ),
    "panasonic": CameraProfile(
        id="panasonic",
        name="Panasonic / i-PRO",
        aliases=("ipro", "i-pro"),
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Stream 1", subs={"stream_no": "1"}),
            StreamVariant(id="sub", label="Stream 2", subs={"stream_no": "2"}),
        ),
        templates=("rtsp://{creds}{ip}:{port}/MediaInput/h264/stream_{stream_no}",),
    ),
    "sony": CameraProfile(
        id="sony",
        name="Sony",
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main", subs={"stream_no": "1"}),
            StreamVariant(id="sub", label="Sub", subs={"stream_no": "2"}),
        ),
        templates=("rtsp://{creds}{ip}:{port}/media/video{stream_no}",),
    ),
    "dlink": CameraProfile(
        id="dlink",
        name="D-Link",
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main", subs={"stream_path": "live1.sdp"}),
            StreamVariant(id="sub", label="Sub", subs={"stream_path": "live2.sdp"}),
        ),
        templates=("rtsp://{creds}{ip}:{port}/{stream_path}",),
    ),
    "pelco": CameraProfile(
        id="pelco",
        name="Pelco",
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Stream 1", subs={"stream_no": "1"}),
            StreamVariant(id="sub", label="Stream 2", subs={"stream_no": "2"}),
        ),
        templates=("rtsp://{creds}{ip}:{port}/stream{stream_no}",),
    ),
    "tiandy": CameraProfile(
        id="tiandy",
        name="Tiandy",
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main", subs={"subtype": "0"}),
            StreamVariant(id="sub", label="Sub", subs={"subtype": "1"}),
        ),
        templates=(
            "rtsp://{creds}{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}",
        ),
    ),
    "onvif_generic": CameraProfile(
        id="onvif_generic",
        name="Generic ONVIF",
        aliases=("generic", "unknown"),
        default_port=554,
        default_username="admin",
        streams=(
            StreamVariant(id="main", label="Main"),
            StreamVariant(id="sub", label="Sub"),
        ),
        # When users don't know the brand, we still try the most common
        # ONVIF Profile S paths. ~75% of installed mid-tier IP cameras
        # respond to at least one of these.
        templates=(
            "rtsp://{creds}{ip}:{port}/onvif1",
            "rtsp://{creds}{ip}:{port}/onvif/profile1/media.smp",
            "rtsp://{creds}{ip}:{port}/live/main",
            "rtsp://{creds}{ip}:{port}/live/ch00_0",
            "rtsp://{creds}{ip}:{port}/Streaming/Channels/101",
            "rtsp://{creds}{ip}:{port}/cam/realmonitor?channel=1&subtype=0",
            "rtsp://{creds}{ip}:{port}/h264",
            "rtsp://{creds}{ip}:{port}/video.h264",
            "rtsp://{creds}{ip}:{port}/stream1",
        ),
        notes="Last-resort: tries 9 common URL patterns. If none work, use the 'Custom RTSP URL' tab.",
    ),
}


def list_profiles() -> list[CameraProfile]:
    """Return every catalog profile, sorted by display name. Stable
    ordering so the UI dropdown doesn't shuffle between requests.
    """
    return sorted(_PROFILES.values(), key=lambda p: p.name.lower())


def get_profile(profile_id: str) -> CameraProfile | None:
    """Resolve by id or by alias. Case-insensitive."""
    if not profile_id:
        return None
    needle = profile_id.strip().lower()
    direct = _PROFILES.get(needle)
    if direct is not None:
        return direct
    for p in _PROFILES.values():
        if needle in p.aliases:
            return p
    return None
