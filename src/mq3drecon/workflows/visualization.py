"""Package-backed visualization workflow APIs."""

from pathlib import Path


def run_visualize_camera_trajectories(project_dir: Path) -> None:
    from mq3drecon.dataio import DataIO
    from mq3drecon.processing.test.visualize_camera_tragectories import (
        visualize_camera_trajectories,
    )

    data_io = DataIO(project_dir=project_dir)
    visualize_camera_trajectories(data_io=data_io)
