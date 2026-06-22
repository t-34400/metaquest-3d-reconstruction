from __future__ import annotations

from typing import Any

import numpy as np

from mq3drecon.config.project_path_config import RGBDPathConfig
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.dataio.image_data_io import ImageDataIO
from mq3drecon.models.camera_dataset import CameraDataset, DepthDataset
from mq3drecon.models.side import Side


class RGBDDataIO:
    def __init__(
        self,
        image_data_io: ImageDataIO,
        depth_data_io: DepthDataIO,
        rgbd_path_config: RGBDPathConfig,
    ):
        self.image_data_io = image_data_io
        self.depth_data_io = depth_data_io
        self.rgbd_path_config = rgbd_path_config

    def load_color_aligned_depth(self, side: Side, timestamp: int) -> np.ndarray:
        color_aligned_depth_path = self.rgbd_path_config.get_color_aligned_depth_path(side=side, timestamp=timestamp)

        if not color_aligned_depth_path.exists():
            raise FileNotFoundError(f"Color-aligned depth file not found: {color_aligned_depth_path}")

        return np.load(color_aligned_depth_path)

    def load_color_aligned_depth_by_index(
        self,
        side: Side,
        dataset: DepthDataset,
        index: int,
    ) -> np.ndarray | None:
        if index < 0 or index >= len(dataset.timestamps):
            return None

        depth = self.load_color_aligned_depth(side=side, timestamp=int(dataset.timestamps[index]))
        return self._validate_and_normalize_depth(depth=depth, dataset=dataset, index=index, label="Color-aligned")

    def build_color_aligned_depth_dataset(
        self,
        side: Side,
        color_dataset: CameraDataset,
        near_m: float = 0.0,
        far_m: float = np.inf,
    ) -> DepthDataset:
        indices = []
        depth_filenames = []
        for index, timestamp in enumerate(color_dataset.timestamps):
            timestamp_int = int(timestamp)
            path = self.rgbd_path_config.get_color_aligned_depth_path(side=side, timestamp=timestamp_int)
            if path.exists():
                indices.append(index)
                depth_filenames.append(path.name)

        if not indices:
            depth_dir = self.rgbd_path_config.get_color_aligned_depth_dir(side=side)
            raise FileNotFoundError(f"No color-aligned depth maps found for {side.name}: {depth_dir}")

        source = color_dataset[np.asarray(indices, dtype=np.int64)]
        return DepthDataset(
            directory_relative_path=str(self.rgbd_path_config.get_color_aligned_depth_dir(side=side).relative_to(self.rgbd_path_config.project_dir)),
            image_file_names=np.asarray(depth_filenames),
            timestamps=source.timestamps,
            fx=source.fx,
            fy=source.fy,
            cx=source.cx,
            cy=source.cy,
            transforms=source.transforms,
            widths=source.widths,
            heights=source.heights,
            nears=np.full(len(indices), near_m, dtype=np.float32),
            fars=np.full(len(indices), far_m, dtype=np.float32),
        )

    def build_color_aligned_rgbd_datasets(
        self,
        side: Side,
        color_dataset: CameraDataset,
        near_m: float = 0.0,
        far_m: float = np.inf,
    ) -> tuple[CameraDataset, DepthDataset]:
        depth_dataset = self.build_color_aligned_depth_dataset(
            side=side,
            color_dataset=color_dataset,
            near_m=near_m,
            far_m=far_m,
        )
        timestamp_to_color_index = {int(timestamp): index for index, timestamp in enumerate(color_dataset.timestamps)}
        color_indices = [timestamp_to_color_index[int(timestamp)] for timestamp in depth_dataset.timestamps]
        return color_dataset[np.asarray(color_indices, dtype=np.int64)], depth_dataset

    def save_color_aligned_depth(self, depth_map: np.ndarray, side: Side, timestamp: int):
        color_aligned_depth_path = self.rgbd_path_config.get_color_aligned_depth_path(side=side, timestamp=timestamp)
        color_aligned_depth_path.parent.mkdir(parents=True, exist_ok=True)

        np.save(color_aligned_depth_path, depth_map)

    def save_rectified_stereo_depth(self, depth_map: np.ndarray, side: Side, timestamp: int) -> None:
        path = self.rgbd_path_config.get_rectified_stereo_depth_path(side=side, timestamp=timestamp)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, depth_map.astype(np.float32, copy=False))

    def save_rectified_stereo_depth_dataset(self, dataset: DepthDataset, side: Side) -> None:
        dataset.save(self.rgbd_path_config.get_rectified_stereo_depth_dataset_path(side=side))

    def load_rectified_stereo_depth_dataset(self, side: Side) -> DepthDataset:
        path = self.rgbd_path_config.get_rectified_stereo_depth_dataset_path(side=side)
        if not path.exists():
            raise FileNotFoundError(f"Rectified stereo depth dataset not found: {path}")
        return DepthDataset.load(path)

    def load_rectified_stereo_depth(self, side: Side, timestamp: int) -> np.ndarray:
        path = self.rgbd_path_config.get_rectified_stereo_depth_path(side=side, timestamp=timestamp)
        if not path.exists():
            raise FileNotFoundError(f"Rectified stereo depth file not found: {path}")
        return np.load(path)

    def load_rectified_stereo_depth_by_index(
        self,
        side: Side,
        dataset: DepthDataset,
        index: int,
    ) -> np.ndarray | None:
        if index < 0 or index >= len(dataset.timestamps):
            return None
        depth = self.load_rectified_stereo_depth(side=side, timestamp=int(dataset.timestamps[index]))
        return self._validate_and_normalize_depth(depth=depth, dataset=dataset, index=index, label="Rectified stereo")

    def build_rectified_stereo_rgbd_datasets(
        self,
        side: Side = Side.LEFT,
        near_m: float = 0.0,
        far_m: float = np.inf,
    ) -> tuple[CameraDataset, DepthDataset]:
        color_dataset = self.image_data_io.load_rectified_stereo_color_dataset(side=side)
        depth_dataset = self.load_rectified_stereo_depth_dataset(side=side)
        existing = {
            int(timestamp): i
            for i, timestamp in enumerate(depth_dataset.timestamps)
            if self.rgbd_path_config.get_rectified_stereo_depth_path(side=side, timestamp=int(timestamp)).exists()
        }
        color_indices = []
        depth_indices = []
        for color_index, timestamp in enumerate(color_dataset.timestamps):
            depth_index = existing.get(int(timestamp))
            if depth_index is not None:
                color_indices.append(color_index)
                depth_indices.append(depth_index)
        if not color_indices:
            raise FileNotFoundError(f"No rectified stereo RGBD frames found for {side.name}")
        matched_depth = depth_dataset[np.asarray(depth_indices, dtype=np.int64)]
        matched_depth.nears = np.full(len(depth_indices), near_m, dtype=np.float32)
        matched_depth.fars = np.full(len(depth_indices), far_m, dtype=np.float32)
        return color_dataset[np.asarray(color_indices, dtype=np.int64)], matched_depth

    def save_stereo_rectification(self, **metadata: Any) -> None:
        path = self.rgbd_path_config.get_stereo_rectification_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, **metadata)

    def load_stereo_rectification(self) -> dict[str, np.ndarray]:
        path = self.rgbd_path_config.get_stereo_rectification_path()
        if not path.exists():
            raise FileNotFoundError(f"Stereo rectification metadata not found: {path}")
        return dict(np.load(path, allow_pickle=False))

    @staticmethod
    def _validate_and_normalize_depth(
        depth: np.ndarray,
        dataset: DepthDataset,
        index: int,
        label: str,
    ) -> np.ndarray:
        expected_shape = (int(dataset.heights[index]), int(dataset.widths[index]))
        if depth.shape != expected_shape:
            raise ValueError(
                f"{label} depth shape does not match dataset resolution: "
                f"timestamp={dataset.timestamps[index]}, expected={expected_shape}, got={depth.shape}"
            )
        depth = depth.astype(np.float32, copy=False)
        return np.where(np.isfinite(depth) & (depth > 0.0), depth, 0.0).astype(np.float32, copy=False)
