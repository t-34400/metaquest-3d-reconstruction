from __future__ import annotations

import open3d as o3d
from tqdm import tqdm

from mq3drecon.config.reconstruction_config import ReconstructionConfig
from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem
from mq3drecon.processing.reconstruction.adapters.open3d_adapter import to_open3d_device
from mq3drecon.processing.reconstruction.rgbd_integration_common import (
    integrate_rgbd_frame,
    load_rgbd_images,
    make_color_tsdf_vbg,
)
from mq3drecon.processing.reconstruction.tiled_rgbd_integration import reconstruct_tiled_rgbd_scene
from mq3drecon.processing.reconstruction.utils.mesh_extraction import extract_triangle_mesh_with_cpu_fallback
from mq3drecon.processing.reconstruction.utils.o3d_utils import compute_o3d_intrinsic_matrices


def reconstruct_color_aligned_rgbd_scene(data_io: DataIO, config: ReconstructionConfig) -> None:
    if config.estimate_depth_confidences:
        print("[Info] Skipping Quest depth confidence estimation for stereo-generated depth source.")
    if config.optimize_depth_pose:
        print("[Info] Skipping Quest depth pose optimization for stereo-generated depth source.")
    if config.optimize_color_pose:
        print("[Info] Skipping color map optimization for stereo-generated depth source; integrating LEFT RGBD directly.")
    if config.render_color_aligned_depth:
        print("[Info] Skipping color-aligned depth rendering to avoid overwriting the selected depth source.")
    if config.use_colorless_vbg_cache:
        print("[Info] Ignoring colorless VBG cache for stereo-generated RGBD integration.")

    integration_config = config.depth_integration
    device = to_open3d_device(integration_config.device)

    depth_kind = "color_aligned"
    try:
        color_dataset, depth_dataset = data_io.rgbd.build_rectified_stereo_rgbd_datasets(side=Side.LEFT)
        depth_kind = "rectified_stereo"
        print("[Info] Using rectified stereo RGBD frames for stereo-generated depth source.")
    except FileNotFoundError:
        full_color_dataset = data_io.color.load_color_dataset(side=Side.LEFT, use_cache=config.use_dataset_cache)
        color_dataset, depth_dataset = data_io.rgbd.build_color_aligned_rgbd_datasets(
            side=Side.LEFT,
            color_dataset=full_color_dataset,
        )

    depth_dataset.transforms = depth_dataset.transforms.convert_coordinate_system(
        target_coordinate_system=CoordinateSystem.OPEN3D,
        is_camera=True,
    )
    color_dataset.transforms = depth_dataset.transforms


    if integration_config.mode == "tiled":
        reconstruct_tiled_rgbd_scene(
            data_io=data_io,
            config=config,
            color_dataset=color_dataset,
            depth_dataset=depth_dataset,
            depth_kind=depth_kind,
        )
        return

    vbg = make_color_tsdf_vbg(integration_config=integration_config, device=device)

    intrinsic_matrices = compute_o3d_intrinsic_matrices(dataset=depth_dataset)
    extrinsic_wc = depth_dataset.transforms.extrinsics_wc

    for index in tqdm(range(len(depth_dataset)), desc="[LEFT] Integrating stereo-generated RGBD frames ..."):
        color, depth = load_rgbd_images(
            data_io=data_io,
            color_dataset=color_dataset,
            depth_dataset=depth_dataset,
            index=index,
            device=device,
            depth_kind=depth_kind,
        )
        intrinsic = o3d.core.Tensor(intrinsic_matrices[index], dtype=o3d.core.Dtype.Float64)
        extrinsic = o3d.core.Tensor(extrinsic_wc[index], dtype=o3d.core.Dtype.Float64)
        integrate_rgbd_frame(
            vbg=vbg,
            color=color,
            depth=depth,
            intrinsic=intrinsic,
            extrinsic=extrinsic,
            depth_max=integration_config.depth_max,
            trunc_voxel_multiplier=integration_config.trunc_voxel_multiplier,
        )

    mesh = extract_triangle_mesh_with_cpu_fallback(vbg)
    data_io.reconstruction.save_colored_mesh(mesh=mesh)

    legacy_mesh = None
    if config.visualize_colored_mesh:
        print("[Info] Visualizing colored mesh ...")
        legacy_mesh = mesh.to_legacy()
        axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.6, origin=[0, 0, 0])
        o3d.visualization.draw_geometries([legacy_mesh, axis], window_name="Colored Mesh")  # type: ignore

    if config.sample_point_cloud_from_colored_mesh:
        if legacy_mesh is None:
            legacy_mesh = mesh.to_legacy()
        vertex_count = len(legacy_mesh.vertices)
        num_sampled_points = int(vertex_count * config.points_per_vertex_ratio)
        pcd = legacy_mesh.sample_points_uniformly(number_of_points=num_sampled_points)
        data_io.reconstruction.save_colored_pcd_legacy(pcd=pcd)
