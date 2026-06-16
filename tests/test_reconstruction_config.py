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


def test_reconstruction_config_has_no_open3d_adapter_api():
    import mq3drecon.config.reconstruction_config as reconstruction_config

    assert not hasattr(ReconstructionConfig(), "open3d_device")
    assert not hasattr(ReconstructionConfig().fragment_pose_refinement, "icp_criteria_list")
    assert not hasattr(reconstruction_config, "to_open3d_device")
