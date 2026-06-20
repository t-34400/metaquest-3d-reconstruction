import json

import cv2
import numpy as np
import pytest

from mq3drecon.dataio import DataIO, MRUKImageDataIO
from mq3drecon.models import Side
from mq3drecon.processing.rgba_conversion import convert_rgba_directory
from mq3drecon.workflows import run_rgba_to_png


def _write_mruk_rgba_sample(project_dir, side: Side, timestamp: int = 123456789):
    prefix = side.name.lower()
    camera_position = "Left" if side == Side.LEFT else "Right"
    rgba_dir = project_dir / f"{prefix}_camera_mruk_rgba"
    rgba_dir.mkdir(parents=True)
    file_name = f"{timestamp}.rgba"
    width = 2
    height = 2
    rgba = np.arange(width * height * 4, dtype=np.uint8).reshape(height, width, 4)
    rgba.tofile(rgba_dir / file_name)

    (project_dir / f"{prefix}_camera_mruk_intrinsics.json").write_text(
        json.dumps({
            "backend": "MRUK",
            "cameraPosition": camera_position,
            "imageFormat": "RGBA32",
            "focalLength": {"x": 10.0, "y": 11.0},
            "principalPoint": {"x": 1.0, "y": 1.5},
            "resolution": {"width": width, "height": height},
        }),
        encoding="utf-8",
    )

    csv = (
        "frame_index,file_name,unix_time_ms,timestamp_us_realtime,width,height,format,"
        "camera_position,pose_pos_x,pose_pos_y,pose_pos_z,pose_rot_x,pose_rot_y,"
        "pose_rot_z,pose_rot_w,pose_ok,is_playing,is_updated_this_frame,"
        "current_resolution_width,current_resolution_height,pixel_count,"
        "colors_array_length,rgba_byte_count,get_texture_ok,get_colors_ok,error\n"
        f"1,{file_name},123,{timestamp},{width},{height},RGBA32,{camera_position},"
        "1.0,2.0,3.0,0.0,0.0,0.0,1.0,true,true,true,"
        f"{width},{height},4,16,16,true,true,\n"
    )
    (project_dir / f"{prefix}_camera_mruk_frame_metadata.csv").write_text(csv, encoding="utf-8")


def test_run_rgba_to_png_converts_mruk_rgba_frames_with_normalized_orientation(tmp_path):
    (tmp_path / "session_info.json").write_text(
        json.dumps({"sessionFormatVersion": 2, "captureBackend": "MRUK"}),
        encoding="utf-8",
    )
    _write_mruk_rgba_sample(tmp_path, Side.LEFT, 123456789)
    _write_mruk_rgba_sample(tmp_path, Side.RIGHT, 123456790)

    run_rgba_to_png(tmp_path)

    png = cv2.imread(str(tmp_path / "left_camera_mruk_rgba_png" / "123456789.png"), cv2.IMREAD_UNCHANGED)
    expected_rgba = np.flipud(np.arange(2 * 2 * 4, dtype=np.uint8).reshape(2, 2, 4))

    assert png.shape == (2, 2, 4)
    np.testing.assert_array_equal(png, cv2.cvtColor(expected_rgba, cv2.COLOR_RGBA2BGRA))
    assert (tmp_path / "right_camera_mruk_rgba_png" / "123456790.png").exists()


def test_convert_rgba_directory_rejects_bad_rgba_file_size(tmp_path):
    _write_mruk_rgba_sample(tmp_path, Side.LEFT, 123456789)
    _write_mruk_rgba_sample(tmp_path, Side.RIGHT, 123456790)
    (tmp_path / "left_camera_mruk_rgba" / "123456789.rgba").write_bytes(b"bad")

    with pytest.raises(Exception, match="MRUK RGBA conversion"):
        convert_rgba_directory(MRUKImageDataIO(DataIO(tmp_path).path_config.image))
