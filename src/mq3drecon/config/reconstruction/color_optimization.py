from dataclasses import dataclass

from mq3drecon.config.reconstruction.device import DeviceSpec


@dataclass
class ColorOptimizationConfig:
    device: DeviceSpec
    weight_threshold: float = 3.0
    estimated_vertex_number: int = -1
    interval: int = 10
    max_iteration: int = 100
    use_dataset_cache: bool = True
