"""Configuration APIs exposed by MQ3DRecon."""

from mq3drecon.config.depth_to_linear_config import Depth2LinearConfig
from mq3drecon.config.project_path_config import ProjectPathConfig
from mq3drecon.layouts import LegacyProjectLayout
from mq3drecon.config.yuv_to_rgb_config import Yuv2RgbConfig

__all__ = [
    "ColorAlignedDepthRenderingConfig",
    "ColorOptimizationConfig",
    "Depth2LinearConfig",
    "DepthConfidenceEstimationConfig",
    "FragmentGenerationConfig",
    "FragmentPoseRefinementConfig",
    "IntegrationConfig",
    "PipelineConfigs",
    "LegacyProjectLayout",
    "ProjectPathConfig",
    "ReconstructionConfig",
    "Yuv2RgbConfig",
]

_RECONSTRUCTION_CONFIG_EXPORTS = {
    "ColorAlignedDepthRenderingConfig",
    "ColorOptimizationConfig",
    "DepthConfidenceEstimationConfig",
    "FragmentGenerationConfig",
    "FragmentPoseRefinementConfig",
    "IntegrationConfig",
    "ReconstructionConfig",
}


def __getattr__(name: str):
    if name == "PipelineConfigs":
        from mq3drecon.config.pipeline_configs import PipelineConfigs

        return PipelineConfigs
    if name in _RECONSTRUCTION_CONFIG_EXPORTS:
        from mq3drecon.config import reconstruction_config

        return getattr(reconstruction_config, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
