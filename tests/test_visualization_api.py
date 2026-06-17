import ast
from pathlib import Path


def test_visualization_processing_api_imports_without_open3d():
    import mq3drecon.processing.visualization as visualization

    assert "get_camera_visualization_lines" in visualization.__all__
    assert "visualize_camera_trajectories" in visualization.__all__


def test_visualization_workflow_uses_canonical_processing_module():
    source = Path("src/mq3drecon/workflows/visualization.py").read_text(encoding="utf-8")

    assert "processing.visualization.camera_trajectories" in source
    assert "processing.test.visualize_camera_tragectories" not in source


def test_legacy_misspelled_visualization_module_reexports_canonical_api():
    import mq3drecon.processing.test.visualize_camera_tragectories as legacy
    from mq3drecon.processing.visualization.camera_trajectories import (
        get_camera_visualization_lines,
        visualize_camera_trajectories,
    )

    assert legacy.get_camera_visualization_lines is get_camera_visualization_lines
    assert legacy.get_camera_visualization_line is get_camera_visualization_lines
    assert legacy.visualize_camera_trajectories is visualize_camera_trajectories


def test_public_visualization_module_does_not_import_open3d_at_module_load():
    source = Path("src/mq3drecon/processing/visualization/camera_trajectories.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)

    top_level_open3d_imports = [
        node for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        and any(alias.name == "open3d" for alias in getattr(node, "names", []))
    ]
    assert top_level_open3d_imports == []
