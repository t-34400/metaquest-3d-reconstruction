from dataclasses import dataclass

from mq3drecon.config.reconstruction.device import DeviceSpec


@dataclass
class FragmentGenerationConfig:
    device: DeviceSpec
    fragment_size: int = 100
    use_confidence_filtered_depth: bool = True
    confidence_threshold: float = 0.05
    valid_count_threshold: int = 4
    depth_max: float = 3.0
    odometry_loop_interval: int = 10
    overlap_ratio_threshold: float = 0.1
    loop_yaw_info_density_threshold: float = 0.3
    dist_threshold: float = 0.07
    edge_prune_threshold: float = 0.25
    use_dataset_cache: bool = True
    use_multi_threading: bool = False
