from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R

from mq3drecon.models.camera_dataset import CameraDataset
from mq3drecon.models.side import Side
from mq3drecon.models.transforms import Transforms


@dataclass(frozen=True)
class StereoRectification:
    left_map_x: np.ndarray
    left_map_y: np.ndarray
    right_map_x: np.ndarray
    right_map_y: np.ndarray
    left_inverse_map_x: np.ndarray
    left_inverse_map_y: np.ndarray
    left_intrinsic: np.ndarray
    right_intrinsic: np.ndarray
    left_rectification: np.ndarray
    right_rectification: np.ndarray
    left_projection: np.ndarray
    right_projection: np.ndarray
    reprojection: np.ndarray
    baseline_m: float
    width: int
    height: int


def compute_stereo_rectification(
    left_dataset: CameraDataset,
    right_dataset: CameraDataset,
    left_index: int,
    right_index: int,
) -> StereoRectification:
    width = int(left_dataset.widths[left_index])
    height = int(left_dataset.heights[left_index])
    right_size = (int(right_dataset.widths[right_index]), int(right_dataset.heights[right_index]))
    if right_size != (width, height):
        raise ValueError(f"Stereo rectification requires matching image sizes, got left={(width, height)} right={right_size}")

    left_k = _intrinsic_matrix(left_dataset, left_index)
    right_k = _intrinsic_matrix(right_dataset, right_index)
    left_r_cw = R.from_quat(left_dataset.transforms.rotations[left_index]).as_matrix()
    right_r_cw = R.from_quat(right_dataset.transforms.rotations[right_index]).as_matrix()
    left_position = np.asarray(left_dataset.transforms.positions[left_index], dtype=np.float64)
    right_position = np.asarray(right_dataset.transforms.positions[right_index], dtype=np.float64)

    right_r_wc = right_r_cw.T
    relative_r = right_r_wc @ left_r_cw
    relative_t = right_r_wc @ (left_position - right_position)

    dist = np.zeros(5, dtype=np.float64)
    image_size = (width, height)
    left_rect, right_rect, left_proj, right_proj, reproj, _, _ = cv2.stereoRectify(
        cameraMatrix1=left_k,
        distCoeffs1=dist,
        cameraMatrix2=right_k,
        distCoeffs2=dist,
        imageSize=image_size,
        R=relative_r,
        T=relative_t.reshape(3, 1),
        flags=cv2.CALIB_ZERO_DISPARITY,
        alpha=0,
    )

    left_map_x, left_map_y = cv2.initUndistortRectifyMap(
        left_k, dist, left_rect, left_proj, image_size, cv2.CV_32FC1
    )
    right_map_x, right_map_y = cv2.initUndistortRectifyMap(
        right_k, dist, right_rect, right_proj, image_size, cv2.CV_32FC1
    )
    inv_x, inv_y = _build_left_inverse_rectification_map(left_k, left_rect, left_proj[:3, :3], width, height)

    fx = float(left_proj[0, 0])
    baseline = abs(float(right_proj[0, 3]) / fx) if fx != 0.0 else 0.0
    if baseline <= 0.0:
        baseline = float(np.linalg.norm(relative_t))
    if baseline <= 0.0:
        raise ValueError("Stereo baseline is zero after rectification")

    return StereoRectification(
        left_map_x=left_map_x,
        left_map_y=left_map_y,
        right_map_x=right_map_x,
        right_map_y=right_map_y,
        left_inverse_map_x=inv_x,
        left_inverse_map_y=inv_y,
        left_intrinsic=left_proj[:3, :3].astype(np.float32),
        right_intrinsic=right_proj[:3, :3].astype(np.float32),
        left_rectification=left_rect.astype(np.float32),
        right_rectification=right_rect.astype(np.float32),
        left_projection=left_proj.astype(np.float32),
        right_projection=right_proj.astype(np.float32),
        reprojection=reproj.astype(np.float32),
        baseline_m=baseline,
        width=width,
        height=height,
    )


