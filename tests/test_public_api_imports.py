import importlib
import sys


class BlockOpen3DFinder:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "open3d" or fullname.startswith("open3d."):
            raise ImportError("open3d intentionally blocked")
        return None


def test_lightweight_public_imports_do_not_require_reconstruction_dependencies():
    importlib.import_module("mq3drecon")

    from mq3drecon.config import (
        ColorAlignedDepthRenderingConfig,
        ColorOptimizationConfig,
        Depth2LinearConfig,
        DepthConfidenceEstimationConfig,
        FoundationStereoConfig,
        FragmentGenerationConfig,
        FragmentPoseRefinementConfig,
        IntegrationConfig,
        LegacyProjectLayout,
        ProjectPathConfig,
        Yuv2RgbConfig,
    )
    from mq3drecon.dataio import (
        CaptureBackend,
        DataIO,
        DepthDataIO,
        ImageDataIO,
        MRUKImageDataIO,
        MRUKIntrinsics,
        RGBDDataIO,
        ReconstructionDataIO,
        SessionInfo,
        load_session_info,
    )
    from mq3drecon.layouts import ColmapExportLayout, PackageOutputLayout
    from mq3drecon.models import (
        BaseTime,
        CameraCharacteristics,
        CameraDataset,
        ConfidenceMap,
        CoordinateSystem,
        DepthDataset,
        ImageFormatInfo,
        ImagePlaneInfo,
        Side,
        Transforms,
    )
    from mq3drecon.pipeline import PipelineProcessor
    from mq3drecon.processing.depth_conversion import (
        ColorAlignedDepthPngExportResult,
        convert_depth_directory,
        export_color_aligned_depth_pngs,
        save_depth_preview_png,
        save_metric_depth_png,
    )
    from mq3drecon.processing.rgba_conversion import convert_rgba_directory
    from mq3drecon.processing.yuv_conversion import convert_yuv_directory
    from mq3drecon.workflows import (
        RgbImageStatus,
        export_colmap_project,
        get_rgb_image_status,
        has_rgb_images,
        run_color_aligned_depth_to_png,
        run_depth_to_linear,
        run_foundation_stereo_depth,
        run_rgba_to_png,
        run_visualize_camera_trajectories,
        run_yuv_to_rgb,
    )

    assert ColorAlignedDepthRenderingConfig is not None
    assert ColorOptimizationConfig is not None
    assert Depth2LinearConfig is not None
    assert DepthConfidenceEstimationConfig is not None
    assert FoundationStereoConfig is not None
    assert FragmentGenerationConfig is not None
    assert FragmentPoseRefinementConfig is not None
    assert IntegrationConfig is not None
    assert LegacyProjectLayout is not None
    assert ProjectPathConfig is not None
    assert Yuv2RgbConfig is not None
    assert CaptureBackend is not None
    assert DataIO is not None
    assert DepthDataIO is not None
    assert ImageDataIO is not None
    assert MRUKImageDataIO is not None
    assert MRUKIntrinsics is not None
    assert RGBDDataIO is not None
    assert ReconstructionDataIO is not None
    assert SessionInfo is not None
    assert load_session_info is not None
    assert ColmapExportLayout is not None
    assert PackageOutputLayout is not None
    assert BaseTime is not None
    assert CameraCharacteristics is not None
    assert CameraDataset is not None
    assert ConfidenceMap is not None
    assert CoordinateSystem is not None
    assert DepthDataset is not None
    assert ImageFormatInfo is not None
    assert ImagePlaneInfo is not None
    assert Side is not None
    assert Transforms is not None
    assert PipelineProcessor is not None
    assert ColorAlignedDepthPngExportResult is not None
    assert convert_depth_directory is not None
    assert export_color_aligned_depth_pngs is not None
    assert save_depth_preview_png is not None
    assert save_metric_depth_png is not None
    assert convert_rgba_directory is not None
    assert convert_yuv_directory is not None
    assert RgbImageStatus is not None
    assert export_colmap_project is not None
    assert get_rgb_image_status is not None
    assert has_rgb_images is not None
    assert run_color_aligned_depth_to_png is not None
    assert run_depth_to_linear is not None
    assert run_foundation_stereo_depth is not None
    assert run_rgba_to_png is not None
    assert run_visualize_camera_trajectories is not None
    assert run_yuv_to_rgb is not None


def test_lightweight_public_imports_work_when_open3d_is_unavailable():
    sys.modules.pop("open3d", None)
    blocker = BlockOpen3DFinder()
    sys.meta_path.insert(0, blocker)
    try:
        from mq3drecon.config import PipelineConfigs, ReconstructionConfig
        from mq3drecon.dataio import DataIO, ReconstructionDataIO
        from mq3drecon.pipeline import PipelineProcessor
        from mq3drecon.workflows import (
            RgbImageStatus,
            export_colmap_project,
            get_rgb_image_status,
            has_rgb_images,
            run_color_aligned_depth_to_png,
            run_depth_to_linear,
            run_rgba_to_png,
            run_yuv_to_rgb,
        )

        assert PipelineConfigs is not None
        assert ReconstructionConfig is not None
        assert DataIO is not None
        assert ReconstructionDataIO is not None
        assert PipelineProcessor is not None
        assert RgbImageStatus is not None
        assert export_colmap_project is not None
        assert get_rgb_image_status is not None
        assert has_rgb_images is not None
        assert run_color_aligned_depth_to_png is not None
        assert run_depth_to_linear is not None
        assert run_rgba_to_png is not None
        assert run_yuv_to_rgb is not None
        assert "open3d" not in sys.modules
    finally:
        sys.meta_path.remove(blocker)


def test_public_migration_modules_use_explicit_exports():
    import mq3drecon.config as config
    import mq3drecon.dataio as dataio
    import mq3drecon.models as models
    import mq3drecon.pipeline as pipeline

    assert "__getattr__" not in config.__dict__
    assert "__getattr__" not in dataio.__dict__
    assert "__getattr__" not in models.__dict__
    assert "__getattr__" not in pipeline.__dict__


def test_top_level_namespace_reexports_workflow_and_config_apis():
    from mq3drecon import (
        Depth2LinearConfig,
        FoundationStereoConfig,
        MQ3DReconError,
        PipelineConfigs,
        ProcessingError,
        ProjectPathConfig,
        ReconstructionConfig,
        RgbImageStatus,
        Yuv2RgbConfig,
        export_colmap_project,
        get_rgb_image_status,
        has_rgb_images,
        run_color_aligned_depth_to_png,
        run_depth_to_linear,
        run_foundation_stereo_depth,
        run_reconstruct_scene,
        run_rgba_to_png,
        run_visualize_camera_trajectories,
        run_yuv_to_rgb,
    )

    assert Depth2LinearConfig is not None
    assert FoundationStereoConfig is not None
    assert MQ3DReconError is not None
    assert PipelineConfigs is not None
    assert ProcessingError is not None
    assert ProjectPathConfig is not None
    assert ReconstructionConfig is not None
    assert RgbImageStatus is not None
    assert Yuv2RgbConfig is not None
    assert export_colmap_project is not None
    assert get_rgb_image_status is not None
    assert has_rgb_images is not None
    assert run_color_aligned_depth_to_png is not None
    assert run_depth_to_linear is not None
    assert run_foundation_stereo_depth is not None
    assert run_reconstruct_scene is not None
    assert run_rgba_to_png is not None
    assert run_visualize_camera_trajectories is not None
    assert run_yuv_to_rgb is not None
