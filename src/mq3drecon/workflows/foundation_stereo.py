from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np
import pandas as pd
import yaml
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm

from mq3drecon.config.foundation_stereo_config import FoundationStereoConfig
from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.camera_dataset import CameraDataset, DepthDataset
from mq3drecon.models.side import Side
from mq3drecon.processing.depth_conversion.color_aligned_depth_png import (
    save_depth_preview_png,
    save_metric_depth_png,
)
from mq3drecon.processing.stereo_depth.foundation_stereo_onnx import FoundationStereoOnnxModel
from mq3drecon.processing.stereo_depth.rectification import (
    StereoRectification,
    compute_stereo_rectification,
    inverse_rectify_left_depth,
    make_rectified_dataset,
    rectify_image,
)


class StereoDisparityModel(Protocol):
    def predict_disparity(self, left_image: np.ndarray, right_image: np.ndarray) -> np.ndarray:
        ...


@dataclass(frozen=True)
class StereoFramePair:
    left_index: int
    right_index: int


def _load_config_section(config_yml_path: Path, section_name: str) -> dict:
    with open(config_yml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    section = config.get(section_name)
    if not isinstance(section, dict):
        raise ValueError(f"Missing or invalid '{section_name}' section in config: {config_yml_path}")
    return section


def _resolve_config(
    config: FoundationStereoConfig | None,
    config_yml_path: Path | None,
    model_path: Path | None,
) -> FoundationStereoConfig:
    if config is not None and config_yml_path is not None:
        raise ValueError("Pass either config or config_yml_path, not both")
    if config is not None:
        resolved = config
    elif config_yml_path is not None:
        resolved = FoundationStereoConfig.parse(_load_config_section(config_yml_path, "foundation_stereo"))
    else:
        resolved = FoundationStereoConfig()

    if model_path is not None:
        resolved = FoundationStereoConfig(
            model_path=Path(model_path),
            execution_providers=resolved.execution_providers,
            input_height=resolved.input_height,
            input_width=resolved.input_width,
            preserve_aspect_ratio=resolved.preserve_aspect_ratio,
            padding_value=resolved.padding_value,
            normalize=resolved.normalize,
            min_disparity=resolved.min_disparity,
            max_depth_m=resolved.max_depth_m,
            baseline_m=resolved.baseline_m,
            max_pair_timestamp_delta_us=resolved.max_pair_timestamp_delta_us,
            output_sides=resolved.output_sides,
            save_rgba_png=resolved.save_rgba_png,
            save_color_aligned_depth=resolved.save_color_aligned_depth,
            cache_rectification_maps=resolved.cache_rectification_maps,
            skip_existing_outputs=resolved.skip_existing_outputs,
            save_depth_png=resolved.save_depth_png,
            depth_png_scale=resolved.depth_png_scale,
            save_depth_preview_png=resolved.save_depth_preview_png,
            depth_preview_min_m=resolved.depth_preview_min_m,
            depth_preview_max_m=resolved.depth_preview_max_m,
        )
    return resolved


def run_foundation_stereo_depth(
    project_dir: Path,
    model_path: Path | None = None,
    config_yml_path: Path | None = None,
    *,
    config: FoundationStereoConfig | None = None,
    disparity_model: StereoDisparityModel | None = None,
) -> None:
    resolved_config = _resolve_config(config=config, config_yml_path=config_yml_path, model_path=model_path)
    if disparity_model is None:
        if resolved_config.model_path is None:
            raise ValueError("model_path is required when disparity_model is not provided")
        disparity_model = FoundationStereoOnnxModel(resolved_config.model_path, resolved_config)

    data_io = DataIO(project_dir=Path(project_dir))
    left_dataset = data_io.color.load_color_dataset(Side.LEFT)
    right_dataset = data_io.color.load_color_dataset(Side.RIGHT)
    pairs = _resolve_stereo_pairs(data_io=data_io, left_dataset=left_dataset, right_dataset=right_dataset, config=resolved_config)
    if not pairs:
        raise ValueError("No stereo frame pairs found for FoundationStereo depth generation")

    left_rectifications: list[StereoRectification] = []
    rectification_cache: dict[tuple, StereoRectification] = {}
    left_indices: list[int] = []
    right_indices: list[int] = []
    left_file_names: list[str] = []
    right_file_names: list[str] = []
    depth_file_names: list[str] = []
    left_projections: list[np.ndarray] = []
    right_projections: list[np.ndarray] = []
    left_rectification_matrices: list[np.ndarray] = []
    right_rectification_matrices: list[np.ndarray] = []
    baselines: list[float] = []

    for pair in tqdm(pairs, desc="FoundationStereo depth", unit="pair"):
        left_timestamp = int(left_dataset.timestamps[pair.left_index])
        right_timestamp = int(right_dataset.timestamps[pair.right_index])
        rectification = _compute_or_load_rectification(
            left_dataset=left_dataset,
            right_dataset=right_dataset,
            pair=pair,
            config=resolved_config,
            cache=rectification_cache,
        )
        depth_exists = data_io.path_config.rgbd.get_rectified_stereo_depth_path(Side.LEFT, left_timestamp).exists()
        compat_depth_exists = data_io.path_config.rgbd.get_color_aligned_depth_path(Side.LEFT, left_timestamp).exists()
        rectified_left_exists = data_io.path_config.image.get_rectified_stereo_color_path(Side.LEFT, left_timestamp).exists()
        rectified_right_exists = data_io.path_config.image.get_rectified_stereo_color_path(Side.RIGHT, right_timestamp).exists()
        needs_rectified_color = not (resolved_config.skip_existing_outputs and rectified_left_exists and rectified_right_exists)
        needs_depth = not (resolved_config.skip_existing_outputs and depth_exists)
        needs_compat_depth = resolved_config.save_color_aligned_depth and not (resolved_config.skip_existing_outputs and compat_depth_exists)
        needs_rgba_png = resolved_config.save_rgba_png and not (
            resolved_config.skip_existing_outputs
            and data_io.path_config.image.get_mruk_rgba_png_path(Side.LEFT, left_timestamp).exists()
            and data_io.path_config.image.get_mruk_rgba_png_path(Side.RIGHT, right_timestamp).exists()
        )

        rectified_left = None
        rectified_right = None
        left_image = None
        right_image = None

        if needs_rectified_color or needs_depth or needs_rgba_png:
            left_image = data_io.color.load_color_image(left_dataset, pair.left_index)
            right_image = data_io.color.load_color_image(right_dataset, pair.right_index)

        if needs_rectified_color or needs_depth:
            rectified_left = rectify_image(left_image, rectification.left_map_x, rectification.left_map_y)
            rectified_right = rectify_image(right_image, rectification.right_map_x, rectification.right_map_y)

        if needs_rectified_color:
            data_io.color.save_rectified_stereo_rgb_image(rectified_left, Side.LEFT, left_timestamp)
            data_io.color.save_rectified_stereo_rgb_image(rectified_right, Side.RIGHT, right_timestamp)

        if needs_rgba_png:
            _save_rgba_png(data_io, Side.LEFT, left_timestamp, left_image)
            _save_rgba_png(data_io, Side.RIGHT, right_timestamp, right_image)

        if Side.LEFT in resolved_config.output_sides:
            if needs_depth:
                disparity = disparity_model.predict_disparity(rectified_left, rectified_right)
                depth = _disparity_to_depth(
                    disparity=disparity,
                    fx=float(rectification.left_intrinsic[0, 0]),
                    baseline_m=_resolve_rectified_baseline(rectification, resolved_config),
                    config=resolved_config,
                )
                data_io.rgbd.save_rectified_stereo_depth(depth, side=Side.LEFT, timestamp=left_timestamp)
            elif needs_compat_depth:
                depth = data_io.rgbd.load_rectified_stereo_depth(Side.LEFT, left_timestamp)
            else:
                depth = None

            if needs_compat_depth:
                color_aligned_depth = inverse_rectify_left_depth(depth, rectification)
                data_io.rgbd.save_color_aligned_depth(depth_map=color_aligned_depth, side=Side.LEFT, timestamp=left_timestamp)
            elif resolved_config.save_color_aligned_depth and (resolved_config.save_depth_png or resolved_config.save_depth_preview_png):
                color_aligned_depth = data_io.rgbd.load_color_aligned_depth(Side.LEFT, left_timestamp)
            else:
                color_aligned_depth = None

            if resolved_config.save_color_aligned_depth:
                if resolved_config.save_depth_png and not (
                    resolved_config.skip_existing_outputs
                    and data_io.path_config.rgbd.get_color_aligned_depth_png_path(Side.LEFT, left_timestamp).exists()
                ):
                    _save_depth_png(data_io, Side.LEFT, left_timestamp, color_aligned_depth, resolved_config.depth_png_scale)
                if resolved_config.save_depth_preview_png and not (
                    resolved_config.skip_existing_outputs
                    and data_io.path_config.rgbd.get_color_aligned_depth_preview_png_path(Side.LEFT, left_timestamp).exists()
                ):
                    _save_depth_preview_png(data_io, Side.LEFT, left_timestamp, color_aligned_depth, resolved_config)
            depth_file_names.append(data_io.path_config.rgbd.get_rectified_stereo_depth_filename(left_timestamp))

        left_indices.append(pair.left_index)
        right_indices.append(pair.right_index)
        left_file_names.append(f"{left_timestamp}.png")
        right_file_names.append(f"{right_timestamp}.png")
        left_rectifications.append(rectification)
        left_projections.append(rectification.left_projection)
        right_projections.append(rectification.right_projection)
        left_rectification_matrices.append(rectification.left_rectification)
        right_rectification_matrices.append(rectification.right_rectification)
        baselines.append(_resolve_rectified_baseline(rectification, resolved_config))

    _save_rectified_datasets(
        data_io=data_io,
        left_dataset=left_dataset,
        right_dataset=right_dataset,
        left_indices=left_indices,
        right_indices=right_indices,
        left_file_names=left_file_names,
        right_file_names=right_file_names,
        depth_file_names=depth_file_names,
        rectifications=left_rectifications,
        config=resolved_config,
    )
    data_io.rgbd.save_stereo_rectification(
        left_projection=np.asarray(left_projections, dtype=np.float32),
        right_projection=np.asarray(right_projections, dtype=np.float32),
        left_rectification=np.asarray(left_rectification_matrices, dtype=np.float32),
        right_rectification=np.asarray(right_rectification_matrices, dtype=np.float32),
        baseline_m=np.asarray(baselines, dtype=np.float32),
        left_timestamps=np.asarray([int(left_dataset.timestamps[i]) for i in left_indices], dtype=np.int64),
        right_timestamps=np.asarray([int(right_dataset.timestamps[i]) for i in right_indices], dtype=np.int64),
    )



def _compute_or_load_rectification(
    left_dataset: CameraDataset,
    right_dataset: CameraDataset,
    pair: StereoFramePair,
    config: FoundationStereoConfig,
    cache: dict[tuple, StereoRectification],
) -> StereoRectification:
    build_inverse_map = config.save_color_aligned_depth
    if not config.cache_rectification_maps:
        return compute_stereo_rectification(
            left_dataset,
            right_dataset,
            pair.left_index,
            pair.right_index,
            build_left_inverse_map=build_inverse_map,
        )

    key = _rectification_cache_key(left_dataset, right_dataset, pair, build_inverse_map)
    rectification = cache.get(key)
    if rectification is None:
        rectification = compute_stereo_rectification(
            left_dataset,
            right_dataset,
            pair.left_index,
            pair.right_index,
            build_left_inverse_map=build_inverse_map,
        )
        cache[key] = rectification
    return rectification


def _rectification_cache_key(
    left_dataset: CameraDataset,
    right_dataset: CameraDataset,
    pair: StereoFramePair,
    build_inverse_map: bool,
) -> tuple:
    left_index = pair.left_index
    right_index = pair.right_index
    left_rotation = np.asarray(left_dataset.transforms.rotations[left_index], dtype=np.float64)
    right_rotation = np.asarray(right_dataset.transforms.rotations[right_index], dtype=np.float64)
    left_position = np.asarray(left_dataset.transforms.positions[left_index], dtype=np.float64)
    right_position = np.asarray(right_dataset.transforms.positions[right_index], dtype=np.float64)
    relative_rotation = (R.from_quat(right_rotation).inv() * R.from_quat(left_rotation)).as_quat()
    relative_rotation = np.round(relative_rotation, 8)
    relative_translation = np.round(R.from_quat(right_rotation).inv().apply(left_position - right_position), 8)
    return (
        int(left_dataset.widths[left_index]),
        int(left_dataset.heights[left_index]),
        int(right_dataset.widths[right_index]),
        int(right_dataset.heights[right_index]),
        tuple(np.round([left_dataset.fx[left_index], left_dataset.fy[left_index], left_dataset.cx[left_index], left_dataset.cy[left_index]], 8)),
        tuple(np.round([right_dataset.fx[right_index], right_dataset.fy[right_index], right_dataset.cx[right_index], right_dataset.cy[right_index]], 8)),
        tuple(relative_rotation),
        tuple(relative_translation),
        bool(build_inverse_map),
    )

def _save_rectified_datasets(
    data_io: DataIO,
    left_dataset: CameraDataset,
    right_dataset: CameraDataset,
    left_indices: list[int],
    right_indices: list[int],
    left_file_names: list[str],
    right_file_names: list[str],
    depth_file_names: list[str],
    rectifications: list[StereoRectification],
    config: FoundationStereoConfig,
) -> None:
    left_color_dataset = make_rectified_dataset(
        source_dataset=left_dataset,
        indices=left_indices,
        side=Side.LEFT,
        directory_relative_path="left_rectified_stereo_color",
        file_names=left_file_names,
        rectifications=rectifications,
    )
    right_color_dataset = make_rectified_dataset(
        source_dataset=right_dataset,
        indices=right_indices,
        side=Side.RIGHT,
        directory_relative_path="right_rectified_stereo_color",
        file_names=right_file_names,
        rectifications=rectifications,
    )
    data_io.color.save_rectified_stereo_color_dataset(left_color_dataset, Side.LEFT)
    data_io.color.save_rectified_stereo_color_dataset(right_color_dataset, Side.RIGHT)

    if depth_file_names:
        depth_dataset = DepthDataset(
            directory_relative_path="left_rectified_stereo_depth",
            image_file_names=np.asarray(depth_file_names),
            timestamps=left_color_dataset.timestamps,
            fx=left_color_dataset.fx,
            fy=left_color_dataset.fy,
            cx=left_color_dataset.cx,
            cy=left_color_dataset.cy,
            transforms=left_color_dataset.transforms,
            widths=left_color_dataset.widths,
            heights=left_color_dataset.heights,
            nears=np.zeros(len(left_color_dataset), dtype=np.float32),
            fars=np.full(
                len(left_color_dataset),
                np.inf if config.max_depth_m is None else float(config.max_depth_m),
                dtype=np.float32,
            ),
        )
        data_io.rgbd.save_rectified_stereo_depth_dataset(depth_dataset, Side.LEFT)


def _resolve_stereo_pairs(
    data_io: DataIO,
    left_dataset: CameraDataset,
    right_dataset: CameraDataset,
    config: FoundationStereoConfig,
) -> list[StereoFramePair]:
    pairs_csv = data_io.path_config.image.get_mruk_stereo_pairs_csv_path()
    if pairs_csv.exists():
        return _resolve_pairs_from_csv(pairs_csv, left_dataset, right_dataset)
    return _resolve_pairs_by_timestamp(left_dataset, right_dataset, config.max_pair_timestamp_delta_us)


def _resolve_pairs_by_timestamp(
    left_dataset: CameraDataset,
    right_dataset: CameraDataset,
    max_delta_us: int | None,
) -> list[StereoFramePair]:
    pairs: list[StereoFramePair] = []
    right_timestamps = np.asarray(right_dataset.timestamps, dtype=np.int64)
    for left_index, left_timestamp in enumerate(np.asarray(left_dataset.timestamps, dtype=np.int64)):
        right_index = int(np.argmin(np.abs(right_timestamps - left_timestamp)))
        delta = abs(int(right_timestamps[right_index]) - int(left_timestamp))
        if max_delta_us is None or delta <= max_delta_us:
            pairs.append(StereoFramePair(left_index=left_index, right_index=right_index))
    return pairs


def _resolve_pairs_from_csv(path: Path, left_dataset: CameraDataset, right_dataset: CameraDataset) -> list[StereoFramePair]:
    df = pd.read_csv(path)
    left_file_col = _first_existing_column(df, ["left_file_name", "left_filename", "left_frame", "left_image"])
    right_file_col = _first_existing_column(df, ["right_file_name", "right_filename", "right_frame", "right_image"])
    left_time_col = _first_existing_column(df, ["left_timestamp_us_realtime", "left_timestamp_us", "left_timestamp"])
    right_time_col = _first_existing_column(df, ["right_timestamp_us_realtime", "right_timestamp_us", "right_timestamp"])

    if left_file_col and right_file_col:
        left_lookup = {str(name): i for i, name in enumerate(left_dataset.image_file_names)}
        right_lookup = {str(name): i for i, name in enumerate(right_dataset.image_file_names)}
        pairs = []
        for row in df.itertuples(index=False):
            left_name = str(getattr(row, left_file_col))
            right_name = str(getattr(row, right_file_col))
            if left_name in left_lookup and right_name in right_lookup:
                pairs.append(StereoFramePair(left_lookup[left_name], right_lookup[right_name]))
        return pairs

    if left_time_col and right_time_col:
        left_lookup = {int(ts): i for i, ts in enumerate(left_dataset.timestamps)}
        right_lookup = {int(ts): i for i, ts in enumerate(right_dataset.timestamps)}
        pairs = []
        for row in df.itertuples(index=False):
            left_ts = int(getattr(row, left_time_col))
            right_ts = int(getattr(row, right_time_col))
            if left_ts in left_lookup and right_ts in right_lookup:
                pairs.append(StereoFramePair(left_lookup[left_ts], right_lookup[right_ts]))
        return pairs

    raise ValueError(f"Unsupported stereo pair CSV schema: {path}")


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def _resolve_rectified_baseline(rectification: StereoRectification, config: FoundationStereoConfig) -> float:
    if config.baseline_m is not None:
        return float(config.baseline_m)
    return rectification.baseline_m


def _disparity_to_depth(
    disparity: np.ndarray,
    fx: float,
    baseline_m: float,
    config: FoundationStereoConfig,
) -> np.ndarray:
    valid = disparity > config.min_disparity
    safe_disparity = np.where(valid, disparity, np.nan).astype(np.float32)
    depth = (fx * baseline_m / safe_disparity).astype(np.float32)
    if config.max_depth_m is not None:
        depth = np.where(depth <= config.max_depth_m, depth, np.nan).astype(np.float32)
    return depth


def _save_rgba_png(data_io: DataIO, side: Side, timestamp: int, image: np.ndarray) -> None:
    path = data_io.path_config.image.get_mruk_rgba_png_path(side=side, timestamp=timestamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError(f"Unsupported RGBA debug image shape: {image.shape}")
    if image.shape[2] == 4:
        output = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
    else:
        output = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), output)


def _save_depth_preview_png(
    data_io: DataIO,
    side: Side,
    timestamp: int,
    depth: np.ndarray,
    config: FoundationStereoConfig,
) -> None:
    save_depth_preview_png(
        depth=depth,
        path=data_io.path_config.rgbd.get_color_aligned_depth_preview_png_path(side=side, timestamp=timestamp),
        min_m=config.depth_preview_min_m,
        max_m=config.depth_preview_max_m if config.depth_preview_max_m is not None else config.max_depth_m,
    )


def _save_depth_png(data_io: DataIO, side: Side, timestamp: int, depth: np.ndarray, scale: float) -> None:
    save_metric_depth_png(
        depth=depth,
        path=data_io.path_config.rgbd.get_color_aligned_depth_png_path(side=side, timestamp=timestamp),
        scale=scale,
    )
