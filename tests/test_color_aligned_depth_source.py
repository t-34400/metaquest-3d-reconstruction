import numpy as np

from mq3drecon.config import ReconstructionConfig
from mq3drecon.dataio import DataIO
from mq3drecon.models import CameraDataset, CoordinateSystem, Side, Transforms


def _save_color_dataset(project_dir, side, timestamps):
    if side == Side.LEFT:
        path = project_dir / "dataset" / "left_camera_dataset.npz"
        directory = "left_camera_rgb"
    else:
        path = project_dir / "dataset" / "right_camera_dataset.npz"
        directory = "right_camera_rgb"

    timestamps = np.asarray(timestamps, dtype=np.int64)
    dataset = CameraDataset(
        directory_relative_path=directory,
        image_file_names=np.asarray([f"{ts}.png" for ts in timestamps]),
        timestamps=timestamps,
        fx=np.full(len(timestamps), 100.0, dtype=np.float32),
        fy=np.full(len(timestamps), 100.0, dtype=np.float32),
        cx=np.full(len(timestamps), 3.0, dtype=np.float32),
        cy=np.full(len(timestamps), 2.0, dtype=np.float32),
        transforms=Transforms(
            coordinate_system=CoordinateSystem.UNITY,
            positions=np.zeros((len(timestamps), 3), dtype=np.float32),
            rotations=np.tile(np.asarray([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32), (len(timestamps), 1)),
        ),
        widths=np.full(len(timestamps), 6, dtype=np.int32),
        heights=np.full(len(timestamps), 4, dtype=np.int32),
    )
    dataset.save(path)
    return dataset


def test_reconstruction_config_accepts_color_aligned_depth_source():
    config = ReconstructionConfig.parse({"depth_source": "color_aligned"})

    assert config.depth_source == "color_aligned"


def test_reconstruction_config_accepts_rectified_stereo_depth_source():
    config = ReconstructionConfig.parse({"depth_source": "rectified_stereo"})

    assert config.depth_source == "rectified_stereo"


def test_reconstruction_config_rejects_unknown_depth_source():
    try:
        ReconstructionConfig.parse({"depth_source": "invalid"})
    except ValueError as exc:
        assert "depth_source" in str(exc)
    else:
        raise AssertionError("Expected invalid depth_source error")


def test_rgbd_builds_color_aligned_depth_dataset_from_existing_maps(tmp_path):
    color_dataset = _save_color_dataset(tmp_path, Side.LEFT, [1000, 2000, 3000])
    depth_dir = tmp_path / "left_color_aligned_depth"
    depth_dir.mkdir()
    np.save(depth_dir / "1000.npy", np.ones((4, 6), dtype=np.float32))
    np.save(depth_dir / "3000.npy", np.full((4, 6), np.nan, dtype=np.float32))

    data_io = DataIO(tmp_path)
    dataset = data_io.rgbd.build_color_aligned_depth_dataset(Side.LEFT, color_dataset)

    assert dataset.directory_relative_path == "left_color_aligned_depth"
    assert dataset.image_file_names.tolist() == ["1000.npy", "3000.npy"]
    assert dataset.timestamps.tolist() == [1000, 3000]
    assert dataset.fx.tolist() == [100.0, 100.0]

    first = data_io.rgbd.load_color_aligned_depth_by_index(Side.LEFT, dataset, 0)
    second = data_io.rgbd.load_color_aligned_depth_by_index(Side.LEFT, dataset, 1)
    assert np.allclose(first, 1.0)
    assert np.allclose(second, 0.0)


def test_rgbd_color_aligned_depth_shape_mismatch_is_explicit(tmp_path):
    color_dataset = _save_color_dataset(tmp_path, Side.LEFT, [1000])
    depth_dir = tmp_path / "left_color_aligned_depth"
    depth_dir.mkdir()
    np.save(depth_dir / "1000.npy", np.ones((2, 2), dtype=np.float32))

    data_io = DataIO(tmp_path)
    dataset = data_io.rgbd.build_color_aligned_depth_dataset(Side.LEFT, color_dataset)

    try:
        data_io.rgbd.load_color_aligned_depth_by_index(Side.LEFT, dataset, 0)
    except ValueError as exc:
        assert "shape" in str(exc)
    else:
        raise AssertionError("Expected shape mismatch error")


def test_rgbd_builds_matching_color_and_depth_datasets_for_existing_maps(tmp_path):
    color_dataset = _save_color_dataset(tmp_path, Side.LEFT, [1000, 2000, 3000])
    depth_dir = tmp_path / "left_color_aligned_depth"
    depth_dir.mkdir()
    np.save(depth_dir / "1000.npy", np.ones((4, 6), dtype=np.float32))
    np.save(depth_dir / "3000.npy", np.ones((4, 6), dtype=np.float32))

    data_io = DataIO(tmp_path)
    matched_color_dataset, depth_dataset = data_io.rgbd.build_color_aligned_rgbd_datasets(
        Side.LEFT,
        color_dataset,
    )

    assert matched_color_dataset.timestamps.tolist() == [1000, 3000]
    assert matched_color_dataset.image_file_names.tolist() == ["1000.png", "3000.png"]
    assert depth_dataset.timestamps.tolist() == [1000, 3000]
    assert depth_dataset.image_file_names.tolist() == ["1000.npy", "3000.npy"]


def test_color_aligned_rgbd_loader_uses_float_color_for_float_depth(tmp_path):
    import cv2
    import pytest

    o3d = pytest.importorskip("open3d")

    from mq3drecon.processing.reconstruction.color_aligned_rgbd_integration import _load_rgbd_images

    color_dataset = _save_color_dataset(tmp_path, Side.LEFT, [1000])
    color_dir = tmp_path / "left_camera_rgb"
    color_dir.mkdir()
    rgb = np.zeros((4, 6, 3), dtype=np.uint8)
    rgb[0, 0] = [255, 128, 0]
    cv2.imwrite(str(color_dir / "1000.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

    depth_dir = tmp_path / "left_color_aligned_depth"
    depth_dir.mkdir()
    np.save(depth_dir / "1000.npy", np.ones((4, 6), dtype=np.float32))

    data_io = DataIO(tmp_path)
    _, depth_dataset = data_io.rgbd.build_color_aligned_rgbd_datasets(Side.LEFT, color_dataset)
    color_image, depth_image = _load_rgbd_images(
        data_io=data_io,
        color_dataset=color_dataset,
        depth_dataset=depth_dataset,
        index=0,
        device=o3d.core.Device("CPU:0"),
    )

    assert color_image.as_tensor().dtype == o3d.core.Dtype.Float32
    assert depth_image.as_tensor().dtype == o3d.core.Dtype.Float32
    assert np.allclose(color_image.as_tensor().cpu().numpy()[0, 0], [1.0, 128.0 / 255.0, 0.0])


def test_rgbd_builds_rectified_stereo_rgbd_datasets(tmp_path):
    color_dataset = _save_color_dataset(tmp_path, Side.LEFT, [1000])
    color_dataset.directory_relative_path = "left_rectified_stereo_color"
    color_dataset.image_file_names = np.asarray(["1000.png"])
    color_dataset.save(tmp_path / "dataset" / "left_rectified_stereo_color_dataset.npz")

    depth_dataset = color_dataset.__class__.from_dict(color_dataset.to_dict())
    from mq3drecon.models import DepthDataset

    depth_dataset = DepthDataset(
        directory_relative_path="left_rectified_stereo_depth",
        image_file_names=np.asarray(["1000.npy"]),
        timestamps=color_dataset.timestamps,
        fx=color_dataset.fx,
        fy=color_dataset.fy,
        cx=color_dataset.cx,
        cy=color_dataset.cy,
        transforms=color_dataset.transforms,
        widths=color_dataset.widths,
        heights=color_dataset.heights,
        nears=np.asarray([0.0], dtype=np.float32),
        fars=np.asarray([np.inf], dtype=np.float32),
    )
    depth_dataset.save(tmp_path / "dataset" / "left_rectified_stereo_depth_dataset.npz")
    (tmp_path / "left_rectified_stereo_color").mkdir()
    (tmp_path / "left_rectified_stereo_depth").mkdir()
    np.save(tmp_path / "left_rectified_stereo_depth" / "1000.npy", np.ones((4, 6), dtype=np.float32))

    data_io = DataIO(tmp_path)
    matched_color, matched_depth = data_io.rgbd.build_rectified_stereo_rgbd_datasets(Side.LEFT)

    assert matched_color.directory_relative_path == "left_rectified_stereo_color"
    assert matched_depth.directory_relative_path == "left_rectified_stereo_depth"
    assert matched_color.timestamps.tolist() == [1000]
    assert matched_depth.timestamps.tolist() == [1000]
