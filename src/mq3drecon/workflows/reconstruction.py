"""Package-backed reconstruction workflow APIs."""

from pathlib import Path


def run_reconstruct_scene(project_dir: Path, config_yml_path: Path) -> None:
    from mq3drecon.pipeline import PipelineProcessor

    processor = PipelineProcessor(project_dir=project_dir, config_yml_path=config_yml_path)
    processor.reconstruct_scene()
