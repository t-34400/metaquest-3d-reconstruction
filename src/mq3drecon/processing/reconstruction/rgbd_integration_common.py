from __future__ import annotations

import numpy as np
import open3d as o3d

from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.camera_dataset import CameraDataset, DepthDataset
from mq3drecon.models.side import Side


def make_tensor_image(array: np.ndarray, dtype: o3d.core.Dtype, device: o3d.core.Device) -> o3d.t.geometry.Image:
    return o3d.t.geometry.Image(o3d.core.Tensor(np.ascontiguousarray(array), dtype=dtype, device=device))


def normalize_color_for_float_depth(color: np.ndarray) -> np.ndarray:
    return color.astype(np.float32, copy=False) / 255.0


def load_rgbd_images(
    data_io: DataIO,
    color_dataset: CameraDataset,
    depth_dataset: DepthDataset,
    index: int,
    device: o3d.core.Device,
    *,
    depth_kind: str = "color_aligned",
) -> tuple[o3d.t.geometry.Image, o3d.t.geometry.Image]:
    color = data_io.color.load_color_rgb_image(dataset=color_dataset, index=index)
    if depth_kind == "rectified_stereo":
        depth = data_io.rgbd.load_rectified_stereo_depth_by_index(side=Side.LEFT, dataset=depth_dataset, index=index)
    else:
        depth = data_io.rgbd.load_color_aligned_depth_by_index(side=Side.LEFT, dataset=depth_dataset, index=index)
    if depth is None:
        raise FileNotFoundError(f"Stereo-generated depth is missing for index {index}")

    expected_shape = (int(depth_dataset.heights[index]), int(depth_dataset.widths[index]), 3)
    if color.shape != expected_shape:
        raise ValueError(
            "Color image shape does not match stereo-generated depth resolution: "
            f"timestamp={depth_dataset.timestamps[index]}, expected={expected_shape}, got={color.shape}"
        )

    color_float = normalize_color_for_float_depth(color)

    return (
        make_tensor_image(color_float, o3d.core.Dtype.Float32, device),
        make_tensor_image(depth.astype(np.float32, copy=False), o3d.core.Dtype.Float32, device),
    )


def make_color_tsdf_vbg(integration_config, device: o3d.core.Device) -> o3d.t.geometry.VoxelBlockGrid:
    return o3d.t.geometry.VoxelBlockGrid(
        attr_names=("tsdf", "weight", "color"),
        attr_dtypes=(o3d.core.float32, o3d.core.float32, o3d.core.float32),
        attr_channels=((1), (1), (3)),
        voxel_size=integration_config.voxel_size,
        block_resolution=integration_config.block_resolution,
        block_count=integration_config.block_count,
        device=device,
    )


def filter_block_coordinates_by_aabb(
    block_coords: o3d.core.Tensor,
    *,
    voxel_size: float,
    block_resolution: int,
    min_bound: np.ndarray,
    max_bound: np.ndarray,
) -> o3d.core.Tensor:
    coords = block_coords.cpu().numpy()
    if coords.size == 0:
        return block_coords

    block_size = float(voxel_size) * int(block_resolution)
    block_min = coords.astype(np.float64) * block_size
    block_max = block_min + block_size
    keep = np.all(block_max >= min_bound, axis=1) & np.all(block_min <= max_bound, axis=1)
    if np.all(keep):
        return block_coords
    return o3d.core.Tensor(coords[keep], dtype=block_coords.dtype, device=block_coords.device)


def integrate_rgbd_frame(
    vbg: o3d.t.geometry.VoxelBlockGrid,
    color: o3d.t.geometry.Image,
    depth: o3d.t.geometry.Image,
    intrinsic: o3d.core.Tensor,
    extrinsic: o3d.core.Tensor,
    depth_max: float,
    trunc_voxel_multiplier: float,
    *,
    voxel_size: float | None = None,
    block_resolution: int | None = None,
    block_min_bound: np.ndarray | None = None,
    block_max_bound: np.ndarray | None = None,
) -> int:
    block_coords = vbg.compute_unique_block_coordinates(
        depth=depth,
        intrinsic=intrinsic,
        extrinsic=extrinsic,
        depth_scale=1.0,
        depth_max=float(depth_max),
        trunc_voxel_multiplier=float(trunc_voxel_multiplier),
    )

    if block_min_bound is not None and block_max_bound is not None:
        if voxel_size is None or block_resolution is None:
            raise ValueError("voxel_size and block_resolution are required when filtering block coordinates")
        block_coords = filter_block_coordinates_by_aabb(
            block_coords,
            voxel_size=voxel_size,
            block_resolution=block_resolution,
            min_bound=block_min_bound,
            max_bound=block_max_bound,
        )

    block_count = int(block_coords.shape[0])
    if block_count == 0:
        return 0

    try:
        vbg.integrate(
            block_coords=block_coords,
            depth=depth,
            color=color,
            depth_intrinsic=intrinsic,
            color_intrinsic=intrinsic,
            extrinsic=extrinsic,
            depth_scale=1.0,
            depth_max=float(depth_max),
            trunc_voxel_multiplier=float(trunc_voxel_multiplier),
        )
    except TypeError:
        vbg.integrate(
            block_coords,
            depth,
            color,
            intrinsic,
            intrinsic,
            extrinsic,
            1.0,
            float(depth_max),
            float(trunc_voxel_multiplier),
        )
    return block_count
