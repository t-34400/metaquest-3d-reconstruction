"""Camera trajectory visualization helpers."""

from __future__ import annotations

from typing import Any

import numpy as np

from mq3drecon.dataio.data_io import DataIO
from mq3drecon.models.camera_dataset import CameraDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import CoordinateSystem


def get_camera_visualization_lines(
    dataset: CameraDataset,
    color: np.ndarray = np.array([1, 0, 0]),
    interval: int = 5,
    scale: float = 0.05,
) -> list[Any]:
    import open3d as o3d

    camera_lines = []
    widths = dataset.widths
    heights = dataset.heights
    intrinsics_matrices = dataset.get_intrinsic_matrices()
    intrinsics_matrices[:, 0, 2] = widths - intrinsics_matrices[:, 0, 2]
    extrinsics = dataset.transforms.convert_coordinate_system(
        target_coordinate_system=CoordinateSystem.OPEN3D,
        is_camera=True,
    ).extrinsics_wc

    for i in range(0, len(dataset.timestamps), interval):
        intrinsic = o3d.camera.PinholeCameraIntrinsic(
            width=widths[i],
            height=heights[i],
            fx=intrinsics_matrices[i][0, 0],
            fy=intrinsics_matrices[i][1, 1],
            cx=intrinsics_matrices[i][0, 2],
            cy=intrinsics_matrices[i][1, 2],
        )
        line = o3d.geometry.LineSet.create_camera_visualization(
            intrinsic=intrinsic,
            extrinsic=extrinsics[i],
            scale=scale,
        )
        line.paint_uniform_color(color)
        camera_lines.append(line)

    return camera_lines


def visualize_camera_trajectories(data_io: DataIO) -> None:
    import open3d as o3d

    left_depth_camera_lines = get_camera_visualization_lines(
        dataset=data_io.depth.load_depth_dataset(Side.LEFT),
        color=np.array([1, 0, 0]),
    )
    right_depth_camera_lines = get_camera_visualization_lines(
        dataset=data_io.depth.load_depth_dataset(Side.RIGHT),
        color=np.array([0, 1, 0]),
    )
    left_rgb_camera_lines = get_camera_visualization_lines(
        dataset=data_io.color.load_color_dataset(Side.LEFT),
        color=np.array([0, 0, 1]),
    )
    right_rgb_camera_lines = get_camera_visualization_lines(
        dataset=data_io.color.load_color_dataset(Side.RIGHT),
        color=np.array([1, 1, 0]),
    )

    axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.6, origin=[0, 0, 0])
    lines = (
        left_depth_camera_lines
        + right_depth_camera_lines
        + left_rgb_camera_lines
        + right_rgb_camera_lines
        + [axis]
    )
    o3d.visualization.draw_geometries(lines, window_name="Visualize Camera Trajectory")