def rectify_image(image: np.ndarray, map_x: np.ndarray, map_y: np.ndarray) -> np.ndarray:
    return cv2.remap(image, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def inverse_rectify_left_depth(depth: np.ndarray, rectification: StereoRectification) -> np.ndarray:
    restored = cv2.remap(
        depth.astype(np.float32, copy=False),
        rectification.left_inverse_map_x,
        rectification.left_inverse_map_y,
        interpolation=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    return np.where(np.isfinite(restored) & (restored > 0.0), restored, np.nan).astype(np.float32)


def make_rectified_dataset(
    source_dataset: CameraDataset,
    indices: list[int],
    side: Side,
    directory_relative_path: str,
    file_names: list[str],
    rectifications: list[StereoRectification],
) -> CameraDataset:
    if len(indices) != len(rectifications):
        raise ValueError("indices and rectifications must have matching lengths")

    fx: list[float] = []
    fy: list[float] = []
    cx: list[float] = []
    cy: list[float] = []
    widths: list[int] = []
    heights: list[int] = []
    rotations: list[np.ndarray] = []
    positions: list[np.ndarray] = []
    timestamps: list[int] = []

    for index, rectification in zip(indices, rectifications):
        intrinsic = rectification.left_intrinsic if side == Side.LEFT else rectification.right_intrinsic
        rect = rectification.left_rectification if side == Side.LEFT else rectification.right_rectification
        source_rotation = R.from_quat(source_dataset.transforms.rotations[index]).as_matrix()
        rectified_rotation = source_rotation @ rect.T
        fx.append(float(intrinsic[0, 0]))
        fy.append(float(intrinsic[1, 1]))
        cx.append(float(intrinsic[0, 2]))
        cy.append(float(intrinsic[1, 2]))
        widths.append(rectification.width)
        heights.append(rectification.height)
        rotations.append(R.from_matrix(rectified_rotation).as_quat().astype(np.float32))
        positions.append(np.asarray(source_dataset.transforms.positions[index], dtype=np.float32))
        timestamps.append(int(source_dataset.timestamps[index]))

    return CameraDataset(
        directory_relative_path=directory_relative_path,
        image_file_names=np.asarray(file_names),
        timestamps=np.asarray(timestamps, dtype=np.int64),
        fx=np.asarray(fx, dtype=np.float32),
        fy=np.asarray(fy, dtype=np.float32),
        cx=np.asarray(cx, dtype=np.float32),
        cy=np.asarray(cy, dtype=np.float32),
        transforms=Transforms(
            coordinate_system=source_dataset.transforms.coordinate_system,
            positions=np.asarray(positions, dtype=np.float32),
            rotations=np.asarray(rotations, dtype=np.float32),
        ),
        widths=np.asarray(widths, dtype=np.int32),
        heights=np.asarray(heights, dtype=np.int32),
    )


def _intrinsic_matrix(dataset: CameraDataset, index: int) -> np.ndarray:
    return np.asarray(
        [
            [float(dataset.fx[index]), 0.0, float(dataset.cx[index])],
            [0.0, float(dataset.fy[index]), float(dataset.cy[index])],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def _build_left_inverse_rectification_map(
    original_k: np.ndarray,
    left_rectification: np.ndarray,
    rectified_k: np.ndarray,
    width: int,
    height: int,
) -> tuple[np.ndarray, np.ndarray]:
    ys, xs = np.indices((height, width), dtype=np.float32)
    rays = np.stack([xs, ys, np.ones_like(xs)], axis=-1).reshape(-1, 3).T
    original_rays = np.linalg.inv(original_k) @ rays
    rectified_rays = left_rectification @ original_rays
    pixels = rectified_k @ rectified_rays
    pixels[:2] /= np.where(np.abs(pixels[2:3]) > 1e-12, pixels[2:3], np.nan)
    map_x = pixels[0].reshape(height, width).astype(np.float32)
    map_y = pixels[1].reshape(height, width).astype(np.float32)
    return map_x, map_y
