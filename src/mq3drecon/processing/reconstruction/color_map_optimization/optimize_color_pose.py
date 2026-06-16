import open3d as o3d

from mq3drecon.config.reconstruction_config import ColorOptimizationConfig
from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.camera_dataset import CameraDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem, Transforms
from mq3drecon.processing.reconstruction.utils.o3d_utils import convert_dataset_to_trajectory, convert_trajectory_to_transforms, raycast_in_color_view


def optimize_color_pose(
    vbg: o3d.t.geometry.VoxelBlockGrid,
    data_io: DataIO,
    config: ColorOptimizationConfig
) -> tuple[o3d.geometry.TriangleMesh, dict[Side, CameraDataset]]:
    mesh = vbg.extract_triangle_mesh(
        weight_threshold=config.weight_threshold,
        estimated_vertex_number=config.estimated_vertex_number
    )

    scene = o3d.t.geometry.RaycastingScene(device=config.device)
    scene.add_triangles(mesh.cpu())
    
    rgbd_images = []
    trajectory_params = []

    color_dataset_map: dict[Side, CameraDataset] = {}

    for side in Side:
        color_dataset = data_io.color.load_color_dataset(side=side, use_cache=config.use_dataset_cache)
        color_dataset = color_dataset[::config.interval]
        color_dataset_map[side] = color_dataset

        color_dataset.transforms = color_dataset.transforms.convert_coordinate_system(
            target_coordinate_system=CoordinateSystem.OPEN3D,
            is_camera=True
        )

        side_trajectory = convert_dataset_to_trajectory(color_dataset)
        trajectory_params.extend(side_trajectory.parameters)

        N = len(color_dataset.timestamps)

        depth_map_iter = raycast_in_color_view(scene=scene, dataset=color_dataset)

        for i in range(N):
            timestamp = color_dataset.timestamps[i]

            color_map = data_io.color.load_rgb(side=side, timestamp=timestamp)
            depth_map = next(depth_map_iter)

            color_map_o3d = o3d.geometry.Image(color_map)
            depth_map_o3d = o3d.geometry.Image(depth_map)

            rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
                color_map_o3d, depth_map_o3d, 
                depth_scale=1.0,
                convert_rgb_to_intensity=False
            )
            rgbd_images.append(rgbd_image)

    trajectory = o3d.camera.PinholeCameraTrajectory()
    trajectory.parameters = trajectory_params

    with o3d.utility.VerbosityContextManager(
        o3d.utility.VerbosityLevel.Debug) as _:
        colored_mesh, trajectory = o3d.pipelines.color_map.run_rigid_optimizer(
            mesh.cpu().to_legacy(), rgbd_images, trajectory,
            o3d.pipelines.color_map.RigidOptimizerOption(maximum_iteration=config.max_iteration)
        )

    trajectory_transforms = convert_trajectory_to_transforms(trajectory=trajectory)

    start_index = 0
    for side, color_dataset in color_dataset_map.items():
        end_index = start_index + len(color_dataset)
    
        color_dataset.transforms = Transforms(
            coordinate_system=trajectory_transforms.coordinate_system,
            positions=trajectory_transforms.positions[start_index:end_index],
            rotations=trajectory_transforms.rotations[start_index:end_index]
        )

        start_index = end_index

    return colored_mesh, color_dataset_map