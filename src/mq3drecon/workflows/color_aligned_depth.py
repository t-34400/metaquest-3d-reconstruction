from __future__ import annotations

from pathlib import Path

from mq3drecon.models.side import Side
from mq3drecon.processing.depth_conversion.color_aligned_depth_png import (
    ColorAlignedDepthPngExportResult,
    export_color_aligned_depth_pngs,
)


def run_color_aligned_depth_to_png(
    project_dir: Path,
    *,
    side: Side = Side.LEFT,
    write_metric_png: bool = False,
    write_preview_png: bool = True,
    depth_png_scale: float = 1000.0,
    depth_preview_min_m: float = 0.1,
    depth_preview_max_m: float | None = None,
) -> ColorAlignedDepthPngExportResult:
    return export_color_aligned_depth_pngs(
        project_dir=Path(project_dir),
        side=side,
        write_metric_png=write_metric_png,
        write_preview_png=write_preview_png,
        depth_png_scale=depth_png_scale,
        depth_preview_min_m=depth_preview_min_m,
        depth_preview_max_m=depth_preview_max_m,
    )
