from dataclasses import dataclass


@dataclass
class ImagePlaneInfo:
    buffer_size: int
    row_stride: int
    pixel_stride: int


@dataclass
class BaseTime:
    mono_time_ns: int
    unix_time_ns: int


@dataclass
class ImageFormatInfo:
    width: int
    height: int

    format: str

    planes: list[ImagePlaneInfo]

    base_time: BaseTime