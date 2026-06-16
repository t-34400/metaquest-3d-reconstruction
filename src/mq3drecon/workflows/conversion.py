from pathlib import Path
from typing import Any

import yaml

from mq3drecon.config.depth_to_linear_config import Depth2LinearConfig
from mq3drecon.layouts import LegacyProjectLayout
from mq3drecon.config.yuv_to_rgb_config import Yuv2RgbConfig
from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.dataio.image_data_io import ImageDataIO
from mq3drecon.processing.depth_conversion import convert_depth_directory
from mq3drecon.processing.yuv_conversion import convert_yuv_directory


def _load_config_section(config_yml_path: Path, section_name: str) -> dict[str, Any]:
    with open(config_yml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    section = config.get(section_name)
    if not isinstance(section, dict):
        raise ValueError(f"Missing or invalid '{section_name}' section in config: {config_yml_path}")
    return section


def run_yuv_to_rgb(project_dir: Path, config_yml_path: Path) -> None:
    path_config = LegacyProjectLayout(project_dir=project_dir)
    config = Yuv2RgbConfig.parse(_load_config_section(config_yml_path, "yuv_to_rgb"))
    convert_yuv_directory(image_io=ImageDataIO(image_path_config=path_config.image), config=config)


def run_depth_to_linear(project_dir: Path, config_yml_path: Path) -> None:
    path_config = LegacyProjectLayout(project_dir=project_dir)
    config = Depth2LinearConfig.parse(_load_config_section(config_yml_path, "depth_to_linear"))
    convert_depth_directory(depth_data_io=DepthDataIO(depth_path_config=path_config.depth), depth_to_linear_config=config)
