from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.side import Side


@dataclass(frozen=True)
class ColorAlignedDepthPngExportResult:
    side: Side
    metric_png_count: int
    preview_png_count: int


def save_metric_depth_png(depth: np.ndarray, path: Path, scale: float = 1000.0) -> None:
    if scale <= 0.0:
        raise ValueError("depth_png_scale must be positive")
    path.parent.mkdir(parents=True, exist_ok=True)
    finite_positive = np.isfinite(depth) & (depth > 0.0)
    scaled = np.zeros(depth.shape, dtype=np.float32)
    scaled[finite_positive] = depth[finite_positive] * float(scale)
    png = np.clip(np.rint(scaled), 0, np.iinfo(np.uint16).max).astype(np.uint16)
    cv2.imwrite(str(path), png)


def save_depth_preview_png(
    depth: np.ndarray,
    path: Path,
    *,
    min_m: float = 0.1,
    max_m: float | None = None,
) -> None:
    resolved_min_m = float(min_m)
    resolved_max_m = _resolve_preview_max(depth=depth, min_m=resolved_min_m, max_m=max_m)
    if resolved_min_m < 0.0 or resolved_max_m <= resolved_min_m:
        raise ValueError("depth preview range must satisfy 0 <= depth_preview_min_m < depth_preview_max_m")

    path.parent.mkdir(parents=True, exist_ok=True)
    finite_positive = np.isfinite(depth) & (depth > 0.0)
    normalized = np.zeros(depth.shape, dtype=np.float32)
    normalized[finite_positive] = (depth[finite_positive] - resolved_min_m) / (resolved_max_m - resolved_min_m)
    png = np.clip(np.rint(normalized * 255.0), 0, 255).astype(np.uint8)
    cv2.imwrite(str(path), png)


def export_color_aligned_depth_pngs(
    project_dir: Path,
    *,
    side: Side,
    write_metric_png: bool = False,
    write_preview_png: bool = True,
    depth_png_scale: float = 1000.0,
    depth_preview_min_m: float = 0.1,
    depth_preview_max_m: float | None = None,
) -> ColorAlignedDepthPngExportResult:
    if not write_metric_png and not write_preview_png:
        raise ValueError("At least one of write_metric_png or write_preview_png must be enabled")

    data_io = DataIO(project_dir=Path(project_dir))
    depth_paths = data_io.path_config.rgbd.get_color_aligned_depth_dir(side=side).glob("*.npy")
    depth_paths = sorted(depth_paths)
    if not depth_paths:
        depth_dir = data_io.path_config.rgbd.get_color_aligned_depth_dir(side=side)
        raise FileNotFoundError(f"No color-aligned depth maps found for {side.name}: {depth_dir}")

    metric_png_count = 0
    preview_png_count = 0
    for depth_path in tqdm(depth_paths, desc=f"[{side.name}] Exporting color-aligned depth PNG", unit="map"):
        timestamp = int(depth_path.stem)
        depth = np.load(depth_path).astype(np.float32, copy=False)
        if write_metric_png:
            save_metric_depth_png(
                depth=depth,
                path=data_io.path_config.rgbd.get_color_aligned_depth_png_path(side=side, timestamp=timestamp),
                scale=depth_png_scale,
            )
            metric_png_count += 1
        if write_preview_png:
            save_depth_preview_png(
                depth=depth,
                path=data_io.path_config.rgbd.get_color_aligned_depth_preview_png_path(side=side, timestamp=timestamp),
                min_m=depth_preview_min_m,
                max_m=depth_preview_max_m,
            )
            preview_png_count += 1

    return ColorAlignedDepthPngExportResult(
        side=side,
        metric_png_count=metric_png_count,
        preview_png_count=preview_png_count,
    )


def _resolve_preview_max(depth: np.ndarray, min_m: float, max_m: float | None) -> float:
    if max_m is not None:
        return float(max_m)
    finite_positive = depth[np.isfinite(depth) & (depth > 0.0)]
    if finite_positive.size == 0:
        return min_m + 1.0
    percentile = float(np.percentile(finite_positive, 99.0))
    if percentile <= min_m:
        return min_m + 1.0
    return percentile
