import numpy as np


def bilinear_interpolate_depth(depth_map: np.ndarray, u: np.ndarray, v: np.ndarray, depth_max: float) -> np.ndarray:
    h, w = depth_map.shape
    u0 = np.floor(u).astype(np.int32)
    v0 = np.floor(v).astype(np.int32)
    u1 = u0 + 1
    v1 = v0 + 1

    valid = (
        (u0 >= 0) & (u1 < w) &
        (v0 >= 0) & (v1 < h)
    )

    z = np.zeros_like(u, dtype=np.float32)

    u0v = u0[valid]
    u1v = u1[valid]
    v0v = v0[valid]
    v1v = v1[valid]
    uv = u[valid]
    vv = v[valid]

    Ia = depth_map[v0v, u0v]
    Ib = depth_map[v0v, u1v]
    Ic = depth_map[v1v, u0v]
    Id = depth_map[v1v, u1v]

    is_valid_interp = (
        (Ib > 0) & (Ib <= depth_max) &
        (Ia > 0) & (Ia <= depth_max) &
        (Ic > 0) & (Ic <= depth_max) &
        (Id > 0) & (Id <= depth_max)
    )

    wa = (u1v - uv) * (v1v - vv)
    wb = (uv - u0v) * (v1v - vv)
    wc = (u1v - uv) * (vv - v0v)
    wd = (uv - u0v) * (vv - v0v)

    z_interp = wa * Ia + wb * Ib + wc * Ic + wd * Id
    z[valid] = np.where(is_valid_interp, z_interp, 0.0)

    return z


def depth_to_pointcloud_numpy(
    depth_map: np.ndarray,   # (h, w)
    intrinsics: np.ndarray,  # (3, 3)
    extrinsics: np.ndarray,  # (4, 4)
    depth_max: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fx, fy = intrinsics[0, 0], intrinsics[1, 1]
    cx, cy = intrinsics[0, 2], intrinsics[1, 2]

    valid_mask = (depth_map > 0) & (depth_map <= depth_max)
    v_coords, u_coords = np.where(valid_mask)

    z = depth_map[v_coords, u_coords]
    x = (u_coords - cx) * z / fx
    y = (v_coords - cy) * z / fy

    points_cam = np.stack([x, y, z], axis=1)

    ones = np.ones((points_cam.shape[0], 1))
    points_cam_h = np.concatenate([points_cam, ones], axis=1)
    points_world = (extrinsics @ points_cam_h.T).T[:, :3]

    return points_world, u_coords, v_coords


def compute_pixel_error_map(
    intrinsic_matrices: np.ndarray,
    extrinsic_matrices: np.ndarray,
    extrinsic_matrices_inv: np.ndarray,
    ref_frame_idx: int,
    ref_depth_map: np.ndarray,
    target_frame_idx: int,
    target_depth_map: np.ndarray,
    depth_max: float = 3.0
) -> np.ndarray:
    h, w = ref_depth_map.shape

    # Step 1: target depth -> world point cloud
    ref_points_world, ref_u, ref_v = depth_to_pointcloud_numpy(
        depth_map=ref_depth_map,
        intrinsics=intrinsic_matrices[ref_frame_idx],
        extrinsics=extrinsic_matrices[ref_frame_idx],
        depth_max=depth_max
    )

    # Step 2: world point cloud -> target camera space
    source_extr_inv = extrinsic_matrices_inv[target_frame_idx]
    points_h = np.hstack([ref_points_world, np.ones((ref_points_world.shape[0], 1))])
    target_points = (source_extr_inv @ points_h.T).T[:, :3]

    x, y, z = target_points[:, 0], target_points[:, 1], target_points[:, 2]
    fx, fy = intrinsic_matrices[target_frame_idx][0, 0], intrinsic_matrices[target_frame_idx][1, 1]
    cx, cy = intrinsic_matrices[target_frame_idx][0, 2], intrinsic_matrices[target_frame_idx][1, 2]

    # Step 3: Project points to target depth map pixel coordinates
    valid_project_mask = (z > 0) & np.isfinite(z) & (z <= depth_max)
    x, y, z = x[valid_project_mask], y[valid_project_mask], z[valid_project_mask]

    u = (x * fx / z) + cx
    v = (y * fy / z) + cy

    # Step 4: Bilinear interpolation to get target depth values
    z_target = bilinear_interpolate_depth(
        depth_map=target_depth_map,
        u=u,
        v=v,
        depth_max=depth_max
    )
    valid_target_mask = z_target > 0

    # Step 5: Compute pixel errors
    x_valid_target  = (u[valid_target_mask] - cx) * z_target[valid_target_mask] / fx
    y_valid_target  = (v[valid_target_mask] - cy) * z_target[valid_target_mask] / fy
    z_valid_target  = z_target[valid_target_mask]
    target_points = np.stack([x_valid_target, y_valid_target, z_valid_target], axis=1)

    ones = np.ones((target_points.shape[0], 1))
    target_points_h = np.concatenate([target_points, ones], axis=1)
    target_points_world = (extrinsic_matrices[target_frame_idx] @ target_points_h.T).T[:, :3]

    ref_points_valid_world = ref_points_world[valid_project_mask][valid_target_mask]
    dist = np.linalg.norm(ref_points_valid_world - target_points_world, axis=1)

    # Step 6: Create confidence map
    confidence_map = np.full_like(ref_depth_map, fill_value=np.nan, dtype=np.float32)

    u_valid = ref_u[valid_project_mask][valid_target_mask]
    v_valid = ref_v[valid_project_mask][valid_target_mask]
    inside_mask = (u_valid >= 0) & (u_valid < w) & (v_valid >= 0) & (v_valid < h)

    u_valid = u_valid[inside_mask]
    v_valid = v_valid[inside_mask]

    confidence_map[v_valid, u_valid] = dist[inside_mask]

    return confidence_map