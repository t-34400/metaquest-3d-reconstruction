# Meta Quest 3D Reconstruction

<p align="center">
  <img src="docs/overview.png" alt="QuestRealityCapture" width="480"/>
</p>

**Reconstruct 3D scenes from image and depth data captured using [Quest Reality Capture (QRC)](https://github.com/t-34400/QuestRealityCapture/).**

---

## Overview

This project provides conversion, stereo depth generation, COLMAP export, and TSDF-based 3D reconstruction workflows for Quest capture datasets.

Supported workflows:

- Legacy capture datasets
- MRUK capture datasets
- Quest native depth reconstruction
- FoundationStereo depth reconstruction
- Fast-FoundationStereo depth reconstruction
- COLMAP export workflows

---

## Quick Install

Install the full package from source:

```bash
uv pip install -e ".[full]"
```

For installation requirements, optional dependencies, and development setup, see:

- [Installation Guide](docs/INSTALLATION.md)

---

## Quick Start

Generate stereo depth:

```bash
mq3drecon foundation-stereo-depth \
  --project-dir path/to/project \
  --model-path path/to/model.onnx
```

Run reconstruction:

```bash
mq3drecon reconstruct \
  --project-dir path/to/project
```

For additional command-line examples and command descriptions, see:

- [Command-Line Usage](docs/CLI.md)

---

## Choosing a Workflow

Most users should start by selecting a reconstruction workflow.

| Capture Source | Depth Source | Recommendation |
| --- | --- | --- |
| MRUK | FoundationStereo | ⭐ Recommended |
| MRUK | Fast-FoundationStereo | ⭐ Recommended |
| MRUK | Quest Native Depth | Supported |
| Legacy | Any Depth Source | Compatibility Workflow |

For workflow recommendations, architecture details, and capture compatibility:

- [Pipeline Guide](docs/PIPELINES.md)

---

## Choosing a Stereo Model

Supported stereo models:

- FoundationStereo
- Fast-FoundationStereo

For model selection, ONNX conversion, and runtime requirements:

- [Models Guide](docs/MODELS.md)

---

## Public Python API

The package can also be used directly from Python for custom processing workflows.

For public imports, RGB/depth loading, camera trajectories, conversion helpers, and workflow APIs, see:

- [Public Python API](docs/API.md)

For timestamp conventions, coordinate systems, MRUK frame formats, dataset cache schemas, depth formats, and generated artifact layouts, see:

- [Data Format Reference](docs/DATA_FORMAT.md)

---

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Command-Line Usage](docs/CLI.md)
- [Public Python API](docs/API.md)
- [Data Format Reference](docs/DATA_FORMAT.md)
- [Pipeline Guide](docs/PIPELINES.md)
- [Models Guide](docs/MODELS.md)
- [Legacy Usage Index](docs/USAGE.md)

---

## 🧩 Third-Party Code

This project includes components from [COLMAP](https://github.com/colmap/colmap), licensed under the 3-clause BSD License.

See [`scripts/third_party/colmap/COPYING.txt`](./scripts/third_party/colmap/COPYING.txt) for details.

---

## 📝 License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for full text.
