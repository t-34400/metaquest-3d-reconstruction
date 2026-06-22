from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import open3d as o3d
from tqdm import tqdm

from mq3drecon.config.reconstruction_config import ReconstructionConfig
from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.camera_dataset import CameraDataset, DepthDataset
from mq3drecon.processing.reconstruction.adapters.open3d_adapter import to_open3d_device
from mq3drecon.processing.reconstruction.rgbd_integration_common import (
    integrate_rgbd_frame,
    load_rgbd_images,
    make_color_tsdf_vbg,
)
from mq3drecon.processing.reconstruction.utils.mesh_extraction import extract_triangle_mesh_with_cpu_fallback
from mq3drecon.processing.reconstruction.utils.o3d_utils import compute_o3d_intrinsic_matrices


@dataclass(frozen=True)
class TileBounds:
    index: tuple[int, int, int]
    min_bound: np.ndarray
    max_bound: np.ndarray
    expanded_min_bound: np.ndarray
    expanded_max_bound: np.ndarray


def _compute_scene_bounds(depth_dataset: DepthDataset, depth_max: float) -> tuple[np.ndarray, np.ndarray]:
    positions = depth_dataset.transforms.positions_wc.astype(np.float64)
    if positions.size == 0:
        raise ValueError("Cannot build tiled TSDF plan from an empty depth dataset")
    margin = float(depth_max)
    return positions.min(axis=0) - margin, positions.max(axis=0) + margin


def _iter_tiles(
    *,
    scene_min: np.ndarray,
    scene_max: np.ndarray,
    tile_size_m: float,
    tile_overlap_m: float,
) -> list[TileBounds]:
    extent = np.maximum(scene_max - scene_min, tile_size_m)
    counts = np.maximum(np.ceil(extent / tile_size_m).astype(int), 1)
    tiles: list[TileBounds] = []
    for ix in range(int(counts[0])):
        for iy in range(int(counts[1])):
            for iz in range(int(counts[2])):
                index = np.array([ix, iy, iz], dtype=np.float64)
                min_bound = scene_min + index * tile_size_m
                max_bound = np.minimum(min_bound + tile_size_m, scene_max)
                tiles.append(
                    TileBounds(
                        index=(ix, iy, iz),
                        min_bound=min_bound,
                        max_bound=max_bound,
                        expanded_min_bound=min_bound - tile_overlap_m,
                        expanded_max_bound=max_bound + tile_overlap_m,
                    )
                )
    return tiles


def _select_candidate_frames(depth_dataset: DepthDataset, tile: TileBounds, depth_max: float) -> list[int]:
    positions = depth_dataset.transforms.positions_wc.astype(np.float64)
    expanded_min = tile.expanded_min_bound - float(depth_max)
    expanded_max = tile.expanded_max_bound + float(depth_max)
    mask = np.all(positions >= expanded_min, axis=1) & np.all(positions <= expanded_max, axis=1)
    return [int(index) for index in np.flatnonzero(mask)]


def _crop_legacy_mesh_to_aabb(mesh: o3d.geometry.TriangleMesh, tile: TileBounds) -> o3d.geometry.TriangleMesh:
    aabb = o3d.geometry.AxisAlignedBoundingBox(
        min_bound=tile.min_bound.astype(float),
        max_bound=tile.max_bound.astype(float),
    )
    cropped = mesh.crop(aabb)
    cropped.remove_duplicated_vertices()
    cropped.remove_duplicated_triangles()
    cropped.remove_degenerate_triangles()
    cropped.remove_unreferenced_vertices()
    return cropped


