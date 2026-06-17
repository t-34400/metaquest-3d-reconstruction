from mq3drecon.layouts.project_layout import (
    DepthPathConfig,
    ImagePathConfig,
    LegacyProjectLayout,
    RGBDPathConfig,
    ReconstructionPathConfig,
)


class ProjectPathConfig(LegacyProjectLayout):
    pass


__all__ = [
    "DepthPathConfig",
    "ImagePathConfig",
    "LegacyProjectLayout",
    "ProjectPathConfig",
    "RGBDPathConfig",
    "ReconstructionPathConfig",
]
