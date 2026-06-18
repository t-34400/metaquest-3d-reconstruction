from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any


class CaptureBackend(Enum):
    NATIVE_CAMERA2 = "NativeCamera2"
    MRUK = "MRUK"


@dataclass(frozen=True)
class SessionInfo:
    capture_backend: CaptureBackend
    session_format_version: int | None = None


def load_session_info(project_dir: Path) -> SessionInfo:
    path = Path(project_dir) / "session_info.json"
    if not path.exists():
        return SessionInfo(capture_backend=CaptureBackend.NATIVE_CAMERA2)

    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    backend_value = data.get("captureBackend")
    try:
        backend = CaptureBackend(backend_value)
    except ValueError as exc:
        raise ValueError(f"Unsupported captureBackend in {path}: {backend_value!r}") from exc

    return SessionInfo(
        capture_backend=backend,
        session_format_version=data.get("sessionFormatVersion"),
    )
