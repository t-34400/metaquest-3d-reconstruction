import sys

from mq3drecon.config import PipelineConfigs, ReconstructionConfig


def test_reconstruction_config_import_and_default_do_not_require_open3d():
    sys.modules.pop("open3d", None)

    config = ReconstructionConfig()

    assert config.device == "CPU:0"
    assert config.fragment_generation.device == "CPU:0"
    assert "open3d" not in sys.modules


def test_reconstruction_config_parse_keeps_explicit_device_spec_without_open3d():
    sys.modules.pop("open3d", None)

    config = ReconstructionConfig.parse({"device": "CUDA:0", "use_dataset_cache": "true"})

    assert config.device == "CUDA:0"
    assert config.fragment_generation.device == "CUDA:0"
    assert config.depth_integration.device == "CUDA:0"
    assert "open3d" not in sys.modules


def test_pipeline_config_import_does_not_require_open3d():
    sys.modules.pop("open3d", None)

    assert PipelineConfigs is not None
    assert "open3d" not in sys.modules
