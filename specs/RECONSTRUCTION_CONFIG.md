# Reconstruction Configuration Specification

## Purpose

This document defines the structure and dependency boundaries for reconstruction configuration objects.

It owns requirements for:

* reconstruction configuration module ownership
* lightweight import behavior
* Open3D independence for configuration data objects
* compatibility exports during migration

Packaging dependency boundaries are specified in `PACKAGING.md`.
Public import stability is specified in `PUBLIC_API.md`.

---

# Configuration Ownership

Reconstruction configuration must be represented by lightweight Python data objects.

Configuration modules may describe reconstruction options, device specifications, and per-step parameter groups, but they must not construct Open3D runtime objects directly.

Open3D-backed runtime conversion belongs in reconstruction processing adapters, not configuration modules.

---

# Module Structure

Reconstruction configuration should be split by responsibility instead of accumulating unrelated configuration classes in one large module.

The package should provide focused modules for:

* device defaults and device specification aliases
* depth confidence estimation configuration
* fragment generation configuration
* fragment pose refinement configuration
* TSDF/depth integration configuration
* color optimization configuration
* color-aligned depth rendering configuration
* top-level reconstruction configuration parsing and composition

---

# Lightweight Import Requirement

Importing reconstruction configuration modules must not require Open3D.

The following imports must remain usable in the default lightweight installation profile:

```python
from mq3drecon.config import ReconstructionConfig
from mq3drecon.config.reconstruction_config import ReconstructionConfig
```

---

# Compatibility Aggregation

During migration, `mq3drecon.config.reconstruction_config` may remain as an aggregation module that re-exports reconstruction configuration classes from focused implementation modules.

This compatibility module must not become the long-term owner of unrelated configuration responsibilities.

# Reconstruction Depth Source

`ReconstructionConfig` supports selecting the depth input used for TSDF integration.

Supported values are:

| Value | Meaning |
| --- | --- |
| `quest` | Use legacy Quest raw depth descriptors and raw depth maps. This is the default compatibility behavior. |
| `rectified_stereo` | Use saved FoundationStereo-generated rectified stereo RGBD artifacts. This is the preferred stereo-generated reconstruction mode. |
| `color_aligned` | Backward-compatible alias for the stereo-generated reconstruction path. Rectified stereo RGBD is preferred when available; compatibility color-aligned depth is the fallback. |

The `rectified_stereo` source is intended for generated stereo depth maps such as FoundationStereo output. `color_aligned` is retained only for compatibility with existing configuration files and currently selects the same stereo-generated reconstruction path. New configs should prefer `rectified_stereo`. Neither stereo-generated source requires raw Quest depth files.

# Stereo-Generated RGBD Reconstruction

When `depth_source` is `rectified_stereo` or the legacy alias `color_aligned`, reconstruction must prefer saved LEFT rectified stereo RGBD frames when they are available. If rectified stereo RGBD artifacts are absent, it must integrate the LEFT color image and LEFT color-aligned depth map as RGBD frames directly. This path
must not require RIGHT color images, raw Quest depth files, Quest depth pose
optimization, Quest depth confidence estimation, color map optimization, or
color-aligned depth rendering.

The stereo-generated RGBD path must treat saved rectified stereo depth maps, or saved compatibility color-aligned depth maps when rectified stereo depth is unavailable, as the selected depth source and must not render over them as an intermediate output.


# Example Pipeline Configuration Files

Example YAML files should be organized around the user's selected depth source.
The Quest raw-depth example pipeline may include raw-depth conversion, confidence
estimation, fragment generation, depth-pose refinement, color optimization, and
color-aligned depth rendering settings.

The stereo example pipeline should contain the FoundationStereo generation section
and a reconstruction section with `depth_source: rectified_stereo`. It must not
carry Quest raw-depth-only conversion or optimization sections just to satisfy old
unified-pipeline structure. Reconstruction subconfigs omitted from the stereo
example are supplied by `ReconstructionConfig` defaults and are ignored when their
parent stereo-incompatible steps are disabled.

# TSDF Mesh Extraction

Reconstruction paths that extract triangle meshes from Open3D `VoxelBlockGrid`
objects should preserve the configured TSDF integration resolution by default.

When CUDA mesh extraction fails because Open3D cannot allocate the Marching
Cubes assistance mesh structure, reconstruction should retry mesh extraction on
CPU instead of requiring users to reduce reconstruction resolution first. Other
mesh extraction failures must continue to propagate to callers.
