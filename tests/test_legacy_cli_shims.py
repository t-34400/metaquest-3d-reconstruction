import subprocess
import sys


def test_conversion_legacy_scripts_expose_help_without_pipeline_imports():
    scripts = [
        "scripts/convert_yuv_to_rgb.py",
        "scripts/convert_depth_to_linear_map.py",
        "scripts/build_colmap_project.py",
        "scripts/reconstruct_scene.py",
        "scripts/visualize_camera_trajectories.py",
    ]

    for script in scripts:
        result = subprocess.run(
            [sys.executable, script, "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "--project_dir" in result.stdout
