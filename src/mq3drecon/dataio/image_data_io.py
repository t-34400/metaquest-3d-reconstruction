import json
from typing import Optional
import numpy as np
import cv2
import pandas as pd
from scipy.spatial.transform import Rotation as R
from mq3drecon.config.project_path_config import ImagePathConfig
from mq3drecon.dataio.helpers.pose_interpolator import PoseInterpolator
from mq3drecon.dataio.mruk_image_data_io import MRUKImageDataIO
from mq3drecon.dataio.session_info import CaptureBackend, load_session_info
from mq3drecon.models.camera_characteristics import CameraCharacteristics
from mq3drecon.models.camera_dataset import CameraDataset
from mq3drecon.models.image_format_info import BaseTime, ImageFormatInfo, ImagePlaneInfo
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem, Transforms


class ImageDataIO:
    def __init__(self, image_path_config: ImagePathConfig):
        self.image_path_config = image_path_config

    
    def get_yuv_timestamps(self, side: Side) -> list[int]:
        yuv_files = self.image_path_config.get_yuv_image_paths(side=side)
        return [
            int(yuv_file.stem)
            for yuv_file
            in yuv_files
        ]

    
    def get_rgb_timestamps(self, side: Side) -> list[int]:
        rgb_files = self.image_path_config.get_rgb_image_paths(side=side)
        return [
            int(rgb_file.stem)
            for rgb_file
            in rgb_files
        ]

    
    def load_yuv(self, side: Side, timestamp: int) -> np.ndarray:
        yuv_dir = self.image_path_config.get_yuv_dir(side=side)
        file_path = yuv_dir / f'{timestamp}.yuv'
        return np.fromfile(file_path, dtype=np.uint8)
    

    def load_rgb(self, side: Side, timestamp: int) -> np.ndarray:
        if self.get_capture_backend() == CaptureBackend.MRUK:
            return self._load_mruk_rgb(side=side, timestamp=timestamp)

        file_path = self.image_path_config.get_rgb_file_path(side=side, timestamp=timestamp)
        return self._load_png_rgb(file_path)


    def _load_mruk_rgb(self, side: Side, timestamp: int) -> np.ndarray:
        png_path = self.image_path_config.get_mruk_rgba_png_path(side=side, timestamp=timestamp)
        if png_path.exists():
            return self._load_png_rgb(png_path)

        dataset = self.load_color_dataset(side=side)
        matches = np.where(dataset.timestamps == int(timestamp))[0]
        if len(matches) == 0:
            raise FileNotFoundError(f"MRUK RGB image not found for {side.name} timestamp {timestamp}")

        return self.load_color_rgb_image(dataset=dataset, index=int(matches[0]))


    def _load_png_rgb(self, file_path) -> np.ndarray:
        image = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise FileNotFoundError(f"Image file not found or cannot be read: {file_path}")
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        raise ValueError(f"Unsupported PNG image shape for {file_path}: {image.shape}")


    def load_color_image(self, dataset: CameraDataset, index: int) -> np.ndarray:
        file_name = str(dataset.image_file_names[index])
        width = int(dataset.widths[index])
        height = int(dataset.heights[index])
        file_path = self.image_path_config.project_dir / dataset.directory_relative_path / file_name

        if file_path.suffix == ".png":
            bgr = cv2.imread(str(file_path))
            if bgr is None:
                raise FileNotFoundError(f"Image file not found or cannot be read: {file_path}")
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        if file_path.suffix == ".rgba":
            expected_size = width * height * 4
            actual_size = file_path.stat().st_size
            if actual_size != expected_size:
                raise ValueError(
                    f"Invalid RGBA file size for {file_path}: expected {expected_size} bytes, got {actual_size}"
                )
            rgba = np.fromfile(file_path, dtype=np.uint8).reshape(height, width, 4)
            return np.ascontiguousarray(np.flipud(rgba))

        raise ValueError(f"Unsupported color image format: {file_path}")


    def load_color_rgb_image(self, dataset: CameraDataset, index: int) -> np.ndarray:
        image = self.load_color_image(dataset=dataset, index=index)
        if image.ndim != 3 or image.shape[2] not in (3, 4):
            raise ValueError(f"Unsupported color image shape: {image.shape}")
        return np.ascontiguousarray(image[:, :, :3])


    def save_rgb(self, rgb: np.ndarray, side: Side, timestamp: int):
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        self.save_bgr(bgr=bgr, side=side, timestamp=timestamp)


    def save_bgr(self, bgr: np.ndarray, side: Side, timestamp: int):
        file_path = self.image_path_config.get_rgb_file_path(side=side, timestamp=timestamp)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(file_path), bgr)


    def load_image_format_info(self, side: Side) -> ImageFormatInfo:
        format_json_path = self.image_path_config.get_camera_format_format_json_path(side)

        with open(format_json_path) as f:
            format_info_dict = json.load(f)
        
        width = format_info_dict["width"]
        height = format_info_dict["height"]

        format = format_info_dict["format"]

        planes = [
            ImagePlaneInfo(
                buffer_size=plane["bufferSize"],
                row_stride=plane["rowStride"],
                pixel_stride=plane["pixelStride"]
            ) for plane in format_info_dict["planes"]
        ]

        base_time_dict = format_info_dict["baseTime"]
        base_time = BaseTime(
            mono_time_ns=base_time_dict["baseMonoTimeNs"],
            unix_time_ns=base_time_dict["baseUnixTimeMs"]
        )

        return ImageFormatInfo(
            width=width,
            height=height,
            format=format,
            planes=planes,
            base_time=base_time
        )


    def load_camera_characteristics(self, side: Side) -> CameraCharacteristics:
        characteristics_json_path = self.image_path_config.get_camera_characteristic_json_path(side)

        with open(characteristics_json_path, "r", encoding="utf-8") as f:
            camera_characteristics = json.load(f)

        array_size = camera_characteristics["sensor"]["activeArraySize"]
        width = array_size["right"] - array_size["left"]
        height = array_size["bottom"] - array_size["top"]

        intrinsics = camera_characteristics["intrinsics"]

        fx = intrinsics["fx"]
        fy = intrinsics["fy"]
        cx = intrinsics["cx"]
        cy = intrinsics["cy"]

        camera_pose = camera_characteristics["pose"]

        transl = camera_pose["translation"]
        transl[2] *= -1
        if len(transl) < 3:
            transl = np.array((0, 0, 0))

        rot_quat = camera_pose["rotation"]
        if len(rot_quat) >=4:
            qx = -rot_quat[0]
            qy = -rot_quat[1]
            qz = rot_quat[2]
            qw = rot_quat[3]

            rot = R.from_quat((qx, qy, qz, qw)).inv()
            # Apply a 180-degree rotation to align the Android camera pose with the HMD world coordinate system.
            rot *= R.from_euler('x', np.pi)

            rot_quat = rot.as_quat()
            
        else:
            rot_quat = np.array((0, 0, 0, 1))

        return CameraCharacteristics(
            width=width,
            height=height,
            fx=fx, fy=fy,
            cx=cx, cy=cy,
            transl=transl,
            rot_quat=rot_quat,
        )
    

    def load_hmd_poses(self) -> pd.DataFrame:
        hmd_poses_csv_path = self.image_path_config.get_hmd_pose_csv_path()

        if not hmd_poses_csv_path.exists():
            raise FileNotFoundError(f"HMD poses CSV file not found at {hmd_poses_csv_path}")

        df = pd.read_csv(hmd_poses_csv_path)

        return df
    

    def get_capture_backend(self) -> CaptureBackend:
        return load_session_info(self.image_path_config.project_dir).capture_backend


    def load_color_dataset(self, side: Side, use_cache: bool = True) -> CameraDataset:
        camera_dataset_path = self.image_path_config.get_color_dataset_path(side=side)

        if use_cache and camera_dataset_path.exists():
            print(f"[Info] Loading cached color dataset for {side.name} from {camera_dataset_path} ...")
            
            try:
                return CameraDataset.load(camera_dataset_path)
            except Exception as e:
                print(f"[Error] Color dataset cache is corrupted or invalid. Rebuilding cache from the original source\n{e}")

        else:
            print(f"[Info] Color dataset not found for {side.name}. Rebuilding cache from the original source...")

        color_dataset = self.build_color_dataset(side=side)
        color_dataset.save(camera_dataset_path)

        return color_dataset
    

    def load_optimized_color_dataset(self, side: Side) -> Optional[CameraDataset]:
        optimized_dataset_path = self.image_path_config.get_optimized_color_dataset_path(side=side)

        if optimized_dataset_path.exists():
            try:
                return CameraDataset.load(optimized_dataset_path)
            except Exception as e:
                print(f"[Error] Optimized color dataset cache is corrupted or invalid.")

    
    def save_optimized_color_dataset(self, dataset: CameraDataset, side: Side):
        optimized_dataset_path = self.image_path_config.get_optimized_color_dataset_path(side=side)
        optimized_dataset_path.parent.mkdir(parents=True, exist_ok=True)

        dataset.save(optimized_dataset_path)


    def build_color_dataset(self, side: Side) -> CameraDataset:
        if self.get_capture_backend() == CaptureBackend.MRUK:
            return MRUKImageDataIO(self.image_path_config).build_color_dataset(side=side)

        return self.build_legacy_color_dataset(side=side)


    def build_legacy_color_dataset(self, side: Side) -> CameraDataset:
        interpolator = PoseInterpolator(
            pose_csv_path=self.image_path_config.get_hmd_pose_csv_path()
        )
        camera_characteristics = self.load_camera_characteristics(side=side)

        directory_path = self.image_path_config.get_rgb_dir(side=side)
        directory_relative_path = self.image_path_config.get_relative_path(directory_path)

        rgb_filenames = []
        timestamps = []

        hmd_positions = []
        hmd_rotations = []

        for path in self.image_path_config.get_rgb_image_paths(side=side):
            filename = path.name
            timestamp = int(filename.split('.')[0])

            pose = interpolator.interpolate_pose(timestamp)
            if pose is None:
                print(f"[Warning] No pose found for timestamp {timestamp}. Skipping this image.")
                continue

            rgb_filenames.append(filename)
            timestamps.append(timestamp)

            position, rotation = pose
            hmd_positions.append(position)
            hmd_rotations.append(rotation)

        if len(timestamps) == 0:
            raise Exception("[Error] No valid timestamps found. Unable to build color dataset for side: {}.".format(side.name))

        hmd_transforms = Transforms(
            coordinate_system=CoordinateSystem.UNITY,
            positions=np.array(hmd_positions),
            rotations=np.array(hmd_rotations)
        )
        camera_transforms = hmd_transforms.apply_local_transform(
            local_position=camera_characteristics.transl,
            local_rotation=camera_characteristics.rot_quat
        )

        fxs = np.full_like(timestamps, camera_characteristics.fx, dtype=np.float32)
        fys = np.full_like(timestamps, camera_characteristics.fy, dtype=np.float32)
        cxs = np.full_like(timestamps, camera_characteristics.cx, dtype=np.float32)
        cys = np.full_like(timestamps, camera_characteristics.cy, dtype=np.float32)
        widths = np.full_like(timestamps, camera_characteristics.width)
        heights = np.full_like(timestamps, camera_characteristics.height)

        if len(rgb_filenames) == 0:
            raise Exception(f"[Error] RGB image not found. Please make sure the YUV-to-RGB conversion has been performed.")

        return CameraDataset(
            directory_relative_path=str(directory_relative_path),
            image_file_names=np.array(rgb_filenames),
            timestamps=np.array(timestamps),
            fx=fxs,
            fy=fys,
            cx=cxs,
            cy=cys,
            transforms=camera_transforms,
            widths=widths,
            heights=heights        
        )