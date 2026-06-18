import json

import numpy as np
import pytest

from mq3drecon.dataio import DataIO
from mq3drecon.models import CoordinateSystem, Side


def write_mruk_sample(project_dir, side: Side, *, valid: bool = True, bad_file_size: bool = False):
    prefix = side.name.lower()
    camera_position = "Left" if side == Side.LEFT else "Right"
    rgba_dir = project_dir / f"{prefix}_camera_mruk_rgba"
    rgba_dir.mkdir(parents=True)
    timestamp = 123456789
    file_name = f"{timestamp}.rgba"
    width = 2
    height = 2
    rgba = np.arange(width * height * 4, dtype=np.uint8)
    if bad_file_size:
        rgba = rgba[:-1]
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
        f"1.0,2.0,3.0,0.0,0.0,0.0,1.0,{str(valid).lower()},true,true,"
        f"{width},{height},4,16,16,true,true,\n"
    )
    (project_dir / f"{prefix}_camera_mruk_frame_metadata.csv").write_text(csv, encoding="utf-8")


def test_mruk_color_dataset_uses_metadata_pose_and_rgba_frames(tmp_path):
    (tmp_path / "session_info.json").write_text(
        json.dumps({"sessionFormatVersion": 2, "captureBackend": "MRUK"}),
        encoding="utf-8",
    )
    write_mruk_sample(tmp_path, Side.LEFT)

    dataset = DataIO(tmp_path).color.load_color_dataset(Side.LEFT, use_cache=False)

    assert dataset.directory_relative_path == "left_camera_mruk_rgba"
    assert dataset.image_file_names.tolist() == ["123456789.rgba"]
    assert dataset.timestamps.tolist() == [123456789]
    assert dataset.fx.tolist() == [10.0]
    assert dataset.fy.tolist() == [11.0]
    assert dataset.cx.tolist() == [1.0]
    assert dataset.cy.tolist() == [1.5]
    assert dataset.transforms.coordinate_system == CoordinateSystem.UNITY
    np.testing.assert_allclose(dataset.transforms.positions, [[1.0, 2.0, 3.0]])
    np.testing.assert_allclose(dataset.transforms.rotations, [[0.0, 0.0, 0.0, 1.0]])

    image = DataIO(tmp_path).color.load_color_image(dataset, 0)

    assert image.shape == (2, 2, 4)


def test_mruk_color_dataset_skips_invalid_frames(tmp_path):
    (tmp_path / "session_info.json").write_text(
        json.dumps({"sessionFormatVersion": 2, "captureBackend": "MRUK"}),
        encoding="utf-8",
    )
    write_mruk_sample(tmp_path, Side.LEFT, valid=False)

    with pytest.raises(ValueError, match="No valid MRUK color frames"):
        DataIO(tmp_path).color.load_color_dataset(Side.LEFT, use_cache=False)


def test_mruk_color_dataset_rejects_bad_rgba_file_size(tmp_path):
    (tmp_path / "session_info.json").write_text(
        json.dumps({"sessionFormatVersion": 2, "captureBackend": "MRUK"}),
        encoding="utf-8",
    )
    write_mruk_sample(tmp_path, Side.LEFT, bad_file_size=True)

    with pytest.raises(ValueError, match="Invalid MRUK RGBA file size"):
        DataIO(tmp_path).color.load_color_dataset(Side.LEFT, use_cache=False)
