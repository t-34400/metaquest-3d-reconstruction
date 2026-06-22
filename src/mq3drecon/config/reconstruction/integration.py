from dataclasses import dataclass
from typing import Literal

from mq3drecon.config.reconstruction.device import DeviceSpec


@dataclass
class IntegrationConfig:
    device: DeviceSpec
    mode: Literal["global", "tiled"] = "global"
    use_confidence_filtered_depth: bool = True
    confidence_threshold: float = 0.05
    valid_count_threshold: int = 4
    voxel_size: float = 0.01
    block_resolution: int = 16
    block_count: int = 50_000
    depth_max: float = 1.5
    trunc_voxel_multiplier: float = 8.0
    tile_size_voxels: int = 256
    tile_overlap_voxels: int = 24
