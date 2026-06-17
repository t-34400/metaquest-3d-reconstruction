from dataclasses import dataclass, field
from pathlib import Path

import yaml

from mq3drecon.config.depth_to_linear_config import Depth2LinearConfig
from mq3drecon.config.reconstruction_config import ReconstructionConfig
from mq3drecon.config.yuv_to_rgb_config import Yuv2RgbConfig


@dataclass
class PipelineConfigs:
    yuv_to_rgb: Yuv2RgbConfig = field(default_factory=Yuv2RgbConfig)
    depth_to_linear: Depth2LinearConfig = field(default_factory=Depth2LinearConfig)
    reconstruction: ReconstructionConfig = field(default_factory=ReconstructionConfig)

    @classmethod
    def parse_config_yml(cls, yml_path: Path) -> "PipelineConfigs":
        with open(yml_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}

        return cls(
            yuv_to_rgb=Yuv2RgbConfig.parse(config_dict["yuv_to_rgb"]),
            depth_to_linear=Depth2LinearConfig.parse(config_dict["depth_to_linear"]),
            reconstruction=ReconstructionConfig.parse(config_dict["reconstruction"]),
        )
