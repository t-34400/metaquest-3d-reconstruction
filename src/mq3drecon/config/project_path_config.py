from pathlib import Path

from mq3drecon.models.side import Side


YUV_DIR_MAP = {
    Side.LEFT: 'left_camera_raw',
    Side.RIGHT: 'right_camera_raw'
}

RGB_DIR_MAP = {
    Side.LEFT: 'left_camera_rgb',
    Side.RIGHT: 'right_camera_rgb'
}

CAMERA_CHARACTERISTICS_JSON_MAP = {
    Side.LEFT: 'left_camera_characteristics.json',
    Side.RIGHT: 'right_camera_characteristics.json'    
}

CAMERA_FORMAT_INFO_JSON_MAP = {
    Side.LEFT: 'left_camera_image_format.json',
    Side.RIGHT: 'right_camera_image_format.json'
}

HMD_POSE_CSV_PATH = 'hmd_poses.csv'

COLOR_DATASET_NPZ_MAP = {
    Side.LEFT: 'dataset/left_camera_dataset.npz',
    Side.RIGHT: 'dataset/right_camera_dataset.npz',
}

OPTIMIZED_COLOR_DATASET_NPZ_MAP = {
    Side.LEFT: 'dataset/left_camera_dataset_optimized.npz',
    Side.RIGHT: 'dataset/right_camera_dataset_optimized.npz',
}

DEPTH_DIR_MAP = {
    Side.LEFT: 'left_depth',
    Side.RIGHT: 'right_depth'
}

DEPTH_DESCRIPTOR_CSV_MAP = {
    Side.LEFT: 'left_depth_descriptors.csv',
    Side.RIGHT: 'right_depth_descriptors.csv',
}

DEPTH_CONFIDENCE_MAP_DIR_MAP = {
    Side.LEFT: 'left_depth_confidence',
    Side.RIGHT: 'right_depth_confidence',
}

LINEAR_DEPTH_DIR_MAP = {
    Side.LEFT: 'left_depth_linear',
    Side.RIGHT: 'right_depth_linear'
}

DEPTH_DATASET_NPZ_MAP = {
    Side.LEFT: 'dataset/left_depth_dataset.npz',
    Side.RIGHT: 'dataset/right_depth_dataset.npz',
}

OPTIMIZED_DEPTH_DATASET_NPZ_MAP = {
    Side.LEFT: 'dataset/left_depth_dataset_optimized.npz',
    Side.RIGHT: 'dataset/right_depth_dataset_optimized.npz',
}

COLOR_ALIGNED_DEPTH_DIR_MAP = {
    Side.LEFT: 'left_color_aligned_depth',
    Side.RIGHT: 'right_color_aligned_depth'
}

CACHE_DIR_PATH = 'cache'

FRAGMENT_DATASET_CACHE_DIR_PATH = f'{CACHE_DIR_PATH}/dataset'
FRAGMENT_PCD_CACHE_DIR_PATH = f'{CACHE_DIR_PATH}/pcd'


class ImagePathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir


    def get_yuv_dir(self, side: Side) -> Path:
        return self.project_dir / YUV_DIR_MAP[side]
    

    def get_yuv_image_paths(self, side: Side) -> list[Path]:
        yuv_dir = self.get_yuv_dir(side)
        return sorted(yuv_dir.glob("*.yuv"))
    

    def get_rgb_dir(self, side: Side) -> Path:
        return self.project_dir / RGB_DIR_MAP[side]
    

    def get_rgb_file_path(self, side: Side, timestamp: int) -> Path:
        return self.project_dir / RGB_DIR_MAP[side] / f"{timestamp}.png"
    

    def get_rgb_image_paths(self, side: Side) -> list[Path]:
        rgb_dir = self.get_rgb_dir(side)
        return sorted(rgb_dir.glob("*.png"))
    

    def get_camera_characteristic_json_path(self, side: Side) -> Path:
        return self.project_dir / CAMERA_CHARACTERISTICS_JSON_MAP[side]
    

    def get_camera_format_format_json_path(self, side: Side) -> Path:
        return self.project_dir / CAMERA_FORMAT_INFO_JSON_MAP[side]
    

    def get_hmd_pose_csv_path(self) -> Path:
        return self.project_dir / HMD_POSE_CSV_PATH
    

    def get_color_dataset_path(self, side: Side) -> Path:
        return self.project_dir / COLOR_DATASET_NPZ_MAP[side]
    

    def get_optimized_color_dataset_path(self, side: Side) -> Path:
        return self.project_dir / OPTIMIZED_COLOR_DATASET_NPZ_MAP[side]


    def get_relative_path(self, path: Path) -> Path:
        return path.relative_to(self.project_dir)


class DepthPathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir


    def get_depth_dir(self, side: Side) -> Path:
        return self.project_dir / DEPTH_DIR_MAP[side]
    

    def get_depth_map_paths(self, side: Side) -> list[Path]:
        depth_dir = self.get_depth_dir(side)
        return sorted(depth_dir.glob("*.raw"))


    def get_depth_map_filename(self, timestamp: int) -> str:
        return f"{timestamp}.raw"


    def get_depth_map_path(self, side: Side, timestamp: int) -> Path:
        depth_dir = self.get_depth_dir(side=side)
        return depth_dir / self.get_depth_map_filename(timestamp=timestamp)


    def get_depth_descriptor_path(self, side: Side) -> Path:
        return self.project_dir / DEPTH_DESCRIPTOR_CSV_MAP[side]
    
    def get_depth_confidence_map_dir_path(self, side: Side) -> Path:
        return self.project_dir / DEPTH_CONFIDENCE_MAP_DIR_MAP[side]
    

    def get_depth_confidence_map_path(self, side: Side, timestamp: int) -> Path:
        return self.get_depth_confidence_map_dir_path(side=side) / f"{timestamp}.npz"
    

    def get_depth_dataset_path(self, side: Side) -> Path:
        return self.project_dir / DEPTH_DATASET_NPZ_MAP[side]
    

    def get_optimized_depth_dataset_path(self, side: Side) -> Path:
        return self.project_dir / OPTIMIZED_DEPTH_DATASET_NPZ_MAP[side]
    

    def get_linear_depth_dir(self, side: Side) -> Path:
        return self.project_dir / LINEAR_DEPTH_DIR_MAP[side]
    

    def get_relative_path(self, path: Path) -> Path:
        return path.relative_to(self.project_dir)


class RGBDPathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir


    def get_color_aligned_depth_filename(self, timestamp: int) -> str:
        return f"{timestamp}.npy"


    def get_color_aligned_depth_dir(self, side: Side) -> Path:
        return self.project_dir / COLOR_ALIGNED_DEPTH_DIR_MAP[side]
    

    def get_color_aligned_depth_path(self, side: Side, timestamp: int) -> Path:
        color_aligned_depth_dir = self.get_color_aligned_depth_dir(side=side)
        return color_aligned_depth_dir / self.get_color_aligned_depth_filename(timestamp=timestamp)


class ReconstructionPathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    
    def get_fragment_dir(self) -> Path:
        return self.project_dir / FRAGMENT_DATASET_CACHE_DIR_PATH
    
    
    def get_fragment_dataset_paths(self) -> dict[Side, list[Path]]:
        dir_path = self.get_fragment_dir()
        if not dir_path.exists() or not dir_path.is_dir():
            return {}

        fragment_dataset_paths = {}

        for side in Side:
            side_datasets = sorted(dir_path.glob(f'{side.name}_fragment_*_dataset.npz'))
            fragment_dataset_paths[side] = side_datasets

        return fragment_dataset_paths
        

    def get_fragment_dataset_path(self, side: Side, index: int) -> Path:
        return self.get_fragment_dir() / f'{side.name}_fragment_{index}_dataset.npz'


    def get_fragment_pcd_path(self, side: Side, index: int) -> Path:
        return self.project_dir / FRAGMENT_PCD_CACHE_DIR_PATH / f'{side.name}_fragment_{index}.pcd'
    

    def get_colorless_vbg_path(self) -> Path:
        return self.project_dir / "reconstruction/colorless_vbg.npz"


    def get_colored_mesh_path(self) -> Path:
        return self.project_dir / "reconstruction/color_mesh.ply"
    

    def get_colored_pcd_path(self) -> Path:
        return self.project_dir / "reconstruction/color.ply"

    
    def get_relative_path(self, path: Path) -> Path:
        return path.relative_to(self.project_dir)


class ProjectPathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.image = ImagePathConfig(project_dir=project_dir)
        self.depth = DepthPathConfig(project_dir=project_dir)
        self.rgbd = RGBDPathConfig(project_dir=project_dir)
        self.reconstruction = ReconstructionPathConfig(project_dir=project_dir)