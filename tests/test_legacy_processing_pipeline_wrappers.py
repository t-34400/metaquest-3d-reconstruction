import os
import subprocess
import sys
from pathlib import Path


def test_legacy_processing_and_pipeline_wrappers_delegate_without_open3d():
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

from pipeline import PipelineProcessor
from pipeline.pipeline_processor import PipelineProcessor as PipelineProcessorFromModule
from processing.depth_conversion import convert_depth_directory
from processing.depth_conversion.convert_depth_to_linear import convert_depth_directory as ConvertDepthFromModule
from processing.yuv_conversion import convert_yuv_directory
from processing.yuv_conversion.convert_yuv_dir import convert_yuv_directory as ConvertYuvFromModule

assert PipelineProcessor is PipelineProcessorFromModule
assert convert_depth_directory is ConvertDepthFromModule
assert convert_yuv_directory is ConvertYuvFromModule
assert 'open3d' not in sys.modules
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(repo_root / "scripts"), str(repo_root / "src")])
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
