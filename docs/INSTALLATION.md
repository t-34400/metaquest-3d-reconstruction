# Installation

This document describes how to install MQ3DRecon for package use, local development, and optional runtime features.

## Requirements

MQ3DRecon requires Python 3.10 or newer.

The default package profile is lightweight. It supports configuration, project layout helpers, domain models, data I/O APIs, conversion workflows, and COLMAP export module imports without requiring Open3D.

## Install from PyPI

Install the lightweight package:

```bash
pip install mq3drecon
```

Install the full toolkit when you need reconstruction, stereo depth generation, and visualization-related optional dependencies:

```bash
pip install "mq3drecon[full]"
```

Use the stereo extra when you only need ONNX-backed FoundationStereo depth generation in addition to the lightweight package:

```bash
pip install "mq3drecon[stereo]"
```

Use the reconstruction extra when you need Open3D-backed reconstruction:

```bash
pip install "mq3drecon[reconstruction]"
```

## Local development install

For development from a cloned repository, create an environment and install the package in editable mode:

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install -e .
```

Install all optional runtime dependencies for local end-to-end testing:

```bash
uv pip install -e ".[full]"
```

When validating changes from a local checkout, prefer editable install over reinstalling a wheel so source edits are reflected immediately.

## Optional dependency profiles

MQ3DRecon defines feature-specific optional extras:

| Extra | Use when you need |
| --- | --- |
| `io` | A stable explicit target for public data I/O APIs. |
| `convert` | A stable explicit target for color and depth conversion workflows. |
| `reconstruction` | Open3D-backed reconstruction workflows and reconstruction data operations. |
| `stereo` | ONNX Runtime-backed FoundationStereo depth generation. |
| `full` | The complete toolkit, including reconstruction and stereo dependencies. |

The default install intentionally does not require Open3D. This keeps lightweight public imports usable in environments that do not have visualization or reconstruction dependencies installed.

## CUDA, Open3D, and ONNX Runtime notes

Open3D is only required for reconstruction workflows. Install `mq3drecon[reconstruction]` or `mq3drecon[full]` before running Open3D-backed reconstruction commands.

ONNX Runtime is only required for FoundationStereo ONNX inference. Install `mq3drecon[stereo]` or `mq3drecon[full]` before running stereo depth generation.

The `stereo` extra installs `onnxruntime`. For GPU execution, install an ONNX Runtime package that matches your CUDA environment, such as `onnxruntime-gpu`, following the ONNX Runtime compatibility requirements for your system.

CUDA itself is not configured by MQ3DRecon. GPU availability depends on the installed ONNX Runtime build, NVIDIA driver, CUDA runtime compatibility, and the execution providers selected in the FoundationStereo configuration.

## Model directory layout

MQ3DRecon does not download stereo models automatically. Keep FoundationStereo or Fast-FoundationStereo ONNX files in a local model directory, for example:

```text
.local/models/
└── foundationstereo.onnx
```

Pass the model path explicitly from the CLI or Python API, or set it in a pipeline configuration file.

CLI example:

```bash
mq3drecon foundation-stereo-depth \
  --project-dir data/project \
  --model-path .local/models/foundationstereo.onnx
```

Python example:

```python
from pathlib import Path

from mq3drecon.workflows import run_foundation_stereo_depth

run_foundation_stereo_depth(
    Path("data/project"),
    model_path=Path(".local/models/foundationstereo.onnx"),
)
```

See [MODELS.md](MODELS.md) for stereo model selection, checkpoint, and ONNX notes.

## Verify the installation

Check that the CLI is available:

```bash
mq3drecon --help
```

Check lightweight package imports:

```bash
python - <<'PY'
import mq3drecon
from mq3drecon.config import PipelineConfigs

print(mq3drecon.__name__)
print(PipelineConfigs())
PY
```

For CLI and API examples, see [USAGE.md](USAGE.md).
