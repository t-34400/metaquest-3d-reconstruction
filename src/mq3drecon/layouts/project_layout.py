from dataclasses import dataclass
from pathlib import Path

from mq3drecon.models.side import Side


YUV_DIR_MAP = {
    Side.LEFT: "left_camera_raw",
    Side.RIGHT: "right_camera_raw",
}

RGB_DIR_MAP = {
    Side.LEFT: "left_camera_rgb",
    Side.RIGHT: "right_camera_rgb",
}

CAMERA_CHARACTERISTICS_JSON_MAP = {
    Side.LEFT: "left_camera_characteristics.json",
    Side.RIGHT: "right_camera_characteristics.json",
}

CAMERA_FORMAT_INFO_JSON_MAP = {
    Side.LEFT: "left_camera_image_format.json",
    Side.RIGHT: "right_camera_image_format.json",
}

HMD_POSE_CSV_PATH = "hmd_poses.csv"
SESSION_INFO_JSON_PATH = "session_info.json"

MRUK_RGBA_DIR_MAP = {
    Side.LEFT: "left_camera_mruk_rgba",
    Side.RIGHT: "right_camera_mruk_rgba",
}

MRUK_RGBA_PNG_DIR_MAP = {
    Side.LEFT: "left_camera_mruk_rgba_png",
    Side.RIGHT: "right_camera_mruk_rgba_png",
}

MRUK_INTRINSICS_JSON_MAP = {
    Side.LEFT: "left_camera_mruk_intrinsics.json",
    Side.RIGHT: "right_camera_mruk_intrinsics.json",
}

MRUK_FRAME_METADATA_CSV_MAP = {
    Side.LEFT: "left_camera_mruk_frame_metadata.csv",
    Side.RIGHT: "right_camera_mruk_frame_metadata.csv",
}

MRUK_STEREO_PAIRS_CSV_PATH = "mruk_stereo_pairs.csv"

COLOR_DATASET_NPZ_MAP = {
    Side.LEFT: "dataset/left_camera_dataset.npz",
    Side.RIGHT: "dataset/right_camera_dataset.npz",
}

OPTIMIZED_COLOR_DATASET_NPZ_MAP = {
    Side.LEFT: "dataset/left_camera_dataset_optimized.npz",
    Side.RIGHT: "dataset/right_camera_dataset_optimized.npz",
}

DEPTH_DIR_MAP = {
    Side.LEFT: "left_depth",
    Side.RIGHT: "right_depth",
}

DEPTH_DESCRIPTOR_CSV_MAP = {
    Side.LEFT: "left_depth_descriptors.csv",
    Side.RIGHT: "right_depth_descriptors.csv",
}

DEPTH_CONFIDENCE_MAP_DIR_MAP = {
    Side.LEFT: "left_depth_confidence",
    Side.RIGHT: "right_depth_confidence",
}

LINEAR_DEPTH_DIR_MAP = {
    Side.LEFT: "left_depth_linear",
    Side.RIGHT: "right_depth_linear",
}

DEPTH_DATASET_NPZ_MAP = {
    Side.LEFT: "dataset/left_depth_dataset.npz",
    Side.RIGHT: "dataset/right_depth_dataset.npz",
}

OPTIMIZED_DEPTH_DATASET_NPZ_MAP = {
    Side.LEFT: "dataset/left_depth_dataset_optimized.npz",
    Side.RIGHT: "dataset/right_depth_dataset_optimized.npz",
}

COLOR_ALIGNED_DEPTH_DIR_MAP = {
    Side.LEFT: "left_color_aligned_depth",
    Side.RIGHT: "right_color_aligned_depth",
}

COLOR_ALIGNED_DEPTH_PNG_DIR_MAP = {
    Side.LEFT: "left_color_aligned_depth_png",
    Side.RIGHT: "right_color_aligned_depth_png",
}

COLOR_ALIGNED_DEPTH_PREVIEW_PNG_DIR_MAP = {
    Side.LEFT: "left_color_aligned_depth_preview_png",
    Side.RIGHT: "right_color_aligned_depth_preview_png",
}

