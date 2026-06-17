from pathlib import Path

import pytest

import mq3drecon.workflows.conversion as conversion
from mq3drecon.config import Depth2LinearConfig, Yuv2RgbConfig


def test_conversion_configs_are_default_constructible():
    assert Yuv2RgbConfig() == Yuv2RgbConfig(
        blur_filter=False,
        blur_threshold=50.0,
        exposure_filter=False,
        exposure_threshold_low=0.05,
        exposure_threshold_high=0.05,
    )
    assert Depth2LinearConfig() == Depth2LinearConfig(
        clip_near_m=0.1,
        clip_far_m=3.0,
        use_cache=True,
    )


def test_run_yuv_to_rgb_uses_default_config_when_config_is_omitted(tmp_path, monkeypatch):
    captured = {}

    class DummyLayout:
        def __init__(self, *, project_dir):
            captured["project_dir"] = project_dir
            self.image = object()

    class DummyImageDataIO:
        def __init__(self, *, image_path_config):
            captured["image_path_config"] = image_path_config

    def fake_convert_yuv_directory(*, image_io, config):
        captured["image_io"] = image_io
        captured["config"] = config

    monkeypatch.setattr(conversion, "LegacyProjectLayout", DummyLayout)
    monkeypatch.setattr(conversion, "ImageDataIO", DummyImageDataIO)
    monkeypatch.setattr(conversion, "convert_yuv_directory", fake_convert_yuv_directory)

    conversion.run_yuv_to_rgb(tmp_path)

    assert captured["project_dir"] == tmp_path
    assert captured["config"] == Yuv2RgbConfig()


def test_run_yuv_to_rgb_accepts_typed_config(tmp_path, monkeypatch):
    captured = {}

    class DummyLayout:
        def __init__(self, *, project_dir):
            self.image = object()

    class DummyImageDataIO:
        def __init__(self, *, image_path_config):
            pass

    def fake_convert_yuv_directory(*, image_io, config):
        captured["config"] = config

    monkeypatch.setattr(conversion, "LegacyProjectLayout", DummyLayout)
    monkeypatch.setattr(conversion, "ImageDataIO", DummyImageDataIO)
    monkeypatch.setattr(conversion, "convert_yuv_directory", fake_convert_yuv_directory)

    config = Yuv2RgbConfig(blur_filter=True, blur_threshold=75.0)
    conversion.run_yuv_to_rgb(tmp_path, config=config)

    assert captured["config"] is config


def test_run_yuv_to_rgb_rejects_ambiguous_config_sources(tmp_path):
    with pytest.raises(ValueError, match="Pass either config or config_yml_path"):
        conversion.run_yuv_to_rgb(tmp_path, Path("config.yml"), config=Yuv2RgbConfig())


def test_run_depth_to_linear_uses_default_config_when_config_is_omitted(tmp_path, monkeypatch):
    captured = {}

    class DummyLayout:
        def __init__(self, *, project_dir):
            captured["project_dir"] = project_dir
            self.depth = object()

    class DummyDepthDataIO:
        def __init__(self, *, depth_path_config):
            captured["depth_path_config"] = depth_path_config

    def fake_convert_depth_directory(*, depth_data_io, depth_to_linear_config):
        captured["depth_data_io"] = depth_data_io
        captured["config"] = depth_to_linear_config

    monkeypatch.setattr(conversion, "LegacyProjectLayout", DummyLayout)
    monkeypatch.setattr(conversion, "DepthDataIO", DummyDepthDataIO)
    monkeypatch.setattr(conversion, "convert_depth_directory", fake_convert_depth_directory)

    conversion.run_depth_to_linear(tmp_path)

    assert captured["project_dir"] == tmp_path
    assert captured["config"] == Depth2LinearConfig()


def test_pipeline_configs_are_default_constructible():
    from mq3drecon.config import PipelineConfigs, ReconstructionConfig

    configs = PipelineConfigs()

    assert configs.yuv_to_rgb == Yuv2RgbConfig()
    assert configs.depth_to_linear == Depth2LinearConfig()
    assert configs.reconstruction == ReconstructionConfig()


def test_pipeline_processor_uses_default_configs_when_config_path_is_omitted(tmp_path, monkeypatch):
    from mq3drecon.config import PipelineConfigs
    import mq3drecon.pipeline.pipeline_processor as pipeline_processor

    captured = {}

    class DummyDataIO:
        def __init__(self, *, project_dir):
            captured["project_dir"] = project_dir

    monkeypatch.setattr(pipeline_processor, "DataIO", DummyDataIO)

    processor = pipeline_processor.PipelineProcessor(tmp_path)

    assert captured["project_dir"] == tmp_path
    assert processor.pipeline_configs == PipelineConfigs()
