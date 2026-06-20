from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mq3drecon.config.depth_to_linear_config import Depth2LinearConfig
from mq3drecon.layouts import LegacyProjectLayout
from mq3drecon.config.yuv_to_rgb_config import Yuv2RgbConfig
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.dataio.image_data_io import ImageDataIO
from mq3drecon.dataio.mruk_image_data_io import MRUKImageDataIO
from mq3drecon.processing.depth_conversion import convert_depth_directory
from mq3drecon.processing.yuv_conversion import convert_yuv_directory
from mq3drecon.processing.rgba_conversion import convert_rgba_directory
from mq3drecon.models import Side


@dataclass(frozen=True)
class RgbImageStatus:
    left_count: int
    right_count: int

    @property
    def is_complete(self) -> bool:
        return self.left_count > 0 and self.right_count > 0

    @property
    def is_balanced(self) -> bool:
        return self.left_count == self.right_count


def get_rgb_image_status(project_dir: Path) -> RgbImageStatus:
    path_config = LegacyProjectLayout(project_dir=project_dir)
    image_io = ImageDataIO(image_path_config=path_config.image)
    return RgbImageStatus(
        left_count=len(image_io.get_rgb_timestamps(Side.LEFT)),
        right_count=len(image_io.get_rgb_timestamps(Side.RIGHT)),
    )


def has_rgb_images(project_dir: Path) -> bool:
    return get_rgb_image_status(project_dir).is_complete


def _load_config_section(config_yml_path: Path, section_name: str) -> dict[str, Any]:
    with open(config_yml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    section = config.get(section_name)
    if not isinstance(section, dict):
        raise ValueError(f"Missing or invalid '{section_name}' section in config: {config_yml_path}")
    return section


def _resolve_yuv_to_rgb_config(
    config: Yuv2RgbConfig | None,
    config_yml_path: Path | None,
) -> Yuv2RgbConfig:
    if config is not None and config_yml_path is not None:
        raise ValueError("Pass either config or config_yml_path, not both")
    if config is not None:
        return config
    if config_yml_path is not None:
        return Yuv2RgbConfig.parse(_load_config_section(config_yml_path, "yuv_to_rgb"))
    return Yuv2RgbConfig()


def _resolve_depth_to_linear_config(
    config: Depth2LinearConfig | None,
    config_yml_path: Path | None,
) -> Depth2LinearConfig:
    if config is not None and config_yml_path is not None:
        raise ValueError("Pass either config or config_yml_path, not both")
    if config is not None:
        return config
    if config_yml_path is not None:
        return Depth2LinearConfig.parse(_load_config_section(config_yml_path, "depth_to_linear"))
    return Depth2LinearConfig()


def run_yuv_to_rgb(
    project_dir: Path,
    config_yml_path: Path | None = None,
    *,
    config: Yuv2RgbConfig | None = None,
) -> None:
    path_config = LegacyProjectLayout(project_dir=project_dir)
    resolved_config = _resolve_yuv_to_rgb_config(config=config, config_yml_path=config_yml_path)
    convert_yuv_directory(image_io=ImageDataIO(image_path_config=path_config.image), config=resolved_config)


def run_rgba_to_png(project_dir: Path) -> None:
    path_config = LegacyProjectLayout(project_dir=project_dir)
    convert_rgba_directory(mruk_image_io=MRUKImageDataIO(image_path_config=path_config.image))


def run_depth_to_linear(
    project_dir: Path,
    config_yml_path: Path | None = None,
    *,
    config: Depth2LinearConfig | None = None,
) -> None:
    path_config = LegacyProjectLayout(project_dir=project_dir)
    resolved_config = _resolve_depth_to_linear_config(config=config, config_yml_path=config_yml_path)
    convert_depth_directory(depth_data_io=DepthDataIO(depth_path_config=path_config.depth), depth_to_linear_config=resolved_config)
