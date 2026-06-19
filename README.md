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
- FoundationStereo / Fast-FoundationStereo depth reconstruction
- COLMAP export workflows

---

## Quick Install

Install the full package:

```bash
uv pip install -e ".[full]"
```

For installation profiles, runtime requirements, and development setup, see:

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

For complete CLI and API examples, see:

- [Usage Guide](docs/USAGE.md)

---

## Pipeline Selection

| Capture Source | Depth Source | Recommendation |
| --- | --- | --- |
| MRUK | FoundationStereo | ⭐ Recommended |
| MRUK | Fast-FoundationStereo | ⭐ Recommended |
| MRUK | Quest Native Depth | Supported |
| Legacy | Any Depth Source | Compatibility Workflow |

For pipeline architecture and workflow details, see:

- [Pipeline Guide](docs/PIPELINES.md)

---

## Stereo Models

Supported stereo models:

- FoundationStereo
- Fast-FoundationStereo

For model setup and ONNX requirements, see:

- [Models Guide](docs/MODELS.md)

---

## Documentation

- [Installation](docs/INSTALLATION.md)
- [Usage](docs/USAGE.md)
- [Pipelines](docs/PIPELINES.md)
- [Models](docs/MODELS.md)

--

## 🧩 Third-Party Code

This project includes components from [COLMAP](https://github.com/colmap/colmap), licensed under the 3-clause BSD License. See [`scripts/third_party/colmap/COPYING.txt`](./scripts/third_party/colmap/COPYING.txt) for details.

---

## 📝 License

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for full text.