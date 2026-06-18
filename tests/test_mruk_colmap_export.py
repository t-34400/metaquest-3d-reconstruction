import json

import cv2
import numpy as np

from mq3drecon.dataio import DataIO
from mq3drecon.models import Side
from mq3drecon.workflows.colmap_export import read_colmap_cameras_and_images


def write_mruk_sample(project_dir, side: Side):
    prefix = side.name.lower()
    camera_position = "Left" if side == Side.LEFT else "Right"
    rgba_dir = project_dir / f"{prefix}_camera_mruk_rgba"
    rgba_dir.mkdir(parents=True)
    timestamp = 123456789
    file_name = f"{timestamp}.rgba"
    width = 2
    height = 2
    rgba = np.array(
        [
            [[255, 0, 0, 255], [0, 255, 0, 255]],
            [[0, 0, 255, 255], [255, 255, 255, 255]],
        ],
        dtype=np.uint8,
    )
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
        f"1.0,2.0,3.0,0.0,0.0,0.0,1.0,true,true,true,"
        f"{width},{height},4,16,16,true,true,\n"
    )
    (project_dir / f"{prefix}_camera_mruk_frame_metadata.csv").write_text(csv, encoding="utf-8")


def test_colmap_export_writes_mruk_rgba_frames_as_png(tmp_path):
    (tmp_path / "session_info.json").write_text(
        json.dumps({"sessionFormatVersion": 2, "captureBackend": "MRUK"}),
        encoding="utf-8",
    )
    write_mruk_sample(tmp_path, Side.LEFT)

    data_io = DataIO(tmp_path)
    dataset = data_io.color.load_color_dataset(Side.LEFT, use_cache=False)
    image_output_dir = tmp_path / "colmap" / "images"
    image_output_dir.mkdir(parents=True)

    cameras, images = read_colmap_cameras_and_images(
        data_io=data_io,
        dataset_map={Side.LEFT: dataset},
        image_output_dir=image_output_dir,
    )

    assert list(cameras) == [0]
    assert list(images) == [0]
    output_path = image_output_dir / "LEFT_123456789.png"
    assert output_path.exists()
    exported = cv2.imread(str(output_path), cv2.IMREAD_UNCHANGED)
    assert exported.shape == (2, 2, 4)
