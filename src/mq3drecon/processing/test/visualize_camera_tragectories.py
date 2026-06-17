"""Compatibility exports for the legacy misspelled visualization module."""

from mq3drecon.processing.visualization.camera_trajectories import (  # noqa: F401
    get_camera_visualization_lines,
    visualize_camera_trajectories,
)

get_camera_visualization_line = get_camera_visualization_lines

__all__ = [
    "get_camera_visualization_line",
    "get_camera_visualization_lines",
    "visualize_camera_trajectories",
]
