import numpy as np


def compute_depth_camera_params(
    left: float,
    right: float,
    top: float,
    bottom: float,
    width: int,
    height: int,
):
    fx = width / (right + left)
    fy = height / (top + bottom)

    cx = width * right / (right + left)
    cy = height * top / (top + bottom)

    return fx, fy, cx, cy


def compute_ndc_to_linear_depth_params(near, far):
    if np.isinf(far) or far < near:
        x = -2.0 * near
        y = -1.0
    else:
        x = -2.0 * far * near / (far - near)
        y = -(far + near) / (far - near)
    return x, y


def to_linear_depth(d, x, y):
    ndc = d * 2.0 - 1.0
    denom = ndc + y

    return np.divide(
        x, denom,
        out=np.zeros_like(d),
        where=denom != 0
    )


def convert_depth_to_linear(depth_buffer: np.ndarray, near: float, far: float):
    x, y = compute_ndc_to_linear_depth_params(near, far)
    depth_array = to_linear_depth(depth_buffer, x, y)

    depth_image = depth_array.astype(np.float32)
    return depth_image