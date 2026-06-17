from pathlib import Path

from mq3drecon.models import Side
from mq3drecon.workflows import RgbImageStatus, get_rgb_image_status, has_rgb_images


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"placeholder")


def test_rgb_image_status_reports_missing_images(tmp_path):
    status = get_rgb_image_status(tmp_path)

    assert isinstance(status, RgbImageStatus)
    assert status.left_count == 0
    assert status.right_count == 0
    assert not status.has_left
    assert not status.has_right
    assert not status.is_complete
    assert status.is_balanced
    assert not has_rgb_images(tmp_path)


def test_rgb_image_status_reports_available_images(tmp_path):
    touch(tmp_path / "left_camera_rgb" / "100.png")
    touch(tmp_path / "right_camera_rgb" / "100.png")
    touch(tmp_path / "right_camera_rgb" / "ignored.txt")

    status = get_rgb_image_status(tmp_path)

    assert status.left_count == 1
    assert status.right_count == 1
    assert status.has_left
    assert status.has_right
    assert status.is_complete
    assert status.is_balanced
    assert status.count_for(Side.LEFT) == 1
    assert status.count_for(Side.RIGHT) == 1
    assert status.directory_for(Side.LEFT) == tmp_path / "left_camera_rgb"
    assert status.directory_for(Side.RIGHT) == tmp_path / "right_camera_rgb"
    assert has_rgb_images(tmp_path)


def test_rgb_image_status_exposes_unbalanced_counts(tmp_path):
    touch(tmp_path / "left_camera_rgb" / "100.png")
    touch(tmp_path / "left_camera_rgb" / "200.png")
    touch(tmp_path / "right_camera_rgb" / "100.png")

    status = get_rgb_image_status(tmp_path)

    assert status.is_complete
    assert not status.is_balanced
