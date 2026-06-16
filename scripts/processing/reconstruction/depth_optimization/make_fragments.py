from typing import Generator, Optional
import numpy as np
import open3d as o3d

from config.reconstruction_config import FragmentGenerationConfig, to_open3d_device
from dataio.depth_data_io import DepthDataIO
from models.camera_dataset import DepthDataset
from models.side import Side
from models.transforms import CoordinateSystem
from processing.reconstruction.utils.o3d_utils import compute_o3d_intrinsic_matrices, convert_pose_graph_to_transforms, convert_transforms_to_pose_graph, load_depth_map
from utils.paralell_utils import parallel_map


def frustum_overlap_filter(
    extrinsic_cw_1: np.ndarray,  # (4, 4)
    extrinsic_cw_2: np.ndarray,  # (4, 4)
    intrinsic_1: np.ndarray,     # (3, 3)
    intrinsic_2: np.ndarray,     # (3, 3)
    image_size_1: tuple[int, int],  # (width, height)
    image_size_2: tuple[int, int],
    z_near: float = 0.1,
    z_far: float = 3.0,
    overlap_ratio_threshold: float = 0.05
) -> bool:
    def pixel_to_ray(u, v, fx, fy, cx, cy):
        x = (u - cx) / fx
        y = (v - cy) / fy
        return np.array([x, y, 1.0])

    def get_frustum_points(extrinsic_cw, intrinsic, image_size, z_near, z_far):
        fx, fy = intrinsic[0, 0], intrinsic[1, 1]
        cx, cy = intrinsic[0, 2], intrinsic[1, 2]
        w, h = image_size

        uv_list = [
            (0, 0), (w-1, 0), (w-1, h-1), (0, h-1), (w//2, h//2)
        ]

        points = []
        for d in [z_near, z_far]:
            for u, v in uv_list:
                ray = pixel_to_ray(u, v, fx, fy, cx, cy)
                ray /= np.linalg.norm(ray)
                pt_cam = ray * d  # in camera coord
                pt_world = extrinsic_cw[:3, :3] @ pt_cam + extrinsic_cw[:3, 3]
                points.append(pt_world)

        return np.array(points)  # shape (10, 3)

    def compute_aabb_bounds(points):
        min_pt = points.min(axis=0)
        max_pt = points.max(axis=0)
        return min_pt, max_pt

    def intersect_aabb(min1, max1, min2, max2):
        overlap_min = np.maximum(min1, min2)
        overlap_max = np.minimum(max1, max2)
        overlap = np.maximum(overlap_max - overlap_min, 0.0)
        return overlap

    def volume(min_pt, max_pt):
        return np.prod(np.maximum(max_pt - min_pt, 0.0))

    # Compute frustum AABBs
    pts1 = get_frustum_points(extrinsic_cw_1, intrinsic_1, image_size_1, z_near, z_far)
    pts2 = get_frustum_points(extrinsic_cw_2, intrinsic_2, image_size_2, z_near, z_far)

    min1, max1 = compute_aabb_bounds(pts1)
    min2, max2 = compute_aabb_bounds(pts2)

    inter_size = intersect_aabb(min1, max1, min2, max2)
    inter_vol = np.prod(inter_size)

    vol1 = volume(min1, max1)
    vol2 = volume(min2, max2)

    if inter_vol == 0.0:
        return False

    overlap_ratio = inter_vol / min(vol1, vol2)
    return overlap_ratio > overlap_ratio_threshold


def build_pose_graph_for_fragment(
    frag_dataset: DepthDataset,
    depth_data_io: DepthDataIO,
    side: Side,
    config: FragmentGenerationConfig,
) -> o3d.pipelines.registration.PoseGraph:
    N = len(frag_dataset.timestamps)
    intrinsic_matrix = compute_o3d_intrinsic_matrices(dataset=frag_dataset)[0]

    intrinsic_tensor = o3d.core.Tensor(
        intrinsic_matrix,
        dtype=o3d.core.Dtype.Float64,
        device=o3d.core.Device("CPU:0")  # Must be on CPU
    )

    transforms = frag_dataset.transforms
    extrinsics_wc = transforms.extrinsics_wc
    extrinsics_cw = transforms.extrinsics_cw

    pose_graph = convert_transforms_to_pose_graph(transforms=transforms)

    # odometry
    depth_curr = load_depth_map(
        depth_data_io=depth_data_io,
        side=side,
        index=0,
        dataset=frag_dataset,
        device=to_open3d_device(config.device),
        use_confidence_filtered_depth=config.use_confidence_filtered_depth,
        confidence_threshold=config.confidence_threshold,
        valid_count_threshold=config.valid_count_threshold,
    )
    extrinsic_curr_cw = extrinsics_cw[0]

    for i in range(0, N - 1):
        depth_next =  load_depth_map(
            depth_data_io=depth_data_io,
            side=side,
            index=i + 1,
            dataset=frag_dataset,
            device=to_open3d_device(config.device),
            use_confidence_filtered_depth=config.use_confidence_filtered_depth,
            confidence_threshold=config.confidence_threshold,
            valid_count_threshold=config.valid_count_threshold,
        )
        extrinsic_next_wc = extrinsics_wc[i + 1]

        if depth_curr is not None and depth_next is not None:
            relative_pose = extrinsic_next_wc @ extrinsic_curr_cw

            relative_pose_tensor = o3d.core.Tensor(
                relative_pose,
                dtype=o3d.core.Dtype.Float64,
                device=o3d.core.Device("CPU:0")  # Must be on CPU
            )
            
            # Note: This function requires intrinsic/extrinsic tensors to be on the CPU,
            # even if the depth tensor is on the GPU.
            info = o3d.t.pipelines.odometry.compute_odometry_information_matrix(
                source_depth=depth_curr,
                target_depth=depth_next,
                intrinsic=intrinsic_tensor,
                source_to_target=relative_pose_tensor,
                dist_threshold=config.dist_threshold,
                depth_scale=1.0,
                depth_max=config.depth_max,
            )

            edge = o3d.pipelines.registration.PoseGraphEdge(
                    source_node_id=i,
                    target_node_id=i + 1,
                    transformation=relative_pose,
                    information=info.cpu().numpy(),
                    uncertain=False,
                    confidence=1.0
                )
            pose_graph.edges.append(edge)

        depth_curr = depth_next
        extrinsic_curr_cw = extrinsics_cw[i + 1]

    # loop closure
    key_indices = list(range(0, N, config.odometry_loop_interval))
    N_key_frames = len(key_indices)

    for i in range(N_key_frames):
        key_i = key_indices[i]
        width = frag_dataset.widths[i]
        height = frag_dataset.heights[i]

        depth_curr = load_depth_map(
            depth_data_io=depth_data_io, 
            side=side, 
            index=key_i, 
            dataset=frag_dataset, 
            device=to_open3d_device(config.device),
            use_confidence_filtered_depth=config.use_confidence_filtered_depth,
            confidence_threshold=config.confidence_threshold,
            valid_count_threshold=config.valid_count_threshold,
        )
        extrinsic_curr_cw = extrinsics_cw[key_i]

        if depth_curr is None:
            continue

        for j in range(i + 1, N_key_frames):
            key_j = key_indices[j]
            depth_next = load_depth_map(
                depth_data_io=depth_data_io, 
                side=side, 
                index=key_j, 
                dataset=frag_dataset, 
                device=to_open3d_device(config.device),
                use_confidence_filtered_depth=config.use_confidence_filtered_depth,
                confidence_threshold=config.confidence_threshold,
                valid_count_threshold=config.valid_count_threshold,
            )
            extrinsic_next_cw = extrinsics_cw[key_j]
            extrinsic_next_wc = extrinsics_wc[key_j]

            if depth_next is None:
                continue

            relative_pose = extrinsic_next_wc @ extrinsic_curr_cw
            relative_pose_tensor = o3d.core.Tensor(
                relative_pose, 
                dtype=o3d.core.Dtype.Float64, 
                device=o3d.core.Device("CPU:0")  # Must be on CPU
            )

            if not frustum_overlap_filter(
                extrinsic_cw_1=extrinsic_curr_cw, 
                extrinsic_cw_2=extrinsic_next_cw,
                intrinsic_1=intrinsic_matrix, 
                intrinsic_2=intrinsic_matrix,
                image_size_1=(width, height), 
                image_size_2=(width, height),
                z_near=0.1, z_far=config.depth_max, 
                overlap_ratio_threshold=config.overlap_ratio_threshold,
            ):
                continue

            # Note: This function requires intrinsic/extrinsic tensors to be on the CPU,
            # even if the depth tensor is on the GPU.
            info = o3d.t.pipelines.odometry.compute_odometry_information_matrix(
                source_depth=depth_curr, target_depth=depth_next, intrinsic=intrinsic_tensor,
                source_to_target=relative_pose_tensor, dist_threshold=config.dist_threshold,
                depth_scale=1.0, depth_max=config.depth_max,
            )

            if info[5, 5] / (width * height) > config.loop_yaw_info_density_threshold:
                edge = o3d.pipelines.registration.PoseGraphEdge(
                    source_node_id=key_i, target_node_id=key_j,
                    transformation=relative_pose, information=info.cpu().numpy(),
                    uncertain=True, confidence=1.0
                )
                pose_graph.edges.append(edge)

    return pose_graph


def optimize_dataset_pose(
    depth_data_io: DepthDataIO,
    frag_dataset: DepthDataset,
    side: Side,
    config: FragmentGenerationConfig,
):
    pose_graph = build_pose_graph_for_fragment(
        frag_dataset=frag_dataset, 
        depth_data_io=depth_data_io, 
        side=side, 
        config=config
    )

    # PoseGraph Optimization
    option = o3d.pipelines.registration.GlobalOptimizationOption(
        max_correspondence_distance=config.dist_threshold, 
        edge_prune_threshold=config.edge_prune_threshold, 
        reference_node=0
    )
    o3d.pipelines.registration.global_optimization(
        pose_graph, 
        o3d.pipelines.registration.GlobalOptimizationLevenbergMarquardt(),
        o3d.pipelines.registration.GlobalOptimizationConvergenceCriteria(), 
        option
    )

    frag_dataset.transforms = convert_pose_graph_to_transforms(pose_graph=pose_graph) 


def make_fragment_datasets(
    depth_data_io: DepthDataIO,
    config: FragmentGenerationConfig,
) -> dict[Side, list[DepthDataset]]:
    fragment_dataset_map: dict[Side, list[DepthDataset]] = {}
    
    for side in Side:
        fragments = []
        fragment_dataset_map[side] = fragments

        depth_dataset = depth_data_io.load_depth_dataset(side=side, use_cache=config.use_dataset_cache)
        depth_dataset.transforms = depth_dataset.transforms.convert_coordinate_system(
            target_coordinate_system=CoordinateSystem.OPEN3D,
            is_camera=True
        )

        frag_datasets = depth_dataset.split(fragment_size=config.fragment_size)
        fragment_dataset_map[side] = frag_datasets

        args_list = [
            (depth_data_io, frag_dataset, side, config)
            for frag_dataset in frag_datasets
        ]
        parallel_map(
            func=optimize_dataset_pose,
            args_list=args_list,
            max_workers=None,
            use_multiprocessing=config.use_multi_threading,
            context="spawn",
            default_on_error=None,
            show_progress=True,
            desc=f"[{side.name}] Optimizing Depth Camera Pose for fragments..."
        )

    return fragment_dataset_map