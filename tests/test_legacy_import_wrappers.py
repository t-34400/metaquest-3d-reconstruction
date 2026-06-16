import os
import subprocess
import sys
from pathlib import Path


def test_legacy_dataio_and_models_imports_delegate_to_package_without_open3d():
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

from dataio import DataIO, ReconstructionDataIO
from dataio.data_io import DataIO as DataIOFromModule
from dataio.reconstruction_data_io import ReconstructionDataIO as ReconstructionDataIOFromModule
from models import CameraDataset, DepthDataset, Side
from models.camera_dataset import CameraDataset as CameraDatasetFromModule

assert DataIO is DataIOFromModule
assert ReconstructionDataIO is ReconstructionDataIOFromModule
assert CameraDataset is CameraDatasetFromModule
assert DepthDataset is not None
assert Side is not None
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
