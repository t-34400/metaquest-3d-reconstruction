import numpy as np
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.dataio.image_data_io import ImageDataIO
from mq3drecon.config.project_path_config import RGBDPathConfig
from mq3drecon.models.camera_dataset import CameraDataset, DepthDataset
from mq3drecon.models.side import Side


class RGBDDataIO:
    def __init__(self,
        image_data_io: ImageDataIO,
        depth_data_io: DepthDataIO,
        rgbd_path_config: RGBDPathConfig
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
        expected_shape = (int(dataset.heights[index]), int(dataset.widths[index]))
        if depth.shape != expected_shape:
            raise ValueError(
                "Color-aligned depth shape does not match dataset resolution: "
                f"timestamp={dataset.timestamps[index]}, expected={expected_shape}, got={depth.shape}"
            )
        depth = depth.astype(np.float32, copy=False)
        return np.where(np.isfinite(depth) & (depth > 0.0), depth, 0.0).astype(np.float32, copy=False)

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

    def save_color_aligned_depth(self, depth_map: np.ndarray, side: Side, timestamp: int):
        color_aligned_depth_path = self.rgbd_path_config.get_color_aligned_depth_path(side=side, timestamp=timestamp)
        color_aligned_depth_path.parent.mkdir(parents=True, exist_ok=True)

        np.save(color_aligned_depth_path, depth_map)
