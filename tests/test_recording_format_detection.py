import json

import pytest

from mq3drecon.dataio import CaptureBackend, load_session_info


def test_missing_session_info_defaults_to_legacy_camera2(tmp_path):
    info = load_session_info(tmp_path)

    assert info.capture_backend == CaptureBackend.NATIVE_CAMERA2
    assert info.session_format_version is None


def test_loads_mruk_session_info(tmp_path):
    (tmp_path / "session_info.json").write_text(
        json.dumps({"sessionFormatVersion": 2, "captureBackend": "MRUK"}),
        encoding="utf-8",
    )

    info = load_session_info(tmp_path)

    assert info.capture_backend == CaptureBackend.MRUK
    assert info.session_format_version == 2


def test_unsupported_capture_backend_raises_explicit_error(tmp_path):
    (tmp_path / "session_info.json").write_text(
        json.dumps({"captureBackend": "Unknown"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported captureBackend"):
        load_session_info(tmp_path)
