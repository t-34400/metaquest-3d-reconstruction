from typing import Optional
import open3d as o3d
from tqdm import tqdm

from mq3drecon.config.reconstruction_config import ReconstructionConfig
from mq3drecon.processing.reconstruction.adapters.open3d_adapter import to_open3d_device
from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.camera_dataset import CameraDataset, DepthDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem
from mq3drecon.processing.reconstruction.color_map_optimization.optimize_color_pose import optimize_color_pose
from mq3drecon.processing.reconstruction.confidence_estimation.estimate_depth_confidences import estimate_depth_confidences
from mq3drecon.processing.reconstruction.depth_optimization.depth_pose_optimizer import DepthPoseOptimizer
from mq3drecon.processing.reconstruction.utils.log_utils import log_step
from mq3drecon.processing.reconstruction.utils.o3d_utils import integrate, raycast_in_color_view


def reconstruct_scene(data_io: DataIO, config: ReconstructionConfig):
    # Dataset generation
    if config.depth_source == "quest":
        if not config.use_dataset_cache:
            for side in Side:
                data_io.depth.load_depth_dataset(side=side, use_cache=False)
                data_io.color.load_color_dataset(side=side, use_cache=False)

        # Depth confidence estimation
        if config.estimate_depth_confidences:
            log_step("Estimate depth confidences")
            estimate_depth_confidences(
                depth_data_io=data_io.depth,
                config=config.confidence_estimation
            )

        # Depth pose optimization
        if config.optimize_depth_pose:
            optimizer = DepthPoseOptimizer(
                depth_data_io=data_io.depth,
                recon_data_io=data_io.reconstruction,
                config=config
            )
            depth_dataset_map = optimizer()
        else:
            depth_dataset_map: dict[Side, DepthDataset] = {}
            for side in Side:
                dataset = data_io.depth.load_depth_dataset(
                    side=side,
                    use_cache=config.fragment_generation.use_dataset_cache
                )
                dataset.transforms = dataset.transforms.convert_coordinate_system(
                    target_coordinate_system=CoordinateSystem.OPEN3D,
                    is_camera=True
                )
                depth_dataset_map[side] = dataset
    else:
        if config.estimate_depth_confidences:
            print("[Info] Skipping Quest depth confidence estimation for color_aligned depth source.")
        if config.optimize_depth_pose:
            print("[Info] Skipping Quest depth pose optimization for color_aligned depth source.")

        depth_dataset_map = {}
        for side in Side:
            color_dataset = data_io.color.load_color_dataset(
                side=side,
                use_cache=config.use_dataset_cache
            )
            dataset = data_io.rgbd.build_color_aligned_depth_dataset(
                side=side,
                color_dataset=color_dataset,
            )
            dataset.transforms = dataset.transforms.convert_coordinate_system(
                target_coordinate_system=CoordinateSystem.OPEN3D,
                is_camera=True
            )
            depth_dataset_map[side] = dataset

    # TSDF integration
    vbg: Optional[o3d.t.geometry.VoxelBlockGrid] = None
    if config.use_colorless_vbg_cache:
        vbg = data_io.reconstruction.load_colorless_vbg()

    if vbg is None:
        log_step("Integrate depth maps")
        integration_config = config.depth_integration

        for side, dataset in depth_dataset_map.items():
            vbg = integrate(
                dataset=dataset, 
                depth_data_io=data_io.depth, 
                side=side, 
                use_confidence_filtered_depth=integration_config.use_confidence_filtered_depth,
                confidence_threshold=integration_config.confidence_threshold,
                valid_count_threshold=integration_config.valid_count_threshold,
                voxel_size=integration_config.voxel_size,
                block_resolution=integration_config.block_resolution,
                block_count=integration_config.block_count,
                depth_max=integration_config.depth_max,
                trunc_voxel_multiplier=integration_config.trunc_voxel_multiplier,
                device=to_open3d_device(integration_config.device),
                show_progress=True,
                desc=f"[{side.name}] Integrating depth maps ...",
                vbg_opt=vbg,
                depth_source=config.depth_source,
                rgbd_data_io=data_io.rgbd,
            )

    if vbg is None:
        print("[Error] Failed to generate VoxelBlockGrid. Please check the integration parameters and input data.")
        return

    data_io.reconstruction.save_colorless_vbg(vbg=vbg)

    if config.visualize_colorless_pcd:
        print("[Info] Visualizing colorless point cloud ...")

        pcds = [vbg.extract_point_cloud().to_legacy()]
        axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.6, origin=[0, 0, 0])
        o3d.visualization.draw_geometries(pcds + [axis], window_name="Colorless Point Cloud") # type: ignore        

    # Color map optimization
    optimized_color_dataset_map = None
    if config.optimize_color_pose:
        log_step("Optimize color maps")
        colored_mesh, optimized_color_dataset_map = optimize_color_pose(vbg=vbg, data_io=data_io, config=config.color_optimization)

        data_io.reconstruction.save_colored_mesh_legacy(mesh=colored_mesh)

        for side, optimized_dataset in optimized_color_dataset_map.items():
            data_io.color.save_optimized_color_dataset(dataset=optimized_dataset, side=side)

        if config.visualize_colored_mesh:
            print("[Info] Visualizing colored mesh ...")
            pcds = [colored_mesh]
            axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.6, origin=[0, 0, 0])
            o3d.visualization.draw_geometries(pcds + [axis], window_name="Colored Mesh") # type: ignore        

        if config.sample_point_cloud_from_colored_mesh:
            vertex_count = len(colored_mesh.vertices)
            num_sampled_points = int(vertex_count * config.points_per_vertex_ratio)

            pcd = colored_mesh.sample_points_uniformly(
                number_of_points=num_sampled_points,
            )

            data_io.reconstruction.save_colored_pcd_legacy(pcd=pcd)

    # Color aligned depth rendering
    if config.depth_source == "color_aligned" and config.render_color_aligned_depth:
        print("[Info] Skipping color-aligned depth rendering to avoid overwriting the selected depth source.")
    elif config.render_color_aligned_depth:
        log_step("Render color-aligned depth")

        mesh = vbg.extract_triangle_mesh(
            weight_threshold=config.color_aligned_depth_rendering.weight_threshold,
            estimated_vertex_number=config.color_aligned_depth_rendering.estimated_vertex_number
        )

        scene = o3d.t.geometry.RaycastingScene(device=to_open3d_device(config.device))
        scene.add_triangles(mesh.cpu())

        def render_color_aligned_depth_map(dataset: CameraDataset, desc: str = ''):
            depth_map_iter = raycast_in_color_view(scene=scene, dataset=dataset)

            for i in tqdm(range(len(dataset)), desc=desc):
                timestamp = dataset.timestamps[i]
                depth_map = next(depth_map_iter)

                data_io.rgbd.save_color_aligned_depth(depth_map=depth_map, side=side, timestamp=timestamp)

        for side in Side:
            color_dataset = data_io.color.load_color_dataset(side=side, use_cache=True)

            if optimized_color_dataset_map is not None:
                optimized_color_dataset = optimized_color_dataset_map[side]

                if not config.color_aligned_depth_rendering.only_use_optimized_dataset:
                    optimized_timestamps = set(optimized_color_dataset.timestamps)
                    filtered_color_dataset = color_dataset[
                        [i for i in range(len(color_dataset)) if color_dataset.timestamps[i] not in optimized_timestamps]
                    ]
                    render_color_aligned_depth_map(dataset=filtered_color_dataset, desc=f"[{side.name}] Rendering color aligned depth maps ...")

                render_color_aligned_depth_map(dataset=optimized_color_dataset, desc=f"[{side.name}] Rendering optimized-color aligned depth maps ...")
            else:
                if not config.color_aligned_depth_rendering.only_use_optimized_dataset:
                    render_color_aligned_depth_map(dataset=color_dataset, desc=f"[{side.name}] Rendering color aligned depth maps ...")
