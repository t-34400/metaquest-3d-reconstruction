"""Package-backed reconstruction workflow APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mq3drecon.config import ReconstructionConfig
from mq3drecon.dataio import DataIO


def _load_config_section(config_yml_path: Path, section_name: str) -> dict[str, Any]:
    with open(config_yml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    section = config.get(section_name)
    if not isinstance(section, dict):
        raise ValueError(f"Missing or invalid '{section_name}' section in config: {config_yml_path}")
    return section


def _resolve_reconstruction_config(
    config: ReconstructionConfig | None,
    config_yml_path: Path | None,
) -> ReconstructionConfig:
    if config is not None and config_yml_path is not None:
        raise ValueError("Pass either config or config_yml_path, not both")
    if config is not None:
        return config
    if config_yml_path is not None:
        return ReconstructionConfig.parse(_load_config_section(config_yml_path, "reconstruction"))
    return ReconstructionConfig()


def run_reconstruct_scene(
    project_dir: Path,
    config_yml_path: Path | None = None,
    *,
    config: ReconstructionConfig | None = None,
) -> None:
    """Run scene reconstruction for a project directory."""
    resolved_config = _resolve_reconstruction_config(config=config, config_yml_path=config_yml_path)

    from mq3drecon.processing.reconstruction.reconstruct_scene import reconstruct_scene

    reconstruct_scene(data_io=DataIO(project_dir=Path(project_dir)), config=resolved_config)
