from typing import Generator, Optional, cast
import numpy as np
import open3d as o3d
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm

from mq3drecon.dataio.depth_data_io import DepthDataIO
from mq3drecon.dataio.rgbd_data_io import RGBDDataIO
from mq3drecon.models.camera_dataset import CameraDataset, DepthDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem, Transforms


def compute_o3d_intrinsic_matrices(dataset: CameraDataset) -> np.ndarray:
    widths = dataset.widths
    intrinsic_matrices = dataset.get_intrinsic_matrices()
    intrinsic_matrices[:, 0, 2] = widths - intrinsic_matrices[:, 0, 2]

    return intrinsic_matrices


def convert_transforms_to_pose_graph(transforms: Transforms) -> o3d.pipelines.registration.PoseGraph:
    pose_graph = o3d.pipelines.registration.PoseGraph()

    extrinsics_cw = transforms.extrinsics_cw
    N = len(extrinsics_cw)

    for i in range(N):
        pose_graph.nodes.append(
            o3d.pipelines.registration.PoseGraphNode(
                pose=extrinsics_cw[i]
            )
        )
    
    return pose_graph


def convert_dataset_to_trajectory(dataset: CameraDataset) -> o3d.camera.PinholeCameraTrajectory:
    param_list = []

    intrinsic_matrices = compute_o3d_intrinsic_matrices(dataset=dataset)
    extrinsic_matrices = dataset.transforms.convert_coordinate_system(
        target_coordinate_system=CoordinateSystem.OPEN3D,
        is_camera=True
    ).extrinsics_wc

    for i in range(len(dataset)):
        params = o3d.camera.PinholeCameraParameters()

        width = dataset.widths[i]
        height = dataset.heights[i]
        K = intrinsic_matrices[i]
        fx = K[0, 0]
        fy = K[1, 1]
        cx = K[0, 2]
        cy = K[1, 2]

        intrinsic = o3d.camera.PinholeCameraIntrinsic()
        intrinsic.set_intrinsics(
            width=width,
            height=height,
            fx=fx,
            fy=fy,
            cx=cx,
            cy=cy
        )

        params.intrinsic = intrinsic
        params.extrinsic = extrinsic_matrices[i]

        param_list.append(params)

    trajectory = o3d.camera.PinholeCameraTrajectory()
    trajectory.parameters = param_list

    return trajectory


def convert_trajectory_to_transforms(trajectory: o3d.camera.PinholeCameraTrajectory) -> Transforms:
    positions = []
    rotations = []

    for params in trajectory.parameters:
        pose = np.linalg.inv(params.extrinsic)

        position = pose[:3, 3]
        rotation = R.from_matrix(pose[:3, :3]).as_quat()

        positions.append(position)
        rotations.append(rotation)

    return Transforms(
        coordinate_system=CoordinateSystem.OPEN3D,
        positions=np.array(positions),
        rotations=np.array(rotations)
    )


def convert_pose_graph_to_transforms(pose_graph: o3d.pipelines.registration.PoseGraph) -> Transforms:
    pose = np.array([node.pose for node in pose_graph.nodes])

    return Transforms(
        coordinate_system=CoordinateSystem.OPEN3D,
        positions=pose[:, :3, 3],
        rotations=R.from_matrix(pose[:, :3, :3]).as_quat(),
    )


def load_depth_map(
    depth_data_io: DepthDataIO,
    side: Side,
    index: int,
    dataset: DepthDataset,
    device: o3d.core.Device,
    use_confidence_filtered_depth: bool,
    confidence_threshold: float,
    valid_count_threshold: int,
    depth_source: str = "quest",
    rgbd_data_io: RGBDDataIO | None = None,
) -> Optional[o3d.t.geometry.Image]:
    if depth_source == "color_aligned":
        if rgbd_data_io is None:
            raise ValueError("rgbd_data_io is required when depth_source is color_aligned")
        depth_np = rgbd_data_io.load_color_aligned_depth_by_index(
            side=side,
            dataset=dataset,
            index=index,
        )
    else:
        depth_np = depth_data_io.load_depth_map(
            side=side,
            timestamp=dataset.timestamps[index],
            width=dataset.widths[index],
            height=dataset.heights[index],
            near=dataset.nears[index],
            far=dataset.fars[index],
        )

    if depth_np is None:
        return None

    if use_confidence_filtered_depth and depth_source != "color_aligned":
        confidence_map = depth_data_io.load_confidence_map(
            side=side,
            timestamp=dataset.timestamps[index]
        )

        if confidence_map is None:
            print(f"[Warning] Confidence map not found for timestamp {dataset.timestamps[index]}")
        else:
            depth_np[confidence_map.confidence_map < confidence_threshold] = 0.0
            depth_np[confidence_map.valid_count < valid_count_threshold] = 0.0

    return o3d.t.geometry.Image(
        tensor=o3d.core.Tensor(
            depth_np,
            dtype=o3d.core.Dtype.Float32,
            device=device
        )
    )