CACHE_DIR_PATH = "cache"
FRAGMENT_DATASET_CACHE_DIR_PATH = f"{CACHE_DIR_PATH}/dataset"
FRAGMENT_PCD_CACHE_DIR_PATH = f"{CACHE_DIR_PATH}/pcd"


class ImagePathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)

    def get_yuv_dir(self, side: Side) -> Path:
        return self.project_dir / YUV_DIR_MAP[side]

    def get_yuv_file_path(self, side: Side, timestamp: int) -> Path:
        return self.get_yuv_dir(side=side) / f"{timestamp}.yuv"

    def get_yuv_image_paths(self, side: Side) -> list[Path]:
        return sorted(self.get_yuv_dir(side).glob("*.yuv"))

    def get_rgb_dir(self, side: Side) -> Path:
        return self.project_dir / RGB_DIR_MAP[side]

    def get_rgb_file_path(self, side: Side, timestamp: int) -> Path:
        return self.get_rgb_dir(side) / f"{timestamp}.png"

    def get_rgb_image_paths(self, side: Side) -> list[Path]:
        return sorted(self.get_rgb_dir(side).glob("*.png"))

    def get_camera_characteristic_json_path(self, side: Side) -> Path:
        return self.project_dir / CAMERA_CHARACTERISTICS_JSON_MAP[side]

    def get_camera_format_json_path(self, side: Side) -> Path:
        return self.project_dir / CAMERA_FORMAT_INFO_JSON_MAP[side]

    def get_camera_format_format_json_path(self, side: Side) -> Path:
        return self.get_camera_format_json_path(side=side)

    def get_hmd_pose_csv_path(self) -> Path:
        return self.project_dir / HMD_POSE_CSV_PATH

    def get_session_info_json_path(self) -> Path:
        return self.project_dir / SESSION_INFO_JSON_PATH

    def get_mruk_rgba_dir(self, side: Side) -> Path:
        return self.project_dir / MRUK_RGBA_DIR_MAP[side]

    def get_mruk_rgba_paths(self, side: Side) -> list[Path]:
        return sorted(self.get_mruk_rgba_dir(side).glob("*.rgba"))

    def get_mruk_rgba_png_dir(self, side: Side) -> Path:
        return self.project_dir / MRUK_RGBA_PNG_DIR_MAP[side]

    def get_mruk_rgba_png_path(self, side: Side, timestamp: int) -> Path:
        return self.get_mruk_rgba_png_dir(side=side) / f"{timestamp}.png"

    def get_mruk_rgba_png_paths(self, side: Side) -> list[Path]:
        return sorted(self.get_mruk_rgba_png_dir(side).glob("*.png"))

    def get_mruk_intrinsics_json_path(self, side: Side) -> Path:
        return self.project_dir / MRUK_INTRINSICS_JSON_MAP[side]

    def get_mruk_frame_metadata_csv_path(self, side: Side) -> Path:
        return self.project_dir / MRUK_FRAME_METADATA_CSV_MAP[side]

    def get_mruk_stereo_pairs_csv_path(self) -> Path:
        return self.project_dir / MRUK_STEREO_PAIRS_CSV_PATH

    def get_color_dataset_path(self, side: Side) -> Path:
        return self.project_dir / COLOR_DATASET_NPZ_MAP[side]

    def get_optimized_color_dataset_path(self, side: Side) -> Path:
        return self.project_dir / OPTIMIZED_COLOR_DATASET_NPZ_MAP[side]

    def get_relative_path(self, path: Path) -> Path:
        return Path(path).relative_to(self.project_dir)


class DepthPathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)

    def get_depth_dir(self, side: Side) -> Path:
        return self.project_dir / DEPTH_DIR_MAP[side]

    def get_depth_map_paths(self, side: Side) -> list[Path]:
        return sorted(self.get_depth_dir(side).glob("*.raw"))

    def get_depth_map_filename(self, timestamp: int) -> str:
        return f"{timestamp}.raw"

    def get_depth_map_path(self, side: Side, timestamp: int) -> Path:
        return self.get_depth_dir(side=side) / self.get_depth_map_filename(timestamp=timestamp)

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
        return Path(path).relative_to(self.project_dir)


class RGBDPathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)

    def get_color_aligned_depth_filename(self, timestamp: int) -> str:
        return f"{timestamp}.npy"

    def get_color_aligned_depth_dir(self, side: Side) -> Path:
        return self.project_dir / COLOR_ALIGNED_DEPTH_DIR_MAP[side]

    def get_color_aligned_depth_path(self, side: Side, timestamp: int) -> Path:
        return self.get_color_aligned_depth_dir(side=side) / self.get_color_aligned_depth_filename(timestamp=timestamp)

    def get_color_aligned_depth_png_dir(self, side: Side) -> Path:
        return self.project_dir / COLOR_ALIGNED_DEPTH_PNG_DIR_MAP[side]

    def get_color_aligned_depth_png_path(self, side: Side, timestamp: int) -> Path:
        return self.get_color_aligned_depth_png_dir(side=side) / f"{timestamp}.png"

    def get_color_aligned_depth_preview_png_dir(self, side: Side) -> Path:
        return self.project_dir / COLOR_ALIGNED_DEPTH_PREVIEW_PNG_DIR_MAP[side]

    def get_color_aligned_depth_preview_png_path(self, side: Side, timestamp: int) -> Path:
        return self.get_color_aligned_depth_preview_png_dir(side=side) / f"{timestamp}.png"


class ReconstructionPathConfig:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)

    def get_fragment_dir(self) -> Path:
        return self.project_dir / FRAGMENT_DATASET_CACHE_DIR_PATH

    def get_fragment_dataset_paths(self) -> dict[Side, list[Path]]:
        dir_path = self.get_fragment_dir()
        if not dir_path.exists() or not dir_path.is_dir():
            return {}

        fragment_dataset_paths = {}
        for side in Side:
            fragment_dataset_paths[side] = sorted(dir_path.glob(f"{side.name}_fragment_*_dataset.npz"))
        return fragment_dataset_paths

    def get_fragment_dataset_path(self, side: Side, index: int) -> Path:
        return self.get_fragment_dir() / f"{side.name}_fragment_{index}_dataset.npz"

    def get_fragment_pcd_path(self, side: Side, index: int) -> Path:
        return self.project_dir / FRAGMENT_PCD_CACHE_DIR_PATH / f"{side.name}_fragment_{index}.pcd"

    def get_colorless_vbg_path(self) -> Path:
        return self.project_dir / "reconstruction/colorless_vbg.npz"

    def get_colored_mesh_path(self) -> Path:
        return self.project_dir / "reconstruction/color_mesh.ply"

    def get_colored_pcd_path(self) -> Path:
        return self.project_dir / "reconstruction/color.ply"

    def get_relative_path(self, path: Path) -> Path:
        return Path(path).relative_to(self.project_dir)


class LegacyProjectLayout:
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.image = ImagePathConfig(project_dir=self.project_dir)
        self.depth = DepthPathConfig(project_dir=self.project_dir)
        self.rgbd = RGBDPathConfig(project_dir=self.project_dir)
        self.reconstruction = ReconstructionPathConfig(project_dir=self.project_dir)


@dataclass(frozen=True)
class PackageOutputLayout:
    output_dir: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_dir", Path(self.output_dir))

    def get_dataset_dir(self) -> Path:
        return self.output_dir / "dataset"

    def get_cache_dir(self) -> Path:
        return self.output_dir / "cache"

    def get_reconstruction_dir(self) -> Path:
        return self.output_dir / "reconstruction"

    def get_rgb_dir(self, side: Side) -> Path:
        return self.output_dir / f"{side.name.lower()}_camera_rgb"

    def get_linear_depth_dir(self, side: Side) -> Path:
        return self.output_dir / f"{side.name.lower()}_depth_linear"


@dataclass(frozen=True)
class ColmapExportLayout:
    output_dir: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_dir", Path(self.output_dir))

    def get_image_dir(self) -> Path:
        return self.output_dir / "images"

    def get_model_dir(self) -> Path:
        return self.output_dir / "distorted" / "sparse" / "0"

    def ensure_directories(self) -> None:
        self.get_image_dir().mkdir(parents=True, exist_ok=True)
        self.get_model_dir().mkdir(parents=True, exist_ok=True)
