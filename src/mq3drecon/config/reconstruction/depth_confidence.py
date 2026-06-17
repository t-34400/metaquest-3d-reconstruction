from dataclasses import dataclass


@dataclass
class DepthConfidenceEstimationConfig:
    target_frame_range: int = 10
    depth_max: float = 3.0
    error_threshold: float = 0.05
    skip_if_output_dir_exists: bool = True
    use_dataset_cache: bool = True
    use_multi_threading: bool = True
