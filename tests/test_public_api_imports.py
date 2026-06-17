import importlib
import sys


class BlockOpen3DFinder:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "open3d" or fullname.startswith("open3d."):
            raise ImportError("open3d intentionally blocked")
        return None


def test_lightweight_public_imports_do_not_require_reconstruction_dependencies():
    importlib.import_module("mq3drecon")

    from mq3drecon.config import Depth2LinearConfig, LegacyProjectLayout, ProjectPathConfig, Yuv2RgbConfig
    from mq3drecon.dataio import DataIO, DepthDataIO, ImageDataIO, RGBDDataIO, ReconstructionDataIO
    from mq3drecon.layouts import ColmapExportLayout, PackageOutputLayout
    from mq3drecon.models import CameraDataset, CoordinateSystem, DepthDataset, Side, Transforms
    from mq3drecon.pipeline import PipelineProcessor
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
    assert ReconstructionDataIO is not None
    assert ColmapExportLayout is not None
    assert PackageOutputLayout is not None
    assert CameraDataset is not None
    assert CoordinateSystem is not None
    assert DepthDataset is not None
    assert Side is not None
    assert Transforms is not None
    assert PipelineProcessor is not None
    assert convert_depth_directory is not None
    assert convert_yuv_directory is not None
    assert export_colmap_project is not None
    assert run_depth_to_linear is not None
    assert run_yuv_to_rgb is not None


def test_lightweight_public_imports_work_when_open3d_is_unavailable():
    sys.modules.pop("open3d", None)
    blocker = BlockOpen3DFinder()
    sys.meta_path.insert(0, blocker)
    try:
        from mq3drecon.config import PipelineConfigs, ReconstructionConfig
        from mq3drecon.dataio import DataIO, ReconstructionDataIO
        from mq3drecon.pipeline import PipelineProcessor
        from mq3drecon.workflows import export_colmap_project, run_depth_to_linear, run_yuv_to_rgb

        assert PipelineConfigs is not None
        assert ReconstructionConfig is not None
        assert DataIO is not None
        assert ReconstructionDataIO is not None
        assert PipelineProcessor is not None
        assert export_colmap_project is not None
        assert run_depth_to_linear is not None
        assert run_yuv_to_rgb is not None
        assert "open3d" not in sys.modules
    finally:
        sys.meta_path.remove(blocker)


def test_public_migration_modules_use_explicit_exports():
    import mq3drecon.config as config
    import mq3drecon.dataio as dataio
    import mq3drecon.pipeline as pipeline

    assert "__getattr__" not in config.__dict__
    assert "__getattr__" not in dataio.__dict__
    assert "__getattr__" not in pipeline.__dict__
