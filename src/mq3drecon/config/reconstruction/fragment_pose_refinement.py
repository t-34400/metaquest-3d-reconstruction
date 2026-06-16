from dataclasses import dataclass, field

from mq3drecon.config.reconstruction.device import DeviceSpec


@dataclass
class FragmentPoseRefinementConfig:
    device: DeviceSpec
    use_confidence_filtered_depth: bool = True
    confidence_threshold: float = 0.05
    valid_count_threshold: int = 4
    voxel_size: float = 0.01
    block_resolution: int = 16
    block_count: int = 50_000
    depth_max: float = 1.5
    trunc_voxel_multiplier: float = 8.0
    use_pre_filtering: bool = True
    pre_filter_every_k_points: float = 30
    pre_filter_max_corr_dist: float = 0.1
    pre_filter_inlier_rmse_threshold: float = 0.05
    pre_filter_fitness_threshold: float = 0.2
    icp_voxel_sizes: list[float] = field(default_factory=lambda: [0.05, 0.025, 0.0125])
    max_corr_dists: list[float] = field(default_factory=lambda: [0.1, 0.05, 0.025])
    max_iterations: list[int] = field(default_factory=lambda: [50, 31, 14])
    relative_fitnesses: list[float] = field(default_factory=lambda: [1e-6, 1e-6, 1e-6])
    relative_rmses: list[float] = field(default_factory=lambda: [1e-6, 1e-6, 1e-6])
    icp_fitness_threshold: float = 0.2
    icp_inlier_rmse_threshold: float = 0.05
    dist_threshold: float = 0.07
    edge_prune_threshold: float = 0.25
    use_multi_threading: bool = False
