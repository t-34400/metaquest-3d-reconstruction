from mq3drecon.workflows import get_rgb_image_status, has_rgb_images


def test_rgb_image_status_counts_legacy_rgb_png_files(tmp_path):
    (tmp_path / "left_camera_rgb").mkdir()
    (tmp_path / "right_camera_rgb").mkdir()
    (tmp_path / "left_camera_rgb" / "100.png").write_bytes(b"")
    (tmp_path / "left_camera_rgb" / "200.png").write_bytes(b"")
    (tmp_path / "right_camera_rgb" / "100.png").write_bytes(b"")
    (tmp_path / "right_camera_rgb" / "ignore.txt").write_text("not an image")

    status = get_rgb_image_status(tmp_path)

    assert status.left_count == 2
    assert status.right_count == 1
    assert status.is_complete
    assert not status.is_balanced
    assert has_rgb_images(tmp_path)


def test_rgb_image_status_reports_incomplete_when_one_side_is_missing(tmp_path):
    (tmp_path / "left_camera_rgb").mkdir()
    (tmp_path / "left_camera_rgb" / "100.png").write_bytes(b"")

    status = get_rgb_image_status(tmp_path)

    assert status.left_count == 1
    assert status.right_count == 0
    assert not status.is_complete
    assert not status.is_balanced
    assert not has_rgb_images(tmp_path)
