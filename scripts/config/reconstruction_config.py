from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, get_args, get_origin

DeviceSpec = Any
DEFAULT_DEVICE = "CPU:0"


def to_open3d_device(device: DeviceSpec):
    import open3d as o3d

    if isinstance(device, str):
        return o3d.core.Device(device)
    return device


@dataclass
class DepthConfidenceEstimationConfig:
    target_frame_range: int = 10
    depth_max: float = 3.0
    error_threshold: float = 0.05
    skip_if_output_dir_exists: bool = True
    use_dataset_cache: bool = True
    use_multi_threading: bool = True


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

    @property
    def icp_criteria_list(self):
        import open3d as o3d

        return [
            o3d.t.pipelines.registration.ICPConvergenceCriteria(
                max_iteration=self.max_iterations[i],
                relative_fitness=self.relative_fitnesses[i],
                relative_rmse=self.relative_rmses[i],
            )
            for i in range(len(self.icp_voxel_sizes))
        ]


@dataclass
class IntegrationConfig:
    device: DeviceSpec
    use_confidence_filtered_depth: bool = True
    confidence_threshold: float = 0.05
    valid_count_threshold: int = 4
    voxel_size: float = 0.01
    block_resolution: int = 16
    block_count: int = 50_000
    depth_max: float = 1.5
    trunc_voxel_multiplier: float = 8.0


@dataclass
class ColorOptimizationConfig:
    device: DeviceSpec
    weight_threshold: float = 3.0
    estimated_vertex_number: int = -1
    interval: int = 10
    max_iteration: int = 100
    use_dataset_cache: bool = True


@dataclass
class ColorAlignedDepthRenderingConfig:
    weight_threshold: float = 3.0
    estimated_vertex_number: int = -1
    only_use_optimized_dataset: bool = True


@dataclass
class ReconstructionConfig:
    device: DeviceSpec = DEFAULT_DEVICE

    # Step 0: Dataset generation
    use_dataset_cache: bool = True

    # Step 1: Depth confidence estimation
    estimate_depth_confidences: bool = True

    # Step 2: Depth pose optimization
    optimize_depth_pose: bool = True
    use_fragment_dataset_cache: bool = True
    use_optimized_dataset_cache: bool = True

    # Step 3: TSDF integration
    use_colorless_vbg_cache: bool = True
    visualize_colorless_pcd: bool = True

    # Step 4: Color map optimization
    optimize_color_pose: bool = True
    visualize_colored_mesh: bool = True

    # Step 5: Sample point cloud from colored mesh
    sample_point_cloud_from_colored_mesh: bool = True
    points_per_vertex_ratio: float = 1.0

    # Step 6: Color-aligned depth map generation
    render_color_aligned_depth: bool = True

    confidence_estimation: DepthConfidenceEstimationConfig = field(init=False)
    fragment_generation: FragmentGenerationConfig = field(init=False)
    fragment_pose_refinement: FragmentPoseRefinementConfig = field(init=False)
    depth_integration: IntegrationConfig = field(init=False)
    color_optimization: ColorOptimizationConfig = field(init=False)
    color_aligned_depth_rendering: ColorAlignedDepthRenderingConfig = field(init=False)

    def __post_init__(self):
        self.confidence_estimation = DepthConfidenceEstimationConfig()
        self.fragment_generation = FragmentGenerationConfig(device=self.device)
        self.fragment_pose_refinement = FragmentPoseRefinementConfig(device=self.device)
        self.depth_integration = IntegrationConfig(device=self.device)
        self.color_optimization = ColorOptimizationConfig(device=self.device)
        self.color_aligned_depth_rendering = ColorAlignedDepthRenderingConfig()

        if self.use_dataset_cache:
            self._enable_dataset_cache_on_subconfigs()

    def open3d_device(self):
        return to_open3d_device(self.device)

    def _enable_dataset_cache_on_subconfigs(self):
        for attr_name in vars(self):
            subconfig = getattr(self, attr_name)
            if hasattr(subconfig, "use_dataset_cache"):
                setattr(subconfig, "use_dataset_cache", True)

    @classmethod
    def parse(cls, config_dict: dict[str, Any]) -> "ReconstructionConfig":
        def init_dataclass(dc_cls, d: dict, parent_device=None):
            kwargs = {}
            post_inits = {}

            for f in fields(dc_cls):
                if f.name not in d:
                    continue

                value = d[f.name]
                hint = f.type

                if _is_device_field(f.name, hint):
                    value = str(value) if isinstance(value, str) else value
                elif is_dataclass(hint) and isinstance(value, dict):
                    value = init_dataclass(hint, value, parent_device=parent_device)
                elif hint is float and isinstance(value, str):
                    value = float(value)
                elif hint is int and isinstance(value, str):
                    value = int(value)
                elif hint is bool and isinstance(value, str):
                    value = value.lower() in ("true", "1")
                elif get_origin(hint) is list:
                    subtype = get_args(hint)[0]
                    if isinstance(value, list):
                        if subtype is float:
                            value = [float(v) for v in value]
                        elif subtype is int:
                            value = [int(v) for v in value]
                        elif subtype is str:
                            value = [str(v) for v in value]
                        elif subtype is bool:
                            value = [v.lower() in ("true", "1") if isinstance(v, str) else bool(v) for v in value]

                if f.init:
                    kwargs[f.name] = value
                else:
                    post_inits[f.name] = value

            needs_device = any(_is_device_field(f.name, f.type) for f in fields(dc_cls))
            if needs_device and "device" not in kwargs:
                if parent_device is not None:
                    kwargs["device"] = parent_device
                else:
                    raise ValueError(f"{dc_cls.__name__} requires 'device', but none was provided.")

            instance = dc_cls(**kwargs)

            for k, v in post_inits.items():
                setattr(instance, k, v)

            return instance

        device = config_dict.get("device", DEFAULT_DEVICE)
        config = init_dataclass(cls, config_dict, parent_device=device)

        if config.use_dataset_cache:
            for attr_name in vars(config):
                attr = getattr(config, attr_name)
                if hasattr(attr, "use_dataset_cache") and attr.use_dataset_cache is not False:
                    setattr(attr, "use_dataset_cache", True)

        return config


def _is_device_field(name: str, hint: Any) -> bool:
    return name == "device" and (hint is DeviceSpec or hint is Any or hint == "DeviceSpec")
