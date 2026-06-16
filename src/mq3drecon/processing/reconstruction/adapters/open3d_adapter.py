from typing import Any


def to_open3d_device(device: Any):
    import open3d as o3d

    if isinstance(device, str):
        return o3d.core.Device(device)
    return device


def make_icp_criteria_list(config):
    import open3d as o3d

    return [
        o3d.t.pipelines.registration.ICPConvergenceCriteria(
            max_iteration=config.max_iterations[i],
            relative_fitness=config.relative_fitnesses[i],
            relative_rmse=config.relative_rmses[i],
        )
        for i in range(len(config.icp_voxel_sizes))
    ]
