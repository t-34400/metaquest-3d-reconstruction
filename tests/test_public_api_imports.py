import importlib


def test_lightweight_public_imports_do_not_require_reconstruction_dependencies():
    importlib.import_module("mq3drecon")

    from mq3drecon.config import Depth2LinearConfig, LegacyProjectLayout, ProjectPathConfig, Yuv2RgbConfig
    from mq3drecon.dataio import DataIO, DepthDataIO, ImageDataIO, RGBDDataIO
    from mq3drecon.layouts import ColmapExportLayout, PackageOutputLayout
    from mq3drecon.models import CameraDataset, CoordinateSystem, DepthDataset, Side, Transforms
    from mq3drecon.processing.depth_conversion import convert_depth_directory
    from mq3drecon.processing.yuv_conversion import convert_yuv_directory
    from mq3drecon.workflows import export_colmap_project, run_depth_to_linear, run_yuv_to_rgb

    assert Depth2LinearConfig is not None
    assert LegacyProjectLayout is not None
    assert ProjectPathConfig is not None
    assert Yuv2RgbConfig is not None
    assert DataIO is not None
    assert DepthDataIO is not None
    assert ImageDataIO is not None
    assert RGBDDataIO is not None
    assert ColmapExportLayout is not None
    assert PackageOutputLayout is not None
    assert CameraDataset is not None
    assert CoordinateSystem is not None
    assert DepthDataset is not None
    assert Side is not None
    assert Transforms is not None
    assert convert_depth_directory is not None
    assert convert_yuv_directory is not None
    assert export_colmap_project is not None
    assert run_depth_to_linear is not None
    assert run_yuv_to_rgb is not None
