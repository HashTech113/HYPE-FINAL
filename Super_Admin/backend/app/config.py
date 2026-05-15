from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str

    # API
    APP_NAME: str = "AI CCTV Attendance"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = False

    # Security
    # `JWT_SECRET_KEY` is the active SIGNING key. New tokens are
    # always signed with this. To rotate without logging everyone out
    # at once, also set `JWT_PREVIOUS_KEYS` (CSV) to the previous
    # signing keys; tokens minted under those still verify until the
    # last one is dropped from the env. After the longest token
    # lifetime has passed, you can safely retire the old keys.
    JWT_SECRET_KEY: str
    JWT_PREVIOUS_KEYS: Annotated[list[str], NoDecode] = []
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    @field_validator("JWT_PREVIOUS_KEYS", mode="before")
    @classmethod
    def _split_previous_keys(cls, v: object) -> list[str] | object:
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v

    # Bootstrap admin (set in .env; omit to skip auto-creation)
    BOOTSTRAP_ADMIN_USERNAME: str | None = None
    BOOTSTRAP_ADMIN_PASSWORD: str | None = None

    # Symmetric encryption key for sensitive at-rest column values
    # (currently `cameras.password`). Fernet format — 32 random bytes,
    # base64-encoded. When unset the system runs in PASSTHROUGH mode
    # (legacy plaintext); a startup WARNING is emitted so production
    # operators notice. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    CAMERA_SECRET_KEY: str | None = None

    # Face recognition
    FACE_MODEL_NAME: str = "buffalo_l"
    FACE_MODEL_ROOT: str = "./storage/models"
    FACE_PROVIDER: Literal[
        "CPUExecutionProvider",
        "CUDAExecutionProvider",
        "DmlExecutionProvider",
    ] = "CPUExecutionProvider"
    # buffalo_l's RetinaNet ONNX baked at 640x640 — DirectML fails on
    # other sizes ("Reshape_223 parameter is incorrect"). Stick with 640.
    FACE_DET_SIZE: int = 640
    FACE_MATCH_THRESHOLD: float = 0.45
    FACE_MIN_QUALITY: float = 0.50
    FACE_TRAIN_MIN_IMAGES: int = 5
    FACE_TRAIN_MAX_IMAGES: int = 20

    # Camera pipeline
    CAMERA_FPS: int = 15
    CAMERA_COOLDOWN_SECONDS: int = 2
    CAMERA_HEALTH_INTERVAL_SECONDS: int = 10
    CAMERA_HEARTBEAT_TIMEOUT_SECONDS: int = 30
    # Faster timeouts beat the camera/network glitches that produce
    # multi-second freezes in the live preview. With 2s read timeout,
    # FFmpeg returns from cap.read() within 2s of any silent stream;
    # then we reconnect with a 3s connect ceiling.
    RTSP_CONNECT_TIMEOUT_MS: int = 3000
    RTSP_READ_TIMEOUT_MS: int = 2000
    RTSP_RECONNECT_MAX_SECONDS: int = 10
    # Stall watchdog: if no frame has landed in the buffer in this long,
    # force-release `cv2.VideoCapture` to unblock a stuck native read().
    # This is a belt-and-braces guard on top of FFmpeg's stimeout.
    RTSP_FRAME_STALL_SECONDS: float = 3.0
    # Forced periodic reconnect to defeat slow FFmpeg/decoder state
    # drift over multi-day uptime. The reconnect itself takes ~1s on a
    # healthy network and does not interrupt the latest frame served by
    # the buffer (it's just briefly stale until the new cap produces).
    RTSP_RECYCLE_HOURS: float = 6.0

    # Live preview tuning. Defaults chosen for 4 cameras × 2 viewers on
    # a low-end GPU box: smooth motion at modest CPU. JPEG encode cost
    # is ~linear in pixel count, so capping `max_width` is the single
    # biggest win for 1080p sub-streams.
    PREVIEW_MAX_WIDTH: int = 960
    PREVIEW_DEFAULT_QUALITY: int = 72
    PREVIEW_DEFAULT_FPS: int = 12

    # Storage
    STORAGE_ROOT: str = "./storage"
    TRAINING_DIR: str = "./storage/training_images"
    SNAPSHOT_DIR: str = "./storage/snapshots"
    UNKNOWNS_DIR: str = "./storage/unknowns"
    # Employee profile photos. One JPEG per employee, named `<id>.jpg`.
    EMPLOYEE_IMAGE_DIR: str = "./storage/employees"
    # Hard cap on the raw upload size. Anything larger is rejected with
    # 413 before we touch disk. The server re-encodes to JPEG quality 85
    # at max 1024×1024, so the on-disk file is much smaller than this.
    EMPLOYEE_IMAGE_MAX_BYTES: int = 8 * 1024 * 1024  # 8 MiB
    # Final on-disk dimensions and quality after re-encode. 1024 covers
    # any reasonable display use without bloating storage.
    EMPLOYEE_IMAGE_MAX_DIM: int = 1024
    EMPLOYEE_IMAGE_JPEG_QUALITY: int = 85

    # Timezone
    TIMEZONE: str = "Asia/Kolkata"

    # CORS — comma-separated origin list via env (CORS_ALLOW_ORIGINS=http://a,http://b)
    # NoDecode disables pydantic-settings' default JSON-parse of list types, so the
    # field_validator below sees the raw env string and can split on commas.
    CORS_ALLOW_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> list[str] | object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_MAX_BYTES: int = 104857600
    LOG_BACKUP_COUNT: int = 5
    # `text` (default) — human-readable, good for local dev.
    # `json`           — one JSON object per line, for log aggregators
    #                    (Loki / Datadog / CloudWatch / Grafana Cloud).
    LOG_FORMAT: Literal["text", "json"] = "text"

    @field_validator("FACE_MATCH_THRESHOLD")
    @classmethod
    def _threshold_range(cls, v: float) -> float:
        if not 0.0 < v < 1.0:
            raise ValueError("FACE_MATCH_THRESHOLD must be in (0, 1)")
        return v

    @field_validator("FACE_TRAIN_MIN_IMAGES", "FACE_TRAIN_MAX_IMAGES")
    @classmethod
    def _positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be positive")
        return v

    def ensure_directories(self) -> None:
        for path in (
            self.STORAGE_ROOT,
            self.TRAINING_DIR,
            self.SNAPSHOT_DIR,
            self.UNKNOWNS_DIR,
            self.EMPLOYEE_IMAGE_DIR,
            self.FACE_MODEL_ROOT,
            self.LOG_DIR,
        ):
            Path(path).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()  # type: ignore[call-arg]
    s.ensure_directories()
    return s
