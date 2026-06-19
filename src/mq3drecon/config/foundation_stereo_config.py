from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mq3drecon.models.side import Side


@dataclass(frozen=True)
class FoundationStereoConfig:
    model_path: Path | None = None
    execution_providers: tuple[str, ...] = ("CUDAExecutionProvider", "CPUExecutionProvider")
    input_height: int | None = None
    input_width: int | None = None
    preserve_aspect_ratio: bool = True
    padding_value: float = 0.0
    normalize: str = "imagenet"
    min_disparity: float = 0.1
    max_depth_m: float | None = 20.0
    baseline_m: float | None = None
    max_pair_timestamp_delta_us: int | None = None
    output_sides: tuple[Side, ...] = field(default_factory=lambda: (Side.LEFT,))
    save_rgba_png: bool = False
    save_depth_png: bool = False
    depth_png_scale: float = 1000.0
    save_depth_preview_png: bool = False
    depth_preview_min_m: float = 0.1
    depth_preview_max_m: float | None = None

    def __post_init__(self) -> None:
        if tuple(self.output_sides) != (Side.LEFT,):
            raise ValueError("FoundationStereo depth generation supports only left color-aligned depth output")

    @staticmethod
    def parse(config: dict[str, Any]) -> "FoundationStereoConfig":
        if not isinstance(config, dict):
            raise ValueError("FoundationStereoConfig.parse expects a dictionary")

        values = dict(config)
        if values.get("model_path") is not None:
            values["model_path"] = Path(values["model_path"])
        if values.get("execution_providers") is not None:
            values["execution_providers"] = tuple(str(v) for v in values["execution_providers"])
        if values.get("output_sides") is not None:
            values["output_sides"] = tuple(_parse_side(v) for v in values["output_sides"])
        return FoundationStereoConfig(**values)


def _parse_side(value: str | Side) -> Side:
    if isinstance(value, Side):
        return value
    return Side[str(value).upper()]
