from types import SimpleNamespace

import pytest

from mq3drecon.config import ReconstructionConfig
from mq3drecon.workflows import reconstruction as reconstruction_workflow


class DummyDataIO:
    def __init__(self, project_dir):
        self.project_dir = project_dir


def test_run_reconstruct_scene_accepts_direct_config(monkeypatch, tmp_path):
    calls = []

    def fake_reconstruct_scene(data_io, config):
        calls.append((data_io, config))

    monkeypatch.setattr(reconstruction_workflow, "DataIO", DummyDataIO)
    monkeypatch.setitem(
        __import__("sys").modules,
        "mq3drecon.processing.reconstruction.reconstruct_scene",
        SimpleNamespace(reconstruct_scene=fake_reconstruct_scene),
    )

    config = ReconstructionConfig(depth_source="color_aligned")
    reconstruction_workflow.run_reconstruct_scene(tmp_path, config=config)

    assert calls[0][0].project_dir == tmp_path
    assert calls[0][1] is config


def test_run_reconstruct_scene_rejects_direct_config_and_yml(tmp_path):
    config_path = tmp_path / "pipeline.yml"
    config_path.write_text("reconstruction: {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Pass either config or config_yml_path"):
        reconstruction_workflow.run_reconstruct_scene(
            tmp_path,
            config_yml_path=config_path,
            config=ReconstructionConfig(),
        )
