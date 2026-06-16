from pathlib import Path
import shutil

import numpy as np
from tqdm import tqdm

from mq3drecon.dataio.data_io import DataIO
from mq3drecon.layouts import ColmapExportLayout
from mq3drecon.models.camera_dataset import CameraDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem, Transforms
from mq3drecon.third_party.colmap.read_and_write_model import Camera, Image, Point3D, write_model


def load_colmap_dataset_map(
    data_io: DataIO,
    use_optimized_color_dataset: bool = True,
) -> dict[Side, CameraDataset]:
    dataset_map: dict[Side, CameraDataset] = {}

    if use_optimized_color_dataset:
        for side in Side:
            dataset = data_io.color.load_optimized_color_dataset(side=side)
            if dataset is not None:
                dataset_map[side] = dataset

        if len(dataset_map) == 0:
            print("[Warning] Optimized color datasets not found. Falling back to original color datasets.")

    if len(dataset_map) == 0:
        for side in Side:
            dataset_map[side] = data_io.color.load_color_dataset(side=side)

    return dataset_map


def read_colmap_cameras_and_images(
    data_io: DataIO,
    dataset_map: dict[Side, CameraDataset],
    image_output_dir: Path,
    interval: int = 1,
) -> tuple[dict[int, Camera], dict[int, Image]]:
    if interval < 1:
        raise ValueError("interval must be greater than or equal to 1")

    cameras: dict[int, Camera] = {}
    images: dict[int, Image] = {}

    camera_id = 0
    image_id = 0

    for side, dataset in dataset_map.items():
        print(f"[{side.name}] Exporting images and camera data ...")

        sampled_dataset = dataset[::interval]
        transforms = sampled_dataset.transforms.convert_coordinate_system(
            target_coordinate_system=CoordinateSystem.COLMAP,
            is_camera=True,
        )
        positions = transforms.positions_cw
        rotations = transforms.rotations_cw[:, [3, 0, 1, 2]]

        camera = Camera(
            id=camera_id,
            model="PINHOLE",
            width=sampled_dataset.widths[0],
            height=sampled_dataset.heights[0],
            params=np.array([
                sampled_dataset.fx[0],
                sampled_dataset.fy[0],
                sampled_dataset.cx[0],
                sampled_dataset.cy[0],
            ]),
        )
        cameras[camera_id] = camera

        for i in tqdm(range(len(sampled_dataset)), desc=f"[{side.name}] Copying images", unit="img"):
            timestamp = sampled_dataset.timestamps[i]
            dst_filename = f"{side.name}_{timestamp}.png"

            src_path = data_io.path_config.image.get_rgb_file_path(side=side, timestamp=timestamp)
            dst_path = image_output_dir / dst_filename

            try:
                shutil.copy2(src=src_path, dst=dst_path)
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"RGB image not found at path: {src_path}") from exc

            image = Image(
                id=image_id,
                qvec=rotations[i],
                tvec=positions[i],
                camera_id=camera_id,
                name=dst_filename,
                xys=np.empty((0, 2)),
                point3D_ids=np.empty((0,)),
            )

            images[image_id] = image
            image_id += 1

        camera_id += 1

    return cameras, images


def read_colmap_points_3d(data_io: DataIO) -> dict[int, Point3D]:
    print("[Info] Reading colored point cloud ...")

    pcd = data_io.reconstruction.load_colored_pcd()
    if pcd is None:
        raise FileNotFoundError("Colored point cloud not found. Please ensure it has been generated before export.")

    print("[Info] Finished reading colored point cloud.")

    positions = pcd.point.positions.numpy()
    colors = pcd.point.colors.numpy()

    positions = Transforms(
        coordinate_system=CoordinateSystem.OPEN3D,
        positions=positions,
        rotations=np.empty(()),
    ).convert_coordinate_system(
        target_coordinate_system=CoordinateSystem.COLMAP,
        is_camera=False,
        skip_rotation=True,
    ).positions

    points3d: dict[int, Point3D] = {}
    for point3d_id, (position, color) in enumerate(
        tqdm(zip(positions, colors), desc="[Info] Creating 3D points", unit="pt", total=len(positions))
    ):
        points3d[point3d_id] = Point3D(
            id=point3d_id,
            xyz=position,
            rgb=color,
            error=0.0,
            image_ids=np.array([], dtype=np.int64),
            point2D_idxs=np.array([], dtype=np.int64),
        )

    return points3d


def export_colmap_project(
    project_dir: Path,
    output_dir: Path,
    use_colored_pointcloud: bool = False,
    use_optimized_color_dataset: bool = False,
    interval: int = 1,
) -> None:
    if interval < 1:
        raise ValueError("interval must be greater than or equal to 1")

    project_dir = Path(project_dir)
    layout = ColmapExportLayout(output_dir=output_dir)

    if not project_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {project_dir}")

    layout.ensure_directories()
    model_dir = layout.get_model_dir()
    image_output_dir = layout.get_image_dir()

    data_io = DataIO(project_dir=project_dir)
    dataset_map = load_colmap_dataset_map(
        data_io=data_io,
        use_optimized_color_dataset=use_optimized_color_dataset,
    )

    cameras, images = read_colmap_cameras_and_images(
        data_io=data_io,
        dataset_map=dataset_map,
        image_output_dir=image_output_dir,
        interval=interval,
    )

    if use_colored_pointcloud:
        points3d = read_colmap_points_3d(data_io=data_io)
    else:
        points3d = {}

    write_model(
        cameras=cameras,
        images=images,
        points3D=points3d,
        path=model_dir,
        ext=".bin",
    )
