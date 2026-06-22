from pathlib import Path

import yaml

from mq3drecon.config.foundation_stereo_config import FoundationStereoConfig
from mq3drecon.config.reconstruction_config import ReconstructionConfig


CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


def _load_config(name: str) -> dict:
    with (CONFIG_DIR / name).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_stereo_pipeline_config_contains_only_stereo_sections():
    config = _load_config("pipeline_config_stereo.yml")

    assert set(config) == {"foundation_stereo", "reconstruction"}
    assert "yuv_to_rgb" not in config
    assert "depth_to_linear" not in config


def test_stereo_pipeline_config_parses_stereo_sections():
    config = _load_config("pipeline_config_stereo.yml")

    foundation_stereo = FoundationStereoConfig.parse(config["foundation_stereo"])
    reconstruction = ReconstructionConfig.parse(config["reconstruction"])

    assert foundation_stereo.save_color_aligned_depth is False
    assert reconstruction.depth_source == "rectified_stereo"
    assert reconstruction.estimate_depth_confidences is False
    assert reconstruction.optimize_depth_pose is False
    assert reconstruction.render_color_aligned_depth is False
    assert reconstruction.depth_integration.use_confidence_filtered_depth is False
    assert reconstruction.depth_integration.depth_max == 10.0


def test_quest_pipeline_config_remains_quest_pipeline():
    config = _load_config("pipeline_config.yml")
    reconstruction = ReconstructionConfig.parse(config["reconstruction"])

    assert {"yuv_to_rgb", "depth_to_linear", "reconstruction"}.issubset(config)
    assert reconstruction.depth_source == "quest"
