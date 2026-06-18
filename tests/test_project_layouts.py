from pathlib import Path

from mq3drecon.config import ProjectPathConfig
from mq3drecon.layouts import ColmapExportLayout, LegacyProjectLayout, PackageOutputLayout
from mq3drecon.models import Side


def test_legacy_project_layout_preserves_existing_paths(tmp_path):
    layout = LegacyProjectLayout(tmp_path)

    assert layout.image.get_yuv_dir(Side.LEFT) == tmp_path / "left_camera_raw"
    assert layout.image.get_rgb_file_path(Side.RIGHT, 123) == tmp_path / "right_camera_rgb" / "123.png"
    assert layout.image.get_camera_format_json_path(Side.LEFT) == tmp_path / "left_camera_image_format.json"
    assert layout.image.get_camera_format_format_json_path(Side.LEFT) == layout.image.get_camera_format_json_path(Side.LEFT)
    assert layout.image.get_session_info_json_path() == tmp_path / "session_info.json"
    assert layout.image.get_mruk_rgba_dir(Side.LEFT) == tmp_path / "left_camera_mruk_rgba"
    assert layout.image.get_mruk_intrinsics_json_path(Side.RIGHT) == tmp_path / "right_camera_mruk_intrinsics.json"
    assert layout.image.get_mruk_frame_metadata_csv_path(Side.LEFT) == tmp_path / "left_camera_mruk_frame_metadata.csv"
    assert layout.image.get_mruk_stereo_pairs_csv_path() == tmp_path / "mruk_stereo_pairs.csv"
    assert layout.depth.get_depth_dataset_path(Side.RIGHT) == tmp_path / "dataset" / "right_depth_dataset.npz"
    assert layout.reconstruction.get_colored_pcd_path() == tmp_path / "reconstruction" / "color.ply"


def test_project_path_config_remains_legacy_layout_alias(tmp_path):
    path_config = ProjectPathConfig(tmp_path)

    assert isinstance(path_config, LegacyProjectLayout)
    assert path_config.image.get_color_dataset_path(Side.LEFT) == tmp_path / "dataset" / "left_camera_dataset.npz"


def test_package_output_layout_uses_explicit_output_root(tmp_path):
    layout = PackageOutputLayout(tmp_path / "out")

    assert layout.get_dataset_dir() == tmp_path / "out" / "dataset"
    assert layout.get_cache_dir() == tmp_path / "out" / "cache"
    assert layout.get_reconstruction_dir() == tmp_path / "out" / "reconstruction"
    assert layout.get_rgb_dir(Side.LEFT) == tmp_path / "out" / "left_camera_rgb"
    assert layout.get_linear_depth_dir(Side.RIGHT) == tmp_path / "out" / "right_depth_linear"


def test_colmap_export_layout_owns_export_paths(tmp_path):
    layout = ColmapExportLayout(tmp_path / "colmap")

    assert layout.get_image_dir() == tmp_path / "colmap" / "images"
    assert layout.get_model_dir() == tmp_path / "colmap" / "distorted" / "sparse" / "0"

    layout.ensure_directories()

    assert layout.get_image_dir().is_dir()
    assert layout.get_model_dir().is_dir()
