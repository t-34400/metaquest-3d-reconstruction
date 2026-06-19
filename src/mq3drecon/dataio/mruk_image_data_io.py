import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from mq3drecon.config.project_path_config import ImagePathConfig
from mq3drecon.models.camera_dataset import CameraDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem, Transforms


@dataclass(frozen=True)
class MRUKIntrinsics:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    image_format: str


class MRUKImageDataIO:
    REQUIRED_METADATA_COLUMNS = frozenset({
        "file_name",
        "timestamp_us_realtime",
        "width",
        "height",
        "rgba_byte_count",
        "pose_pos_x",
        "pose_pos_y",
        "pose_pos_z",
        "pose_rot_x",
        "pose_rot_y",
        "pose_rot_z",
        "pose_rot_w",
        "pose_ok",
        "get_texture_ok",
        "get_colors_ok",
    })

    def __init__(self, image_path_config: ImagePathConfig):
        self.image_path_config = image_path_config

    def load_intrinsics(self, side: Side) -> MRUKIntrinsics:
        path = self.image_path_config.get_mruk_intrinsics_json_path(side)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        resolution = data["resolution"]
        focal_length = data["focalLength"]
        principal_point = data["principalPoint"]

        return MRUKIntrinsics(
            width=int(resolution["width"]),
            height=int(resolution["height"]),
            fx=float(focal_length["x"]),
            fy=float(focal_length["y"]),
            cx=float(principal_point["x"]),
            cy=float(principal_point["y"]),
            image_format=str(data.get("imageFormat", data.get("format", "RGBA32"))),
        )

    def load_frame_metadata(self, side: Side) -> pd.DataFrame:
        path = self.image_path_config.get_mruk_frame_metadata_csv_path(side)
        df = pd.read_csv(path)
        missing = sorted(self.REQUIRED_METADATA_COLUMNS.difference(df.columns))
        if missing:
            raise ValueError(f"Missing MRUK frame metadata columns in {path}: {missing}")
        return df

    def load_rgba(self, side: Side, file_name: str, width: int, height: int) -> np.ndarray:
        path = self.image_path_config.get_mruk_rgba_dir(side) / file_name
        expected_size = int(width) * int(height) * 4
        actual_size = path.stat().st_size
        if actual_size != expected_size:
            raise ValueError(
                f"Invalid MRUK RGBA file size for {path}: expected {expected_size} bytes, got {actual_size}"
            )

        rgba = np.fromfile(path, dtype=np.uint8).reshape(int(height), int(width), 4)
        return np.ascontiguousarray(np.flipud(rgba))

    def build_color_dataset(self, side: Side) -> CameraDataset:
        intrinsics = self.load_intrinsics(side)
        metadata = self.load_frame_metadata(side)
        valid = metadata[
            metadata["pose_ok"].astype(bool)
            & metadata["get_texture_ok"].astype(bool)
            & metadata["get_colors_ok"].astype(bool)
        ].copy()

        if valid.empty:
            raise ValueError(f"No valid MRUK color frames found for side: {side.name}")

        valid = valid.sort_values("timestamp_us_realtime")
        directory_path = self.image_path_config.get_mruk_rgba_dir(side)
        directory_relative_path = self.image_path_config.get_relative_path(directory_path)

        file_names: list[str] = []
        timestamps: list[int] = []
        widths: list[int] = []
        heights: list[int] = []
        positions: list[list[float]] = []
        rotations: list[list[float]] = []

        for row in valid.itertuples(index=False):
            file_name = str(row.file_name)
            width = int(row.width)
            height = int(row.height)
            byte_count = int(row.rgba_byte_count)
            expected_byte_count = width * height * 4
            if byte_count != expected_byte_count:
                raise ValueError(
                    f"Invalid MRUK metadata byte count for {file_name}: "
                    f"expected {expected_byte_count}, got {byte_count}"
                )

            file_path = directory_path / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"MRUK RGBA frame listed in metadata does not exist: {file_path}")
            if file_path.stat().st_size != expected_byte_count:
                raise ValueError(
                    f"Invalid MRUK RGBA file size for {file_path}: "
                    f"expected {expected_byte_count} bytes, got {file_path.stat().st_size}"
                )

            file_names.append(file_name)
            timestamps.append(int(row.timestamp_us_realtime))
            widths.append(width)
            heights.append(height)
            positions.append([float(row.pose_pos_x), float(row.pose_pos_y), float(row.pose_pos_z)])
            rotations.append([float(row.pose_rot_x), float(row.pose_rot_y), float(row.pose_rot_z), float(row.pose_rot_w)])

        length = len(timestamps)
        transforms = Transforms(
            coordinate_system=CoordinateSystem.UNITY,
            positions=np.asarray(positions, dtype=np.float32),
            rotations=np.asarray(rotations, dtype=np.float32),
        )

        return CameraDataset(
            directory_relative_path=str(directory_relative_path),
            image_file_names=np.asarray(file_names),
            timestamps=np.asarray(timestamps, dtype=np.int64),
            fx=np.full(length, intrinsics.fx, dtype=np.float32),
            fy=np.full(length, intrinsics.fy, dtype=np.float32),
            cx=np.full(length, intrinsics.cx, dtype=np.float32),
            cy=np.full(length, intrinsics.cy, dtype=np.float32),
            transforms=transforms,
            widths=np.asarray(widths, dtype=np.int32),
            heights=np.asarray(heights, dtype=np.int32),
        )
