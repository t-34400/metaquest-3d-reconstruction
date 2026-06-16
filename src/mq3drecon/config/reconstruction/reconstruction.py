from dataclasses import dataclass, field
from typing import Any

from mq3drecon.config.reconstruction.color_aligned_depth import ColorAlignedDepthRenderingConfig
from mq3drecon.config.reconstruction.color_optimization import ColorOptimizationConfig
from mq3drecon.config.reconstruction.depth_confidence import DepthConfidenceEstimationConfig
from mq3drecon.config.reconstruction.device import DEFAULT_DEVICE, DeviceSpec
from mq3drecon.config.reconstruction.fragment_generation import FragmentGenerationConfig
from mq3drecon.config.reconstruction.fragment_pose_refinement import FragmentPoseRefinementConfig
from mq3drecon.config.reconstruction.integration import IntegrationConfig
from mq3drecon.config.reconstruction.parser import init_dataclass_from_dict


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

    def _enable_dataset_cache_on_subconfigs(self):
        for attr_name in vars(self):
            subconfig = getattr(self, attr_name)
            if hasattr(subconfig, "use_dataset_cache"):
                setattr(subconfig, "use_dataset_cache", True)

    @classmethod
    def parse(cls, config_dict: dict[str, Any]) -> "ReconstructionConfig":
        device = config_dict.get("device", DEFAULT_DEVICE)
        config = init_dataclass_from_dict(cls, config_dict, parent_device=device)

        if config.use_dataset_cache:
            for attr_name in vars(config):
                attr = getattr(config, attr_name)
                if hasattr(attr, "use_dataset_cache") and attr.use_dataset_cache is not False:
                    setattr(attr, "use_dataset_cache", True)

        return config
