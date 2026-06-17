from typing import Optional
import numpy as np
import cv2
import pandas as pd

from mq3drecon.config.project_path_config import DepthPathConfig
from mq3drecon.models.camera_dataset import DepthDataset
from mq3drecon.models.confidence_map import ConfidenceMap
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem, Transforms
from mq3drecon.utils.depth_utils import compute_depth_camera_params, convert_depth_to_linear


class DepthDataIO:
    def __init__(self, depth_path_config: DepthPathConfig):
        self.depth_path_config = depth_path_config
        self.depth_descriptors: dict[Side, pd.DataFrame] = {}
        self.depth_datasets: dict[Side, DepthDataset] = {}

    
    def load_depth_descriptors(self, side: Side) -> pd.DataFrame:
        if side in self.depth_descriptors:
            return self.depth_descriptors[side]

        csv_path = self.depth_path_config.get_depth_descriptor_path(side=side)
        side_descriptors = pd.read_csv(csv_path)

        self.depth_descriptors[side] = side_descriptors

        return side_descriptors
    

    def load_depth_map(self, 
        side: Side, 
        timestamp: int,
        width: int,
        height: int,
        near: float,
        far: float,        
    ) -> Optional[np.ndarray]:
        depth_map_path = self.depth_path_config.get_depth_map_path(side=side, timestamp=timestamp)

        if not depth_map_path.exists():
            return None

        depth_array = np.fromfile(depth_map_path, dtype='<f4').reshape((height, width))

        if not self.is_depth_map_valid(depth_map=depth_array):
            return None

        depth_map = convert_depth_to_linear(depth_array, near, far)

        return depth_map
    

    def load_depth_map_by_index(self,
        side: Side,
        dataset: DepthDataset,
        index: int
    ) -> Optional[np.ndarray]:
        if index < 0 or index >= len(dataset.timestamps):
            return None

        timestamp = dataset.timestamps[index]
        width = dataset.widths[index]
        height = dataset.heights[index]
        near = dataset.nears[index]
        far = dataset.fars[index]

        return self.load_depth_map(
            side=side,
            timestamp=timestamp,
            width=width,
            height=height,
            near=near,
            far=far
        )


    def is_depth_map_valid(self, depth_map: np.ndarray) -> bool:
        is_valid = (depth_map != 0).any() and (depth_map != 1).any()
        is_valid = is_valid and not np.isnan(depth_map).any()
        is_valid = is_valid and (depth_map >= 0).all()

        return bool(is_valid)
    

    def exists_depth_confidence_map_dir(self, side: Side) -> bool:
        return self.depth_path_config.get_depth_confidence_map_dir_path(side=side).exists()
     

    def load_confidence_map(self, side: Side, timestamp: int) -> Optional[ConfidenceMap]:
        confidence_map_path = self.depth_path_config.get_depth_confidence_map_path(side=side, timestamp=timestamp)

        if confidence_map_path.exists():
            try:
                data = np.load(confidence_map_path)
                return ConfidenceMap(
                    confidence_map=data['confidence_map'],
                    valid_count=data['valid_count']
                )
            except Exception as e:
                print(f"[Error] Failed to load confidence map for {side.name} at timestamp {timestamp}: {e}")


    def save_confidence_map(self, side: Side, timestamp: int, confidence_map: ConfidenceMap) -> None:
        confidence_map_path = self.depth_path_config.get_depth_confidence_map_path(side=side, timestamp=timestamp)
        confidence_map_path.parent.mkdir(parents=True, exist_ok=True)

        np.savez(
            confidence_map_path,
            confidence_map=confidence_map.confidence_map,
            valid_count=confidence_map.valid_count
        )


    def load_depth_dataset(self, side: Side, use_cache: bool = True) -> DepthDataset:
        if side in self.depth_datasets:
            print(f"[Info] Depth dataset already loaded. Returning loaded dataset...")
            return self.depth_datasets[side]
        
        depth_dataset_path = self.depth_path_config.get_depth_dataset_path(side=side)

        if use_cache and depth_dataset_path.exists():
            print(f"[Info] Loading cached depth dataset for {side.name} from {depth_dataset_path} ...")

            try:
                depth_dataset = DepthDataset.load(depth_dataset_path)
                self.depth_datasets[side] = depth_dataset
                return depth_dataset

            except Exception as e:
                print(f"[Error] Depth dataset cache is corrupted or invalid. Rebuilding cache from the original source...\n{e}")

        else:
            print(f"[Info] Depth dataset not found. Rebuilding cache from the original source...")


        depth_dataset = self.build_depth_dataset(side=side)
        self.depth_datasets[side] = depth_dataset

        depth_dataset.save(depth_dataset_path)

        return depth_dataset
    

    def load_optimized_depth_dataset(self, side: Side) -> Optional[DepthDataset]:
        optimized_depth_dataset_path = self.depth_path_config.get_optimized_depth_dataset_path(side=side)

        if optimized_depth_dataset_path.exists():
            try:
                return DepthDataset.load(optimized_depth_dataset_path)
            except Exception as e:
                print(f"[Error] Depth dataset cache is corrupted or invalid.\n{e}")

        print(f"[Info] Depth dataset not found.")


    def save_optimized_depth_dataset(self, side: Side, dataset: DepthDataset):
        optimized_depth_dataset_path = self.depth_path_config.get_optimized_depth_dataset_path(side=side)

        dataset.save(optimized_depth_dataset_path)

    
    def build_depth_dataset(self, side: Side) -> DepthDataset:
        df = self.load_depth_descriptors(side=side)

        directory_path = self.depth_path_config.get_depth_dir(side=side)
        directory_relative_path = self.depth_path_config.get_relative_path(path=directory_path)

        depth_filenames = []
        timestamps = []
        fxs = []
        fys = []
        cxs = []
        cys = []
        positions = []
        rotations = []
        widths = []
        heights = []
        nears = []
        fars = []

        for _, row in df.iterrows():
            timestamp = int(row['timestamp_ms'])
            width = int(row['width'])
            height = int(row['height'])

            near = float(row['near_z'])
            far = float(row['far_z'])

            left = float(row['fov_left_angle_tangent'])
            right = float(row['fov_right_angle_tangent'])
            top = float(row['fov_top_angle_tangent'])
            bottom = float(row['fov_down_angle_tangent'])

            position = np.array([
                row['create_pose_location_x'],
                row['create_pose_location_y'],
                row['create_pose_location_z'],
            ])

            rotation = np.array([
                row['create_pose_rotation_x'],
                row['create_pose_rotation_y'],
                row['create_pose_rotation_z'],
                row['create_pose_rotation_w'],
            ])

            fx, fy, cx, cy = compute_depth_camera_params(
                left, right, top, bottom, width, height
            )

            depth_map = self.load_depth_map(
                side=side,
                timestamp=timestamp,
                width=width,
                height=height,
                near=near,
                far=far,
            )

            if depth_map is None:
                continue

            depth_filename = self.depth_path_config.get_depth_map_filename(timestamp=timestamp)

            depth_filenames.append(depth_filename)
            timestamps.append(timestamp)
            fxs.append(fx)
            fys.append(fy)
            cxs.append(cx)
            cys.append(cy)
            positions.append(position)
            rotations.append(rotation)
            widths.append(width)
            heights.append(height)
            nears.append(near)
            fars.append(far)

        depth_dataset = DepthDataset(
            directory_relative_path=str(directory_relative_path),
            image_file_names=np.array(depth_filenames),
            timestamps=np.array(timestamps),
            fx=np.array(fxs),
            fy=np.array(fys),
            cx=np.array(cxs),
            cy=np.array(cys),
            transforms=Transforms(
                coordinate_system=CoordinateSystem.UNITY,
                positions=np.array(positions),
                rotations=np.array(rotations)
            ),
            widths=np.array(widths),
            heights=np.array(heights),
            nears=np.array(nears),
            fars=np.array(fars)
        )

        return depth_dataset
    

    def save_linear_depth_map(self, depth_map: np.ndarray, side: Side, timestamp: int):
        linear_depth_dir = self.depth_path_config.get_linear_depth_dir(side=side)
        linear_depth_dir.mkdir(parents=True, exist_ok=True)

        file_path = linear_depth_dir / f'{timestamp}.png'

        cv2.imwrite(str(file_path), depth_map)