def _postprocess_legacy_mesh(mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
    mesh.remove_duplicated_vertices()
    mesh.remove_duplicated_triangles()
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()
    mesh.compute_vertex_normals()
    return mesh


def _save_tile_mesh(mesh: o3d.geometry.TriangleMesh, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    o3d.io.write_triangle_mesh(str(path), mesh)


def reconstruct_tiled_rgbd_scene(
    *,
    data_io: DataIO,
    config: ReconstructionConfig,
    color_dataset: CameraDataset,
    depth_dataset: DepthDataset,
    depth_kind: str,
) -> None:
    integration_config = config.depth_integration
    if config.depth_source != "rectified_stereo":
        raise ValueError("Tiled TSDF integration is currently supported only for rectified_stereo reconstruction")

    device = to_open3d_device(integration_config.device)
    tile_size_m = float(integration_config.voxel_size) * int(integration_config.tile_size_voxels)
    tile_overlap_m = float(integration_config.voxel_size) * int(integration_config.tile_overlap_voxels)
    if tile_size_m <= 0:
        raise ValueError("depth_integration.tile_size_voxels must produce a positive tile size")
    if tile_overlap_m < 0:
        raise ValueError("depth_integration.tile_overlap_voxels must be non-negative")

    scene_min, scene_max = _compute_scene_bounds(depth_dataset, integration_config.depth_max)
    tiles = _iter_tiles(
        scene_min=scene_min,
        scene_max=scene_max,
        tile_size_m=tile_size_m,
        tile_overlap_m=tile_overlap_m,
    )
    print(
        "[Info] Tiled TSDF integration: "
        f"voxel_size={integration_config.voxel_size}, tile_size_m={tile_size_m:.4f}, "
        f"tile_overlap_m={tile_overlap_m:.4f}, tile_count={len(tiles)}"
    )

    intrinsic_matrices = compute_o3d_intrinsic_matrices(dataset=depth_dataset)
    extrinsic_wc = depth_dataset.transforms.extrinsics_wc
    merged_mesh = o3d.geometry.TriangleMesh()
    non_empty_tile_count = 0
    skipped_tile_count = 0

    tile_dir = data_io.reconstruction.reconstruction_path_config.get_tiled_tsdf_mesh_dir()
    tile_dir.mkdir(parents=True, exist_ok=True)

    for tile in tqdm(tiles, desc="[LEFT] Integrating tiled stereo RGBD frames ..."):
        candidate_indices = _select_candidate_frames(depth_dataset, tile, integration_config.depth_max)
        if not candidate_indices:
            skipped_tile_count += 1
            continue

        vbg = make_color_tsdf_vbg(integration_config=integration_config, device=device)
        integrated_frame_count = 0
        integrated_block_count = 0
        for frame_index in candidate_indices:
            color, depth = load_rgbd_images(
                data_io=data_io,
                color_dataset=color_dataset,
                depth_dataset=depth_dataset,
                index=frame_index,
                device=device,
                depth_kind=depth_kind,
            )
            intrinsic = o3d.core.Tensor(intrinsic_matrices[frame_index], dtype=o3d.core.Dtype.Float64)
            extrinsic = o3d.core.Tensor(extrinsic_wc[frame_index], dtype=o3d.core.Dtype.Float64)
            block_count = integrate_rgbd_frame(
                vbg=vbg,
                color=color,
                depth=depth,
                intrinsic=intrinsic,
                extrinsic=extrinsic,
                depth_max=integration_config.depth_max,
                trunc_voxel_multiplier=integration_config.trunc_voxel_multiplier,
                voxel_size=integration_config.voxel_size,
                block_resolution=integration_config.block_resolution,
                block_min_bound=tile.expanded_min_bound,
                block_max_bound=tile.expanded_max_bound,
            )
            if block_count > 0:
                integrated_frame_count += 1
                integrated_block_count += block_count

        if integrated_block_count == 0:
            skipped_tile_count += 1
            continue

        tile_mesh = extract_triangle_mesh_with_cpu_fallback(vbg).to_legacy()
        tile_mesh = _crop_legacy_mesh_to_aabb(tile_mesh, tile)
        if len(tile_mesh.triangles) == 0:
            skipped_tile_count += 1
            continue

        tile_path = data_io.reconstruction.reconstruction_path_config.get_tiled_tsdf_mesh_path(*tile.index)
        _save_tile_mesh(tile_mesh, tile_path)
        merged_mesh += tile_mesh
        non_empty_tile_count += 1
        print(
            "[Info] Tiled TSDF tile "
            f"{tile.index}: candidates={len(candidate_indices)}, integrated_frames={integrated_frame_count}, "
            f"blocks={integrated_block_count}, triangles={len(tile_mesh.triangles)}"
        )

    if non_empty_tile_count == 0:
        raise RuntimeError("Tiled TSDF integration produced no non-empty tile meshes")

    merged_mesh = _postprocess_legacy_mesh(merged_mesh)
    data_io.reconstruction.save_colored_mesh_legacy(mesh=merged_mesh)
    print(
        "[Info] Tiled TSDF merge complete: "
        f"non_empty_tiles={non_empty_tile_count}, skipped_tiles={skipped_tile_count}, "
        f"vertices={len(merged_mesh.vertices)}, triangles={len(merged_mesh.triangles)}"
    )

    if config.visualize_colored_mesh:
        print("[Info] Visualizing colored mesh ...")
        axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.6, origin=[0, 0, 0])
        o3d.visualization.draw_geometries([merged_mesh, axis], window_name="Colored Mesh")  # type: ignore

    if config.sample_point_cloud_from_colored_mesh:
        vertex_count = len(merged_mesh.vertices)
        num_sampled_points = int(vertex_count * config.points_per_vertex_ratio)
        if num_sampled_points > 0:
            pcd = merged_mesh.sample_points_uniformly(number_of_points=num_sampled_points)
            data_io.reconstruction.save_colored_pcd_legacy(pcd=pcd)