def integrate(
    dataset: DepthDataset,
    depth_data_io: DepthDataIO,
    side: Side,
    use_confidence_filtered_depth: bool,
    confidence_threshold: float,
    valid_count_threshold: int,
    voxel_size: float,
    block_resolution: int,
    block_count: int,
    depth_max: float,
    trunc_voxel_multiplier: float,
    device: o3d.core.Device,
    show_progress: bool = False,
    desc: Optional[str] = None,
    vbg_opt: Optional[o3d.t.geometry.VoxelBlockGrid] = None,
    depth_source: str = "quest",
    rgbd_data_io: RGBDDataIO | None = None,
) -> o3d.t.geometry.VoxelBlockGrid:
    if vbg_opt is None:
        vbg = o3d.t.geometry.VoxelBlockGrid(
            attr_names=('tsdf', 'weight'),
            attr_dtypes=(o3d.core.float32, o3d.core.float32),
            attr_channels=((1), (1)),
            voxel_size=voxel_size,
            block_resolution=block_resolution,
            block_count=block_count,
            device=device,
        )
    else:
        vbg = vbg_opt

    N = len(dataset.timestamps)

    extrinsic_wc = dataset.transforms.extrinsics_wc
    intrinsic_matrices = compute_o3d_intrinsic_matrices(dataset=dataset)

    def integrate(index: int):
        depth_map = load_depth_map(
            depth_data_io=depth_data_io,
            side=side,
            index=index,
            dataset=dataset,
            device=device,
            use_confidence_filtered_depth=use_confidence_filtered_depth,
            confidence_threshold=confidence_threshold,
            valid_count_threshold=valid_count_threshold,
            depth_source=depth_source,
            rgbd_data_io=rgbd_data_io,
        )

        if depth_map is None:
            return

        intrinsic = o3d.core.Tensor(
            intrinsic_matrices[index],
            dtype=o3d.core.Dtype.Float64
        )
        extrinsic = o3d.core.Tensor(
            extrinsic_wc[index],
            dtype=o3d.core.Dtype.Float64
        )

        frustum_block_coords = vbg.compute_unique_block_coordinates(
            depth=depth_map,
            intrinsic=intrinsic,
            extrinsic=extrinsic,
            depth_scale=1.0,
            depth_max=float(depth_max),
            trunc_voxel_multiplier=float(trunc_voxel_multiplier),
        )

        vbg.integrate(
            block_coords=frustum_block_coords,
            depth=depth_map,
            intrinsic=intrinsic,
            extrinsic=extrinsic,
            depth_scale=1.0,
            depth_max=float(depth_max),
            trunc_voxel_multiplier=float(trunc_voxel_multiplier),
        )

    if show_progress:
        for index in tqdm(range(N), desc=desc):
            integrate(index)
    else:
        for index in range(N):
            integrate(index)

    return vbg


def raycast_in_color_view(
    scene: o3d.t.geometry.RaycastingScene,
    dataset: CameraDataset
) -> Generator[np.ndarray, None, None]:
    intrinsic_matrices = compute_o3d_intrinsic_matrices(dataset=dataset)
    extrinsic_matrices = dataset.transforms.extrinsics_wc

    for i in range(len(dataset)):
        intrinsic = o3d.core.Tensor(intrinsic_matrices[i], dtype=o3d.core.Dtype.Float32)
        extrinsic = o3d.core.Tensor(extrinsic_matrices[i], dtype=o3d.core.Dtype.Float32)
        width = dataset.widths[i]
        height = dataset.heights[i]

        rays = scene.create_rays_pinhole(intrinsic, extrinsic, width_px=width, height_px=height)
        result = scene.cast_rays(rays)

        depth = result['t_hit'].cpu().numpy()

        yield depth