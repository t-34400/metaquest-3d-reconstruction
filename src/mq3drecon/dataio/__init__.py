"""Data I/O APIs exposed by MQ3DRecon."""

__all__ = [
    "DataIO",
    "DepthDataIO",
    "ImageDataIO",
    "RGBDDataIO",
    "ReconstructionDataIO",
]


def __getattr__(name: str):
    if name == "DataIO":
        from mq3drecon.dataio.data_io import DataIO

        return DataIO
    if name == "DepthDataIO":
        from mq3drecon.dataio.depth_data_io import DepthDataIO

        return DepthDataIO
    if name == "ImageDataIO":
        from mq3drecon.dataio.image_data_io import ImageDataIO

        return ImageDataIO
    if name == "RGBDDataIO":
        from mq3drecon.dataio.rgbd_data_io import RGBDDataIO

        return RGBDDataIO
    if name == "ReconstructionDataIO":
        from mq3drecon.dataio.reconstruction_data_io import ReconstructionDataIO

        return ReconstructionDataIO
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
