import cv2
import numpy as np

from mq3drecon.models import Side
from mq3drecon.workflows import run_color_aligned_depth_to_png


def test_run_color_aligned_depth_to_png_writes_preview_and_metric_png(tmp_path):
    depth_dir = tmp_path / "left_color_aligned_depth"
    depth_dir.mkdir()
    depth = np.array(
        [
            [0.0, 1.0, 2.0],
            [np.nan, 3.0, 4.0],
        ],
        dtype=np.float32,
    )
    np.save(depth_dir / "1000.npy", depth)

    result = run_color_aligned_depth_to_png(
        tmp_path,
        side=Side.LEFT,
        write_metric_png=True,
        write_preview_png=True,
        depth_preview_min_m=0.0,
        depth_preview_max_m=4.0,
    )

    metric_png = cv2.imread(str(tmp_path / "left_color_aligned_depth_png" / "1000.png"), cv2.IMREAD_UNCHANGED)
    preview_png = cv2.imread(str(tmp_path / "left_color_aligned_depth_preview_png" / "1000.png"), cv2.IMREAD_UNCHANGED)

    assert result.metric_png_count == 1
    assert result.preview_png_count == 1
    assert metric_png.dtype == np.uint16
    assert metric_png.tolist() == [[0, 1000, 2000], [0, 3000, 4000]]
    assert preview_png.dtype == np.uint8
    assert preview_png.tolist() == [[0, 64, 128], [0, 191, 255]]


def test_run_color_aligned_depth_to_png_rejects_empty_output_selection(tmp_path):
    depth_dir = tmp_path / "left_color_aligned_depth"
    depth_dir.mkdir()
    np.save(depth_dir / "1000.npy", np.ones((2, 2), dtype=np.float32))

    try:
        run_color_aligned_depth_to_png(tmp_path, write_metric_png=False, write_preview_png=False)
    except ValueError as exc:
        assert "At least one" in str(exc)
    else:
        raise AssertionError("Expected empty output selection to fail")
