import os
import subprocess
import sys
from pathlib import Path


def test_legacy_config_utils_and_third_party_wrappers_delegate_without_open3d():
    repo_root = Path(__file__).resolve().parents[1]
    code = """
import importlib.abc
import sys

class BlockOpen3D(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'open3d' or fullname.startswith('open3d.'):
            raise ImportError('open3d intentionally blocked')
        return None

sys.meta_path.insert(0, BlockOpen3D())

from config import PipelineConfigs, ReconstructionConfig
from config.reconstruction_config import ReconstructionConfig as ReconstructionConfigFromModule
from config.project_path_config import ProjectPathConfig
from utils.depth_utils import compute_ndc_to_linear_depth_params
from third_party.colmap import read_and_write_model

assert ReconstructionConfig is ReconstructionConfigFromModule
assert PipelineConfigs is not None
assert ProjectPathConfig is not None
assert compute_ndc_to_linear_depth_params(1.0, 3.0) == (-3.0, -2.0)
assert read_and_write_model is not None
assert 'open3d' not in sys.modules
"""
    env = os.environ.copy()
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    env["PYTHONPATH"] = os.pathsep.join([str(repo_root / "scripts"), str(repo_root / "src")])
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
