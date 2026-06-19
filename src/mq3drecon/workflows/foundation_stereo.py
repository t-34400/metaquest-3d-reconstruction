from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

from mq3drecon.config.foundation_stereo_config import FoundationStereoConfig
from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.camera_dataset import CameraDataset
from mq3drecon.models.side import Side
from mq3drecon.processing.stereo_depth.foundation_stereo_onnx import FoundationStereoOnnxModel


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
            save_depth_png=resolved.save_depth_png,
            depth_png_scale=resolved.depth_png_scale,
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

    for pair in tqdm(pairs, desc="FoundationStereo depth", unit="pair"):
        left_image = data_io.color.load_color_image(left_dataset, pair.left_index)
        right_image = data_io.color.load_color_image(right_dataset, pair.right_index)

        if resolved_config.save_rgba_png:
            _save_rgba_png(data_io, Side.LEFT, int(left_dataset.timestamps[pair.left_index]), left_image)
            _save_rgba_png(data_io, Side.RIGHT, int(right_dataset.timestamps[pair.right_index]), right_image)

        if Side.LEFT in resolved_config.output_sides:
            disparity = disparity_model.predict_disparity(left_image, right_image)
            depth = _disparity_to_depth(
                disparity=disparity,
                fx=float(left_dataset.fx[pair.left_index]),
                baseline_m=_resolve_baseline(left_dataset, right_dataset, pair, resolved_config),
                config=resolved_config,
            )
            left_timestamp = int(left_dataset.timestamps[pair.left_index])
            data_io.rgbd.save_color_aligned_depth(
                depth_map=depth,
                side=Side.LEFT,
                timestamp=left_timestamp,
            )
            if resolved_config.save_depth_png:
                _save_depth_png(data_io, Side.LEFT, left_timestamp, depth, resolved_config.depth_png_scale)

        if Side.RIGHT in resolved_config.output_sides:
            disparity = disparity_model.predict_disparity(right_image, left_image)
            depth = _disparity_to_depth(
                disparity=disparity,
                fx=float(right_dataset.fx[pair.right_index]),
                baseline_m=_resolve_baseline(left_dataset, right_dataset, pair, resolved_config),
                config=resolved_config,
            )
            right_timestamp = int(right_dataset.timestamps[pair.right_index])
            data_io.rgbd.save_color_aligned_depth(
                depth_map=depth,
                side=Side.RIGHT,
                timestamp=right_timestamp,
            )
            if resolved_config.save_depth_png:
                _save_depth_png(data_io, Side.RIGHT, right_timestamp, depth, resolved_config.depth_png_scale)


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


def _resolve_baseline(
    left_dataset: CameraDataset,
    right_dataset: CameraDataset,
    pair: StereoFramePair,
    config: FoundationStereoConfig,
) -> float:
    if config.baseline_m is not None:
        return float(config.baseline_m)
    left_position = np.asarray(left_dataset.transforms.positions[pair.left_index], dtype=np.float64)
    right_position = np.asarray(right_dataset.transforms.positions[pair.right_index], dtype=np.float64)
    baseline = float(np.linalg.norm(left_position - right_position))
    if baseline <= 0.0:
        raise ValueError("Stereo baseline is zero; pass baseline_m in FoundationStereoConfig")
    return baseline


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


def _save_depth_png(data_io: DataIO, side: Side, timestamp: int, depth: np.ndarray, scale: float) -> None:
    if scale <= 0.0:
        raise ValueError("depth_png_scale must be positive")
    path = data_io.path_config.rgbd.get_color_aligned_depth_png_path(side=side, timestamp=timestamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    finite_positive = np.isfinite(depth) & (depth > 0.0)
    scaled = np.zeros(depth.shape, dtype=np.float32)
    scaled[finite_positive] = depth[finite_positive] * float(scale)
    png = np.clip(np.rint(scaled), 0, np.iinfo(np.uint16).max).astype(np.uint16)
    cv2.imwrite(str(path), png)
