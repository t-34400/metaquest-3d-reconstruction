import json

import cv2
import numpy as np

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side


def write_legacy_format_info(project_dir, side: Side, *, width: int = 2, height: int = 2):
    prefix = side.name.lower()
    (project_dir / f"{prefix}_camera_image_format.json").write_text(
        json.dumps({
            "width": width,
            "height": height,
            "format": "YUV_420_888",
            "planes": [
                {"bufferSize": width * height, "rowStride": width, "pixelStride": 1},
                {"bufferSize": (width // 2) * (height // 2), "rowStride": width // 2, "pixelStride": 1},
                {"bufferSize": (width // 2) * (height // 2), "rowStride": width // 2, "pixelStride": 1},
            ],
            "baseTime": {"baseMonoTimeNs": 0, "baseUnixTimeMs": 0},
        }),
        encoding="utf-8",
    )


def test_load_rgb_reads_legacy_rgb_png_before_raw_yuv(tmp_path):
    (tmp_path / "left_camera_rgb").mkdir()
    (tmp_path / "left_camera_raw").mkdir()
    write_legacy_format_info(tmp_path, Side.LEFT)

    timestamp = 100
    y = np.full(4, 235, dtype=np.uint8)
    u = np.full(1, 128, dtype=np.uint8)
    v = np.full(1, 128, dtype=np.uint8)
    np.concatenate([y, u, v]).tofile(tmp_path / "left_camera_raw" / f"{timestamp}.yuv")

    expected_rgb = np.array([[[12, 34, 56]]], dtype=np.uint8)
    cv2.imwrite(
        str(tmp_path / "left_camera_rgb" / f"{timestamp}.png"),
        cv2.cvtColor(expected_rgb, cv2.COLOR_RGB2BGR),
    )

    rgb = DataIO(tmp_path).color.load_rgb(Side.LEFT, timestamp)

    np.testing.assert_array_equal(rgb, expected_rgb)


def test_load_rgb_falls_back_to_legacy_raw_yuv_when_png_is_absent(tmp_path):
    (tmp_path / "left_camera_raw").mkdir()
    write_legacy_format_info(tmp_path, Side.LEFT)

    timestamp = 100
    y = np.full(4, 235, dtype=np.uint8)
    u = np.full(1, 128, dtype=np.uint8)
    v = np.full(1, 128, dtype=np.uint8)
    raw_data = np.concatenate([y, u, v])
    raw_data.tofile(tmp_path / "left_camera_raw" / f"{timestamp}.yuv")

    rgb = DataIO(tmp_path).color.load_rgb(Side.LEFT, timestamp)
    expected = cv2.cvtColor(
        cv2.cvtColor(raw_data.reshape(3, 2), cv2.COLOR_YUV2BGR_I420),
        cv2.COLOR_BGR2RGB,
    )

    assert rgb.flags.c_contiguous
    np.testing.assert_array_equal(rgb, expected)


def test_get_rgb_timestamps_includes_legacy_raw_yuv_and_png(tmp_path):
    (tmp_path / "left_camera_rgb").mkdir()
    (tmp_path / "left_camera_raw").mkdir()
    (tmp_path / "left_camera_rgb" / "100.png").write_bytes(b"")
    (tmp_path / "left_camera_raw" / "200.yuv").write_bytes(b"")

    assert DataIO(tmp_path).color.get_rgb_timestamps(Side.LEFT) == [100, 200]
