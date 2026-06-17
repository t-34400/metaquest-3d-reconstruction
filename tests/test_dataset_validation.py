import numpy as np
import pytest

from mq3drecon.models import CameraDataset, CoordinateSystem, DepthDataset, Transforms


def make_camera_dataset(length: int = 2, directory_relative_path: str = "frames") -> CameraDataset:
    return CameraDataset(
        directory_relative_path=directory_relative_path,
        image_file_names=np.array([f"{i}.png" for i in range(length)]),
        timestamps=np.arange(length),
        fx=np.ones(length),
        fy=np.ones(length),
        cx=np.ones(length),
        cy=np.ones(length),
        transforms=Transforms(
            coordinate_system=CoordinateSystem.UNITY,
            positions=np.zeros((length, 3)),
            rotations=np.tile(np.array([0.0, 0.0, 0.0, 1.0]), (length, 1)),
        ),
        widths=np.full(length, 640),
        heights=np.full(length, 480),
    )


def test_camera_dataset_rejects_mismatched_array_lengths():
    with pytest.raises(ValueError, match="matching first dimensions"):
        CameraDataset(
            directory_relative_path="frames",
            image_file_names=np.array(["0.png", "1.png"]),
            timestamps=np.array([0]),
            fx=np.ones(2),
            fy=np.ones(2),
            cx=np.ones(2),
            cy=np.ones(2),
            transforms=Transforms(
                coordinate_system=CoordinateSystem.UNITY,
                positions=np.zeros((2, 3)),
                rotations=np.tile(np.array([0.0, 0.0, 0.0, 1.0]), (2, 1)),
            ),
            widths=np.full(2, 640),
            heights=np.full(2, 480),
        )


def test_camera_dataset_load_rejects_missing_required_keys(tmp_path):
    path = tmp_path / "camera_dataset.npz"
    data = make_camera_dataset().to_dict()
    data.pop("widths")
    np.savez(path, **data)

    with pytest.raises(ValueError, match="Missing required dataset keys"):
        CameraDataset.load(path)


def test_depth_dataset_load_rejects_missing_depth_keys(tmp_path):
    path = tmp_path / "depth_dataset.npz"
    np.savez(path, **make_camera_dataset().to_dict())

    with pytest.raises(ValueError, match="Missing required dataset keys"):
        DepthDataset.load(path)


def test_camera_dataset_merge_rejects_empty_input():
    with pytest.raises(ValueError, match="empty dataset list"):
        CameraDataset.merge([])


def test_camera_dataset_merge_rejects_inconsistent_scalar_values():
    first = make_camera_dataset(directory_relative_path="first")
    second = make_camera_dataset(directory_relative_path="second")

    with pytest.raises(ValueError, match="Inconsistent scalar values"):
        CameraDataset.merge([first, second])
