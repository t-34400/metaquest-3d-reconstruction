import os
import subprocess
import sys
import pytest

from mq3drecon import MQ3DReconError, ProcessingError
from mq3drecon.utils.paralell_utils import parallel_map


def test_project_exceptions_are_public_and_catchable():
    assert issubclass(ProcessingError, MQ3DReconError)


def test_parallel_map_logs_failures_without_printing(capsys, caplog):
    def fail(_value):
        raise ValueError("bad value")

    with caplog.at_level("ERROR"):
        result = parallel_map(fail, [1], use_multiprocessing=False, default_on_error="fallback")

    captured = capsys.readouterr()

    assert result == ["fallback"]
    assert captured.out == ""
    assert captured.err == ""
    assert "fail failed" in caplog.text


@pytest.mark.parametrize(
    ("script", "missing_config_message"),
    [
        ("scripts/convert_yuv_to_rgb.py", "Missing or invalid 'yuv_to_rgb' section"),
        ("scripts/convert_depth_to_linear_map.py", "Missing or invalid 'depth_to_linear' section"),
    ],
)
def test_conversion_legacy_scripts_convert_expected_failures_to_exit_status_one(tmp_path, script, missing_config_message):
    config = tmp_path / "empty.yml"
    config.write_text("{}\n")

    env = os.environ.copy()
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")

    result = subprocess.run(
        [sys.executable, script, "--project_dir", str(tmp_path), "--config", str(config)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

    assert result.returncode == 1
    assert missing_config_message in result.stderr
    assert "Traceback" not in result.stderr
