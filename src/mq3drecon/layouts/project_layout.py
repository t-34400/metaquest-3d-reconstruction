from dataclasses import dataclass
from pathlib import Path

from mq3drecon.config.project_path_config import LegacyProjectLayout
from mq3drecon.models.side import Side


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
