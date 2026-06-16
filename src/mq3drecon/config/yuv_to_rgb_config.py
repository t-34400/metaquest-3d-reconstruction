from dataclasses import dataclass


@dataclass
class Yuv2RgbConfig:
    blur_filter: bool
    blur_threshold: float

    exposure_filter: bool
    exposure_threshold_low: float
    exposure_threshold_high: float


    @classmethod
    def parse(cls, yuv_to_rgb_config_dict: dict) -> 'Yuv2RgbConfig':
        return cls(
            blur_filter=yuv_to_rgb_config_dict['blur_filter'],
            blur_threshold=yuv_to_rgb_config_dict['blur_threshold'],
            exposure_filter=yuv_to_rgb_config_dict['exposure_filter'],
            exposure_threshold_low=yuv_to_rgb_config_dict['exposure_threshold_low'],
            exposure_threshold_high=yuv_to_rgb_config_dict['exposure_threshold_high'],
        )