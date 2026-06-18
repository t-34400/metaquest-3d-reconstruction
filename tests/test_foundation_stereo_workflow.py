from pathlib import Path

import cv2
import numpy as np

from mq3drecon.config import FoundationStereoConfig
from mq3drecon.models import CameraDataset, CoordinateSystem, Side, Transforms
from mq3drecon.processing.stereo_depth.preprocessing import resize_disparity_to_original, resize_pad_image
from mq3drecon.workflows import run_foundation_stereo_depth


class ConstantDisparityModel:
    def __init__(self, disparity: float):
        self.disparity = disparity
        self.calls = []

    def predict_disparity(self, left_image: np.ndarray, right_image: np.ndarray) -> np.ndarray:
        self.calls.append((left_image.shape, right_image.shape))
        return np.full(left_image.shape[:2], self.disparity, dtype=np.float32)


def _write_rgb(path: Path, value: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb = np.full((4, 6, 3), value, dtype=np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    assert cv2.imwrite(str(path), bgr)


def _save_color_dataset(project_dir: Path, side: Side, timestamp: int, x: float) -> None:
    if side == Side.LEFT:
        path = project_dir / "dataset" / "left_camera_dataset.npz"
        directory = "left_camera_rgb"
        file_name = f"{timestamp}.png"
    else:
        path = project_dir / "dataset" / "right_camera_dataset.npz"
        directory = "right_camera_rgb"
        file_name = f"{timestamp}.png"

    dataset = CameraDataset(
        directory_relative_path=directory,
        image_file_names=np.asarray([file_name]),
        timestamps=np.asarray([timestamp], dtype=np.int64),
        fx=np.asarray([100.0], dtype=np.float32),
        fy=np.asarray([100.0], dtype=np.float32),
        cx=np.asarray([3.0], dtype=np.float32),
        cy=np.asarray([2.0], dtype=np.float32),
        transforms=Transforms(
            coordinate_system=CoordinateSystem.UNITY,
            positions=np.asarray([[x, 0.0, 0.0]], dtype=np.float32),
            rotations=np.asarray([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32),
        ),
        widths=np.asarray([6], dtype=np.int32),
        heights=np.asarray([4], dtype=np.int32),
    )
    dataset.save(path)


def test_resize_pad_disparity_restores_original_pixel_scale():
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    _, info = resize_pad_image(image, 8, 8, preserve_aspect_ratio=True)
    model_disparity = np.full((8, 8), 4.0, dtype=np.float32)

    restored = resize_disparity_to_original(model_disparity, info)

    assert restored.shape == (4, 4)
    assert np.allclose(restored, 2.0)


def test_run_foundation_stereo_depth_writes_color_aligned_depth(tmp_path):
    _write_rgb(tmp_path / "left_camera_rgb" / "1000.png", 20)
    _write_rgb(tmp_path / "right_camera_rgb" / "1002.png", 30)
    _save_color_dataset(tmp_path, Side.LEFT, 1000, 0.0)
    _save_color_dataset(tmp_path, Side.RIGHT, 1002, 0.2)
    model = ConstantDisparityModel(disparity=10.0)

    run_foundation_stereo_depth(
        tmp_path,
        config=FoundationStereoConfig(output_sides=(Side.LEFT,), max_depth_m=None),
        disparity_model=model,
    )

    depth = np.load(tmp_path / "left_color_aligned_depth" / "1000.npy")
    assert depth.shape == (4, 6)
    assert np.allclose(depth, 2.0)
    assert not (tmp_path / "right_color_aligned_depth" / "1002.npy").exists()
    assert model.calls == [((4, 6, 3), (4, 6, 3))]


def test_run_foundation_stereo_depth_requires_model_path_without_injected_model(tmp_path):
    try:
        run_foundation_stereo_depth(tmp_path, config=FoundationStereoConfig())
    except ValueError as exc:
        assert "model_path is required" in str(exc)
    else:
        raise AssertionError("Expected missing model_path error")
