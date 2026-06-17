from dataclasses import dataclass


@dataclass
class Depth2LinearConfig:
    clip_near_m: float = 0.1
    clip_far_m: float = 3.0
    use_cache: bool = True

    @classmethod
    def parse(cls, depth_to_linear_config_dict: dict) -> "Depth2LinearConfig":
        return cls(
            clip_near_m=depth_to_linear_config_dict["clip_near_m"],
            clip_far_m=depth_to_linear_config_dict["clip_far_m"],
            use_cache=depth_to_linear_config_dict["use_cache"],
        )
