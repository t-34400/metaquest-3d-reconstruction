import os
import subprocess
import sys

import mq3drecon.cli as cli


def subprocess_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    return env


def test_package_cli_exposes_expected_subcommands_in_help():
    result = subprocess.run(
        [sys.executable, "-m", "mq3drecon.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=subprocess_env(),
    )

    assert result.returncode == 0, result.stderr
    for command in ["yuv-to-rgb", "depth-to-linear", "reconstruct", "export-colmap", "visualize-cameras"]:
        assert command in result.stdout


def test_package_cli_uses_argparse_status_for_invalid_project_dir():
    result = subprocess.run(
        [sys.executable, "-m", "mq3drecon.cli", "reconstruct", "--project-dir", "does-not-exist"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=subprocess_env(),
    )

    assert result.returncode == 2
    assert "Input directory does not exist" in result.stderr


def test_package_cli_converts_expected_workflow_errors_to_status_one(tmp_path, monkeypatch, capsys):
    def fail(*, project_dir, config_yml_path):
        raise ValueError("bad config")

    monkeypatch.setattr(cli, "run_yuv_to_rgb", fail)

    status = cli.main(["yuv-to-rgb", "--project-dir", str(tmp_path), "--config", "missing.yml"])

    captured = capsys.readouterr()
    assert status == 1
    assert "[Error] bad config" in captured.err
